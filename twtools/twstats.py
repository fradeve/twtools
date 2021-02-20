#!/usr/bin/env python3
#
# Minimalistic plotter for TimeWarrior.
#
# Copyright (C) 2016-2017 Francesco de Virgilio <fradeve@inventati.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with twtools. If not, see <http://www.gnu.org/licenses/>.

import json
import subprocess

import click
import matplotlib
import numpy as np

matplotlib.use('TkAgg')

from matplotlib import pyplot as plt, rc
import pandas as pd
from pandas.io.json import json_normalize

try:
    import seaborn as sns
    sns.set()
except ImportError:
    pass


rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)

period_map = {'day': 'D', 'week': 'W', 'month': 'M', 'year': 'M'}


class Data(object):

    def __init__(self, time_span, step, tag):
        self.time_span = time_span
        self.step = step
        self.tag = tag
        self.tw_intervals = self._generate_intervals()
        self.df = json_normalize(self.tw_intervals)

    def _generate_intervals(self):
        """ Export TimeWarrior data as JSON and calculate bins. """
        assert len(self.time_span.split(' ')) >= 1

        if len(self.time_span.split(' ')) == 1:
            command = [':{d}'.format(d=self.time_span)]
        elif len(self.time_span.split(' ')) > 1:
            command = self.time_span.split(' ')

        process = subprocess.Popen(
            ['timew', 'export'] + command + [self.tag],
            stdout=subprocess.PIPE
        )
        out, err = process.communicate()
        intervals = json.loads(out.decode('utf8').replace('\n', ''))

        if intervals and (not intervals[-1].get('end')):
            del intervals[-1]

        return intervals


@click.command()
@click.argument('tags', nargs=-1)
@click.option(
    '--time_span',
    default='month',
    help="How far in the past the tool should look. "
         "Both TimeWarrior's hints (e.g. `:lastmonth`) and TimeWarrior's "
         "natural language (e.g. `45days ago`) are supported."
)
@click.option(
    '--step',
    default='day',
    type=click.Choice(['day', 'week', 'month', 'year']),
    help='The step of the plot.'
)
def run(tags, time_span, step):
    data_sets = [Data(time_span, step, t) for t in tags]
    data_frames = []

    step_fmt = period_map.get(step)

    for ss in data_sets:
        if not ss.df.empty:
            ss.df['start_time'] = pd.to_datetime(ss.df['start'])
            ss.df['end_time'] = pd.to_datetime(ss.df['end'])

            ss.df.drop('start', axis=1, inplace=True)  # Drop `start` column.
            ss.df.drop('end', axis=1, inplace=True)  # Drop `end` column.
            ss.df.drop('tags', axis=1, inplace=True)  # Drop `tags` column.

            ss.df['duration'] = (ss.df['end_time'] - ss.df['start_time'])
            ss.df['duration'] = (
                (ss.df['duration'] / np.timedelta64(1, 's')) / 60
            )
            ss.df['interval'] = ss.df.end_time.dt.to_period(step_fmt)
            ss.df = ss.df.set_index('interval')  # `interval` column as index.

            ss.df.drop('start_time', axis=1, inplace=True)  # Drop `start_time`.
            ss.df.drop('end_time', axis=1, inplace=True)  # Drop `end_time`.
            ss.df.drop('id', axis=1, inplace=True) # Drop `id`.

            ss.df = ss.df.groupby(
                #pd.TimeGrouper(step_fmt),
                pd.Grouper(freq=step_fmt),
                level=0,
            ).aggregate(
                np.sum
            )
            ss.df.rename(columns={'duration': ss.tag}, inplace=True)

            data_frames.append(ss.df)

    result = pd.concat(data_frames, axis=1)

    if step_fmt == 'D':
        result = result.to_timestamp()  # `PeriodIndex` to `DatetimeIndex`.
        result = result.asfreq('D', fill_value=0)  # Fill missing days.

    plot = result.plot(kind='bar')
    plot.set_title('Minutes spent by {p}'.format(p=step))
    plot.set_xlabel('{p}s'.format(p=step))
    plot.set_ylabel('minutes')

    plt.show()
