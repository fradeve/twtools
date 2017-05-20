import arrow
import csv
import glob
import subprocess
import xmltodict

import click

from sqlalchemy import Column, create_engine, Integer, select, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, column_property
from sqlalchemy.pool import NullPool

date_fmt = '%Y-%m-%dT%H:%M:%SZ'


def run_tw_track(start, end, tags, category):
    tw_command = ['timew', 'track', start, '-', end, tags, category]
    try:
        subprocess.check_output(tw_command)
    except (subprocess.CalledProcessError, TypeError) as exc:
        print(tw_command)
        print(exc)


@click.command()
@click.argument(
    'file',
    type=click.Path(exists=True),
)
@click.option(
    '--backend',
    default='hamster',
    type=click.Choice(['hamster', 'timetrap', 'gleeo-csv', 'timesheet']),
    help='The data source.'
)
@click.option(
    '--after',
    type=str,
    help='The start date of the import, everything before this will be skipped.'
)
def run_import(backend, file, after=None):
    engine_definition = 'sqlite:///{file_name}'.format(file_name=file)
    engine = create_engine(engine_definition, poolclass=NullPool)
    Base = declarative_base(engine)

    if backend == 'hamster':

        class Category(Base):
            __tablename__ = 'categories'
            __table_args__ = {'autoload': True, 'extend_existing': True}

        class Tag(Base):
            __tablename__ = 'activities'
            __table_args__ = {'autoload': True, 'extend_existing': True}

            category_id = Column(
                Integer,
                primary_key=True
            )

            category = column_property(
                select(
                    [Category.name]
                ).where(
                    Category.id == category_id
                ).correlate_except(
                    Category
                )
            )

        class SecondaryTag(Base):
            __tablename__ = 'tags'
            __table_args__ = {'autoload': True, 'extend_existing': True}

        class FactsTags(Base):
            __tablename__ = 'fact_tags'
            __table_args__ = {'autoload': True, 'extend_existing': True}

            fact_id = Column(
                Integer,
                primary_key=True
            )

        class Activity(Base):
            __tablename__ = 'facts'
            __table_args__ = {'autoload': True, 'extend_existing': True}

            id = Column(
                Integer,
                primary_key=True
            )

            activity_id = Column(
                Integer,
                primary_key=True
            )

            tag = column_property(
                select(
                    [Tag.name]
                ).where(
                    Tag.id == activity_id
                ).correlate_except(
                    Tag
                )
            )

            secondary_tag = column_property(
                select(
                    [SecondaryTag.name]
                ).where(and_(
                    FactsTags.fact_id == id,
                    FactsTags.tag_id == SecondaryTag.id
                )).correlate_except(
                    Tag
                )
            )

            category = column_property(
                select(
                    [Category.name]
                ).where(and_(
                    Tag.id == activity_id,
                    Category.id == Tag.category_id
                )).correlate_except(
                    Category
                )
            )

            def get_tags(self):
                if self.secondary_tag:
                    return (
                        '{t} {st}'.format(t=self.tag, st=self.secondary_tag),
                        None
                    )
                return self.tag, None

    elif backend == 'timetrap':

        class Activity(Base):
            __tablename__ = 'entries'
            __table_args__ = {'autoload': True, 'extend_existing': True}

            def get_tags(self):
                words = self.note.split(' ')
                if len(words) <= 2:
                    return self.note.replace(' ', ''), None
                elif len(words) > 2:
                    answer = input(
                        '\nFound the following tags:\n{w}\n'
                        '[y] import as they are\n'
                        '[f] use first word as tag\n'
                        '[c] take first to words separated by comma as tag\n'
                        '[_] write them here: '.format(w=words)
                    )
                    if answer == 'y':
                        return ' '.join(words), None
                    elif answer == 'f':
                        tag = words[0]
                        desc = self.note.replace('{w} '.format(w=tag), '', 1)
                        return tag, desc
                    elif answer == 'c':
                        original_tags = words[0]
                        tag = words[0].replace(',', ' ')
                        desc = self.note.replace(
                            '{t} '.format(t=original_tags),
                            ''
                        )
                        return tag, desc
                    else:
                        return answer, None

            @property
            def category(self):
                return self.sheet

            @property
            def start_time(self):
                return self.start

            @property
            def end_time(self):
                return self.end

            @property
            def description(self):
                return None

    elif backend == 'gleeo-csv':

        files = glob.glob('{p}/*.csv'.format(p=file))
        for file_path in files:
            has_content = False
            with open(file_path, 'r') as csv_file:
                reader = csv.reader(csv_file, delimiter=',')
                if sum(1 for _ in reader) > 1:
                    has_content = True
            if has_content:
                with open(file_path, 'r') as csv_file:
                    counter = 0
                    reader = csv.reader(csv_file, delimiter=',')
                    for row in reader:
                        if counter >= 1:
                            prj, task, _, start, end, _, _ = row
                            run_tw_track(
                                arrow.get(start).datetime.strftime(date_fmt),
                                arrow.get(end).datetime.strftime(date_fmt),
                                task,
                                prj
                            )
                        counter += 1
        exit()

    elif backend == 'timesheet':

        with open(file, 'r') as xml_file:
            tree = xmltodict.parse(xml_file.read())
            projects = {
                p.get('projectId'): p for p in
                tree.get('timesheet').get('projects').get('project')
            }
            task_tags = {
                p.get('taskId'): p for p in
                tree.get('timesheet').get('taskTags').get('taskTag')
            }
            tags = {
                p.get('tagId'):
                p for p in tree.get('timesheet').get('tags').get('tag')
            }
            for act in tree.get('timesheet').get('tasks').get('task'):
                tag = None
                task_tag = task_tags.get(act.get('taskId'))
                if task_tag:
                    tag = tags.get(task_tag.get('tagId')).get('name').lower()
                category = projects.get(
                    act.get('projectId')
                ).get('name').lower()
                if len(category.split(' ')) > 1:
                    category = '_'.join(category.split(' '))

                run_tw_track(
                    arrow.get(act.get('startDate')).datetime.strftime(date_fmt),
                    arrow.get(act.get('endDate')).datetime.strftime(date_fmt),
                    tag,
                    category
                )
        exit()

    Session = sessionmaker(bind=engine)
    session = Session()

    rows = []
    after = arrow.get(after).datetime.replace(tzinfo=None) if after else None

    for activity in session.query(Activity):
        start = activity.start_time.strftime(date_fmt)

        if (after and activity.start_time > after) or (not after):

            try:
                end = activity.end_time.strftime(date_fmt)
            except AttributeError:
                continue

            tags, description = activity.get_tags()
            run_tw_track(start, end, tags, activity.category)

            row = [
                backend,
                activity.id,
                start,
                end,
                tags,
                activity.category,
                activity.description or description
            ]
            rows.append(row)
        else:
            'Skipped activity starting at {s}.'.format(s=start)

    with open('imported_activities.csv', 'w') as csv_file:
        csv_writer = csv.writer(
            csv_file,
            delimiter=',',
            quotechar='"',
            lineterminator='|\r\n',
            quoting=csv.QUOTE_ALL
        )
        csv_writer.writerow([
            'source',
            'source_id',
            'start',
            'end',
            'tag',
            'category',
            'description',
        ])
        [csv_writer.writerow(row) for row in rows]

if __name__ == '__main__':
    run_import()
