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

from royalur.urcore import *


class TestCore(unittest.TestCase):
    def oneBoard(self, b):
        self.assertEqual(code2Board(board2Code(b)), b)
        self.assertEqual(index2Board(board2Index(b)), b)


    def test_basic(self):
        b = startPosition()
        self.oneBoard(b)


    def test_boards(self):
        for i in range(TOTAL_POSITIONS):
            self.oneBoard(index2Board(i))


    def test_all_boards(self):
        for g in range(7):
            for r in range(7):
                for b in positionsIterator(g, r):
                    self.oneBoard(b)


    def test_rev(self):
        for i in range(TOTAL_POSITIONS):
            b = index2Board(i)
            self.assertEqual(reverseBoard(reverseBoard(b)), b)


    def test_cov_bug(self):
        l = bytearray(b"\x00") * TOTAL_POSITIONS
        for r in range(7):
            for b in positionsIterator(7, r):
                i = board2Index(b)
                self.assertEqual(l[i], 0)
                l[i] = 1
        for g in range(7):
            for b in positionsIterator(g, 7):
                i = board2Index(b)
                self.assertEqual(l[i], 0, str(i) + "," + repr(b))
                l[i] = 1


    def test_cov_full(self):
        l = bytearray(b"\x00") * TOTAL_POSITIONS
        for g in range(7):
            for r in range(7):
                for b in positionsIterator(g, r):
                    i = board2Index(b)
                    self.assertEqual(l[i], 0, str(i) + "," + repr(b))
                    l[i] = 1
                    self.assertEqual(index2Board(i), b, str(i) + "," + repr(b))


if __name__ == "__main__":
    unittest.main()
