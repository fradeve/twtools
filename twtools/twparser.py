#!/usr/bin/env python3
#
# Get current activity from TimeWarrior
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
# along with twparser. If not, see <http://www.gnu.org/licenses/>.

from subprocess import check_output, CalledProcessError
import sys


def main():
    try:
        lines = check_output(["timew"]).decode('utf-8').split('\n')
    except CalledProcessError:
        return None

    lines = [_.strip() for _ in lines]
    name = lines[0][len('Tracking'):].strip()
    time = lines[2].split()[1]

    sys.stdout.write(' {n} {t}'.format(n=name, t=time) + '\n')
    return name, time


if __name__ == '__main__':
    main()
