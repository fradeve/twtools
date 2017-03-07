# Usage example:
# twstats [time hint] [time bin] [tag]
# Example:
# twstats year week activity1
# will show minutes spent on `activity1` in the last year by week

import csv
import json
from string import Template
import subprocess

import arrow
import dateparser

fmt = 'YYYYMMDDTHHmmss'


def generate_time_spans(hint, period):
    if 'last' in hint:
        hint = hint.replace('last', '')

    if len(hint.split(' ')) == 1:
        hint = '1 {h} ago'.format(h=hint)

    start, end = arrow.get(dateparser.parse(hint)), arrow.utcnow()

    return [r for r in arrow.Arrow.span_range(period, start, end)]


def sum_intervals_in_time_span(intervals, time_span):
    result = 0

    for i in intervals:
        interval_start = arrow.get(i.get('start'), fmt)
        interval_end = arrow.get(i.get('end'), fmt)

        if (
             interval_start >= time_span[0] and
             interval_end <= time_span[1]
        ):
            result += (interval_end - interval_start).total_seconds() / 60

    return '{0:.0f}'.format(result)


def get_label(time_span, period):
    if period == 'day':
        return time_span.month
    elif period == 'week':
        return time_span.isocalendar()[1]
    elif period == 'month':
        return time_span.month
    elif period == 'year':
        return time_span.year


def get_data(hint, period, tag):
    """ Export TimeWarrior data as JSON and calculate bins.

    Args:
        hint (str): TimeWarrior time duration hint (e.g. `:month`).
        period (str): Time bin.
        tag (str): TimeWarrior tag to be analyzed.
    """
    process = subprocess.Popen(
        ['timew', 'export', ':{h}'.format(h=hint), tag],
        stdout=subprocess.PIPE
    )
    out, err = process.communicate()
    intervals = json.loads(out.decode('utf8').replace('\n', ''))

    time_spans = generate_time_spans(hint, period)

    maximum = 0
    rows = []
    for time_span in time_spans:
        result = sum_intervals_in_time_span(intervals, time_span)
        rows.append([get_label(time_span[0], period), result])
        maximum = float(result) if float(result) > maximum else maximum

    rows.sort(key=lambda x: x[0])

    with open('/tmp/twtools_timing', 'w', newline='') as csv_file:
        csv_writer = csv.writer(
            csv_file,
            delimiter=' ',
            lineterminator='\n',
        )
        [csv_writer.writerow(r) for r in rows]

    with open('plot_settings_template') as template_source:
        template = Template(template_source.read())

    template_variables = {
        'activity': tag,
        'period': period,
        'max': maximum + (maximum/5)
    }

    with open('/tmp/twtools_template', 'w') as template_file:
        template_file.write(template.substitute(template_variables))

    print(rows)
