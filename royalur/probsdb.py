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

import struct

from .urcore import TOTAL_POSITIONS, board2Index, index2Board

__all__ = ["PositionsWinProbs"]


class PositionsWinProbs(object):
    """ Win probability for Green (on play) for each ROGOUR position. """

    def __init__(self, filename=None):
        if filename:
            self.load(filename)
        else:
            self.wsize = 4
            self.b = bytearray(b'\xff') * self.wsize * TOTAL_POSITIONS


    def load(self, filename):
        with open(filename, "rb") as f:
            self.b = bytearray(f.read())
        if len(self.b) == 4 * TOTAL_POSITIONS:
            self.wsize = 4
        elif len(self.b) == 2 * TOTAL_POSITIONS:
            self.wsize = 2
        else:
            raise ValueError("corrupt {0}, read only {1}".format(filename, len(self.b)))


    def save(self, filename):
        with open(filename, "wb") as f:
            f.write(self.b)


    def board2key(self, board):
        """Return the db internal 'position'. This happens to be the offset into one humongous
        byte array.
        """
        return self.wsize * board2Index(board)


    def key2board(self, key):
        """ Return the key of the board associated with this position. """
        return index2Board(key//self.wsize)


    def get(self, bpos):
        """ Get the win probability associated with position ``bpos``. """
        if self.wsize == 4:
            v = struct.unpack_from(">l", self.b, bpos)[0]
            return v/(2.0**31) if v != -1 else None
        elif self.wsize == 2:
            v = struct.unpack_from(">H", self.b, bpos)[0]
            return v/(-1 + 2.0**16) if v != 65535 else None


    def set(self, bpos, pr):
        """ Set the win probability associated with position ``bpos`` to ``pr``. """
        if self.wsize == 4:
            struct.pack_into(">l", self.b, bpos, int(pr * 2.0**31))
        elif self.wsize == 2:
            struct.pack_into(">H", self.b, bpos, int(pr * (-1 + 2**16)))


    # convenience

    def aget(self, board):
        """ Get the win probability associated with board."""

        # if gameOver(getBoard(board)):
        #  return 0
        return self.get(self.board2key(board))

    def aset(self, board, pr):
        """ Set the win probability associated with board to ``pr``."""

        self.set(self.board2key(board), pr)
