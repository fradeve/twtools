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

from itertools import chain
import json
import subprocess

import arrow
import click
import matplotlib
import numpy as np

matplotlib.use('TkAgg')

from matplotlib import pyplot as plt, rc

try:
    import seaborn as sns
    sns.set()
except ImportError:
    pass


fmt = 'YYYYMMDDTHHmmss'

rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)


class Data(object):

    def __init__(self, time_span, step, tag):
        self.time_span = time_span
        self.step = step
        self.tag = tag
        self.x_values = []
        self.x_labels = []
        self.y_values = []
        self.bins = []
        self.tw_intervals = self._generate_intervals()
        self.extremes = []

        if self.tw_intervals:
            self.extremes = [
                self.tw_intervals[0].get('start'),
                self.tw_intervals[-1].get('end')
            ]
            self.generate_bins(*self.extremes)

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

    def generate_bins(self, start, end):
        if isinstance(start, str) and isinstance(end, str):
            start, end = arrow.get(start, fmt), arrow.get(end, fmt)

        bins = [r for r in arrow.Arrow.span_range(self.step, start, end)]
        self.extremes = [bins[0][0], bins[-1][1]]
        self.bins = bins

    def calculate_values(self):
        for time_bin in self.bins:
            x, step_label = self._get_x(time_bin[0], self.step)
            step_label_txt = '-{s}'.format(s=step_label) if step_label else None

            self.x_values.append(x)
            self.x_labels.append(
                '{x}{s}'.format(x=x, s=step_label_txt)
                if step_label else
                '{x}'.format(x=x)
            )

            y = self._sum_intervals_in_time_span(time_bin)
            self.y_values.append(y or 0)

    @staticmethod
    def _get_x(time_bin_start, step):
        if step == 'day':
            return time_bin_start.day, time_bin_start.month
        elif step == 'week':
            return time_bin_start.isocalendar()[1], None
        elif step == 'month':
            return time_bin_start.month, time_bin_start.year
        elif step == 'year':
            return time_bin_start.year, None

    def _sum_intervals_in_time_span(self, time_bin):
        result = 0

        for i in self.tw_intervals:
            start = arrow.get(i.get('start'), fmt)
            end = arrow.get(i.get('end'), fmt)

            if all([start >= time_bin[0], end <= time_bin[1]]):
                result += (end - start).total_seconds() / 60

        return result


def auto_label(ax, bar):
    """ Attach a text label above each bar displaying its height. """
    for b in bar:
        if b.get_height() > 0:
            height = b.get_height()
            ax.text(
                b.get_x() + b.get_width() / 2.,
                1.0 * height,
                '%d' % int(height),
                ha='center',
                va='bottom'
            )


def add_to_plot(plot, width, data, many, col_index):

    ind = np.arange(len(data.x_values))  # X locations for the groups.
    column = plot.bar(
        ind + (width * col_index if data.y_values else width),
        data.y_values,
        width,
    )

    index = (ind + width) if many else ind
    plot.set_xticks(index)
    plot.set_xticklabels(data.x_labels)
    auto_label(plot, column)

    return column


@click.command()
@click.argument('tags', nargs=-1)
@click.option(
    '--timespan',
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
def run(tags, timespan, step):
    width = 0.25  # Width of the bars.
    many = len(tags) > 1

    fig, plot = plt.subplots()
    plot.set_title('Minutes spent by {p}'.format(p=step))
    plot.set_xlabel('{p}s'.format(p=step))
    plot.set_ylabel('minutes')

    columns = []
    data_sets = [Data(timespan, step, t) for t in tags]
    data_sets = [d for d in data_sets if d.extremes]

    # Get time extremes across all data sets, regenerate bins based on them.
    extremes = list(chain.from_iterable([d.extremes for d in data_sets]))
    extremes.sort()
    [d.generate_bins(extremes[0], extremes[-1]) for d in data_sets]

    # Calculate x and y values based on the new bins.
    [d.calculate_values() for d in data_sets]

    data_sets = [d for d in data_sets if sum(d.y_values)]

    for i, data in enumerate(data_sets):
        column = add_to_plot(plot, width, data, many, i)
        columns.append(column[0])

    plt.legend(tuple(columns), tags)
    plt.subplots_adjust(left=0, right=1, top=0.9, bottom=0.1)
    plt.show()
