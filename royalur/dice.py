# Copyright (c) 2019-2021 Matthew Sheby.
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import random


def initialize_rng():
    """Initialize the RNG"""
    return random.seed(None)


def get_pips():
    """Roll the dice (equivalent to 4D2-4)"""
    return tuple([random.randint(0, 1) for _ in range(4)])
