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

"""
======================
Probabilities Database
======================

Per-Position win probabilities for the full game space.
"""
from __future__ import absolute_import

import os
import struct
import array

from .urcore import TOTAL_POSITIONS, board2Index, index2Board

__all__ = ["PositionsWinProbs"]


class PositionsWinProbs(object):
    """ Win probability for Green (on play) for each ROGOUR position. """

    def __init__(self, filename=None):
        self.db = array.array("d")
        if filename:
            self.load(filename)
        else:
            self.formatchar = "d"
            self.db.extend([0.5] * TOTAL_POSITIONS)
            self.db[-1] = float("NaN")


    def load(self, filename):
        size = os.path.getsize(filename)
        if size == 8 * TOTAL_POSITIONS:
            self.formatchar = "d"
            readsize = 8
            fcn = lambda x: x
        elif size == 4 * TOTAL_POSITIONS:
            self.formatchar = "f"
            readsize = 4
            fcn = lambda x: x
        elif size == 2 * TOTAL_POSITIONS:
            self.formatchar = "H"
            readsize = 2
            fcn = lambda x: x/(-1 + 2.0**16) if x != 65535 else float("NaN")
        else:
            raise ValueError("corrupt {0}, read only {1}".format(filename, len(self.b)))
        with open(filename, "rb") as f:
            for _ in range(TOTAL_POSITIONS):
                self.db.append(fcn(struct.unpack(">{0}".format(self.formatchar), f.read(readsize))[0]))


    def save(self, filename):
        fcn = None
        if self.formatchar == "d":
            fcn = lambda x: x
        elif self.formatchar == "f":
            fcn = lambda x: x
        elif self.formatchar == "H":
            fcn = lambda x: int(x*(-1 + 2.0**16)) if x == x else 65535
        with open(filename, "wb") as f:
            for i in range(TOTAL_POSITIONS):
                f.write(struct.pack(">{0}".format(self.formatchar), fcn(self.db[i])))


    def board2key(self, board):
        """Return the db internal 'position'. This happens to be the offset into one humongous
        byte array.
        """
        return board2Index(board)


    def key2board(self, key):
        """ Return the board of the key associated with this position. """
        return index2Board(key)


    def get(self, bpos):
        """ Get the win probability associated with position ``bpos``. """
        return self.db[bpos] if self.db[bpos] == self.db[bpos] else None


    def set(self, bpos, pr):
        """ Set the win probability associated with position ``bpos`` to ``pr``. """
        self.db[bpos] = pr


    # convenience

    def aget(self, board):
        """ Get the win probability associated with board."""

        # if gameOver(getBoard(board)):
        #  return 0
        return self.get(self.board2key(board))

    def aset(self, board, pr):
        """ Set the win probability associated with board to ``pr``."""

        self.set(self.board2key(board), pr)
