# Copyright (C) 2018 Joseph Heled.
# Copyright (c) 2019-2021 Matthew Sheby.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import absolute_import

import unittest

import random

from royalur.urcore import *
from royalur.binomhack import bmap
from royalur.urcore import nPositionsOff, bitsIterator


class TestCore(unittest.TestCase):
    def test_bititer(self):
        for _ in range(10):
            k = random.randint(1, 10)
            n = random.randint(k, 15)
            iall = set()
            for b in bitsIterator(k, n):
                self.assertEqual(len(b), n)
                self.assertEqual(sum(b), k)
                self.assertTrue(tuple(b) not in iall)
                iall.add(tuple(b))
            self.assertEqual(bmap[n, k], len(iall))


    def test_counts(self):
        # We'll take the larger cases on faith
        for g in range(7, 2, -1):
            for r in range(7, 2, -1):
                n = 0
                allb = set()
                for b in positionsIterator(g, r):
                    n += 1
                    allb.add(board2Code(b))
                self.assertEqual(nPositionsOff[g, r], n, (g, r, n, nPositionsOff[g, r]))
                self.assertEqual(len(allb), n, (g, r, n, len(allb)))


if __name__ == "__main__":
    unittest.main()
