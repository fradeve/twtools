#!/usr/bin/env python3
#
# Minimalistic wrapper for TimeWarrior, with Pomodoro technique integration.
#
# Written by Chriscz, originally here:
# https://gist.github.com/chriscz/55ca9bf3aef18c5bc1ab3d54e0923607
# refactored for Python3 compatibility.
#
# Copyright (C) 2015-2016 Francesco de Virgilio <fradeve@inventati.org>
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

from subprocess import check_output, CalledProcessError, call
import os
import sys

import click


def get_current_task():
    """ Get current TW task, with name and duration.
    """
    try:
        lines = check_output(["timew"]).decode('utf-8').split('\n')
    except CalledProcessError:
        return None

    lines = [_.strip() for _ in lines]
    name = lines[0][len('Tracking'):].strip()
    time = lines[3].split()[1]

    return name, time


@click.command()
@click.argument('command')
def start_task(command):
    """ Start task coming from commandline, start pomodoro timer.
    """
    os.system('timew start {c}'.format(c=command))


@click.command()
def stop_task():
    """ Stop current TW task, send desktop notification.
    """
    name, time = get_current_task() if get_current_task() else (None, None)
    if name and time:
        call(['timew', 'stop'])
        call(['notify-send', 'TW: stopped {n}'.format(n=name)])


@click.command()
def print_current_task():
    """ Print current task to stdout, with name and duration.
    """
    name, time = get_current_task() if get_current_task() else (None, None)
    if name and time:
        sys.stdout.write(' {n} {t}'.format(n=name, t=time) + '\n')
