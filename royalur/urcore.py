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
=======================================
Core functionality for classical ROGOUR
=======================================

The player are named Green (to move) and Red. Each board square is assigned a character.

::

  D C B A     Z Y
  1 2 3 4 5 6 7 8
  d c b a     z y

Green pieces move through abcd12345678yz, while Red pieces move ABCD12345678YZ. Internally the
board is represented as an array of length 22, indexed thus,

::

  18 17 16 15   [21] 20 19
   4  5  6  7  8  9  10 11
   3  2  1  0   [14] 13 12

Positions 14 and 21 respectively store the number of Green/Red pieces out of play (born-off). The
number of pieces at home is implicit (total must sum to 7). You may find it easier to picture the
game and internal representation like that:

::

 Red   15 16 17 18+                    19 20+ 21
                    4 5 6 7& 8 9 10 11
 Green  0  1  2  3+                    12 13+ 14

The plus sign indicates the square bestows an extra roll. The ampersand provide protection from hits
as well.

The board can be encoded as either a *code* or an *index*. Codes are printable strings (of length 5)
intended for "human interaction" and light usage, i.e. copy/paste for sharing or when the number of
boards is relativly small. The index is tighter representation mapping the board to an unique
integer in the range [0,137913936), the total number of Ur positions. Indices are computationally
slower than codes, but enable storing per-board values in one contiguous memory block, indexed by
the board index, for the full game space. Given the ridiculous overhead of Python lists, and even
the supposedly efficient arrays, the only viable option is to work with low-level bytearrays indexed
by the board index.

"""
from __future__ import absolute_import


import bisect
import struct

from .binomhack import bmap
from .z85 import encode, decode
try:
    import royalur.irogaur as irogaur
except ImportError:
    import irogaur

__all__ = [
    "startPosition",
    "allActualMoves", "allMoves",
    "reverseBoard", "homes", "gameOver", "typeBearOff", "totalPositions",
    "boardAsString", "board2Code", "code2Board", "board2Index", "index2Board",
    "positionsIterator",
    "boardCHmap", "reverseBoardIndex", "boardPos2CH",
    "validBoard"
]

GR_OFF = 14
RD_OFF = 21


def reverseBoard(board):
    """ Reverse roles of Red and Green. """

    r = [0]*22
    for i in range(4):
        opp = 15+i
        r[i] = -board[opp]
        r[opp] = -board[i]
    for i in range(4, 12):
        r[i] = -board[i]
    for i in range(12, 14):
        opp = 7+i
        r[i] = -board[opp]
        r[opp] = -board[i]
    r[14] = board[21]
    r[21] = board[14]
    return r


def validBoard(b):
    """ A valid ROGOUR board (debug) """
    ok1 = all([b[i] in (0, 1) for i in (0, 1, 2, 3, 12, 13)])
    ok2 = all([b[i] in (-1, 0, 1) for i in range(4, 12)])
    ok3 = sum([b[i] == 1 for i in range(14)]) + b[14] <= 7
    ok4 = all([b[i] in (0, -1) for i in (15, 16, 17, 18, 19, 20)])
    ok5 = sum([b[i] == -1 for i in tuple(range(4, 12)) +
               (15, 16, 17, 18, 19, 20)]) + b[21] <= 7
    return len(b) == 22 and ok1 and ok2 and ok3 and ok4 and ok5


# Squares bestowing an extra roll.
extraTurn = [3, 7, 13, 18, 20]
# In indexed array form, for speed
extraTurnA = [False]*22
for i in extraTurn:
    extraTurnA[i] = True

boardCHmap = {"a":  0, "b": 1, "c": 2, "d": 3, "y": 12, "z": 13,
              "A":  15, "B": 16, "C": 17, "D": 18, "Y": 19, "Z": 20,
              "1": 4, "2":  5, "3": 6, "4": 7, "5": 8, "6": 9, "7": 10, "8": 11,
              "e": -1, "E": -1}
boardPos2CH = "abcd12345678yz ABCDYZ e"


def reverseBoardIndex(i):
    if 0 <= i <= 3:
        return 15 + i
    if 15 <= i <= 18:
        return i - 15
    if 12 <= i <= 14:
        return i + 7
    if 19 <= i <= 21:
        return i - 7
    if 4 <= i < 4 + 8:
        return i
    assert False


def allActualMoves(board, pips, froms=None):
    """Return a list of all **actual** moves by Green given the dice.

    *actual* here means an empty list is returned when Green can't move. Each returned move is a ``(b,e)`` pair,
    where ``e`` is True when Green has an extra turn (and thus the board has not been flipped), or False and
    thus this is Red turn and the board is flipped.
    """

    assert not gameOver(board)
    if pips == 0:
        return []

    gOnBoard = sum([i == 1 for i in board[0:14]])
    totPiecesMe = 7 - board[GR_OFF]
    assert totPiecesMe != 0
    atHome = totPiecesMe - gOnBoard

    moves = []
    if atHome:
        to = pips-1
        if board[to] == 0:
            b = list(board)
            b[to] = 1
            moves.append((b, extraTurnA[to]))
            if froms is not None:
                froms.append(-1)
    for i in range(14):
        if board[i] == 1:
            to = i + pips
            if to < 14 and board[to] != 1:
                if board[to] == 0 or to != 7:
                    b = list(board)
                    b[i] = 0
                    b[to] = 1
                    moves.append((b, extraTurnA[to]))
                    if froms is not None:
                        froms.append(i)
            elif to == 14:
                b = list(board)
                b[i] = 0
                b[14] += 1
                moves.append((b, False))
                if froms is not None:
                    froms.append(i)

    for k, (b, e) in enumerate(moves):
        if not e:
            moves[k] = (reverseBoard(b), e)
    return moves


def allMoves(board, pips, froms=None):
    """ Return a list of all moves by Green given the dice.

    Same format as :py:func:`allActualMoves`, but including the "no-move" board from 0 pips.
    """

    aam = allActualMoves(board, pips, froms)
    if aam:
        return aam

    if froms is not None:
        froms.append(None)
    return [(reverseBoard(board), False)]


def startPosition():
    """ Staring position. """

    return [0]*22


def homes(board):
    """ Helper returning a (numberOfGreenMenAtHome, numberOfRedMenAtHome) pair. """

    gOnBoard = sum([i == 1 for i in board[0:14]])
    gTotInPlay = 7 - board[GR_OFF]
    gHome = gTotInPlay - gOnBoard

    rOnBoard = sum([i == -1 for i in board[15:19] +
                    board[4:12] + board[19:21]])
    rTotInPlay = 7 - board[RD_OFF]
    rHome = rTotInPlay - rOnBoard
    return gHome, rHome


def boardAsString(board):
    """ Board as a printable string (debug). """

    o = sum([i == 1 for i in board[0:14]])
    totPiecesMe = 7 - board[GR_OFF]
    atHome = totPiecesMe - o

    oo = sum([i == -1 for i in board[15:19] + board[4:12] + board[19:21]])
    ototPiecesOff = 7 - board[RD_OFF]
    oatHome = ototPiecesOff - oo

    top = "".join(["O" if board[i] == -1 else "." for i in range(18, 14, -1)]) + \
          "  " + "".join(["O" if board[i] == -1 else "." for i in (20, 19)]) + \
          (" (%1d)" % (board[RD_OFF]))
    mid = "".join(["O.X"[board[i]+1] for i in range(4, 12)])
    bot = "".join(["X" if board[i] == 1 else "." for i in range(3, -1, -1)]) + \
          "  " + "".join(["X" if board[i] == 1 else "." for i in (13, 12)]) + \
          (" (%1d)" % (board[GR_OFF]))
    s = "[%1d] " % oatHome + top + "\n" + " " * \
        4 + mid + "\n" + "[%1d] " % atHome + bot
    return s


def board2Code(board):
    """Encode board as a string.

    First the board is encoded as 31 bits: 2x3 bits for number of pieces at home, 2x6 bits pieces on
    abcdyz/ABCDYZ, and 13 bits for squares 1-8. The middle strip squares are taken as representing an
    8 digit base-3 number, which is converted to an integer in the range [0 - 3**8-1], which in turn
    is encoded as 13 bits (6+12+13 = 31). The 31 bits are encodes as string of 5 printable characters
    (2**31 < 85**5).
    """

    sparse_index = 0
    o = sum([i == 1 for i in board[0:14]])
    atHome = 7 - board[GR_OFF] - o
    sparse_index += atHome << 28
    sparse_index += int(
        "".join(["1" if i else "0" for i in board[:4] + board[12:14]]), 2) << 22

    oo = sum([i == -1 for i in board[15:19] + board[4:12] + board[19:21]])
    oatHome = 7 - board[RD_OFF] - oo

    sparse_index += oatHome << 19
    sparse_index += int(
        "".join(["1" if i else "0" for i in board[15:19] + board[19:21]]), 2) << 13
    x = board[4] + 1
    for i in board[5:12]:
        x = 3 * x + i + 1
    sparse_index += x
    s = "".join(
        reversed(encode(struct.pack(">L", sparse_index)).decode("utf-8")))
    return s


def code2Board(e):
    """Decode board code back to internal representation."""
    s = format(struct.unpack(">L", decode("".join(reversed(e))))[0], "031b")
    atHome = int(s[:3], 2)
    oAtHome = int(s[9:12], 2)
    assert 0 <= atHome <= 7 and 0 <= oAtHome <= 7

    board = [0]*22
    for b, k in ((3, 0), (4, 1), (5, 2), (6, 3), (7, 12), (8, 13)):
        if s[b] == "1":
            board[k] = 1
    for b, k in ((12, 15), (13, 16), (14, 17), (15, 18), (16, 19), (17, 20)):
        if s[b] == "1":
            board[k] = -1
    mid = s[18:]
    assert len(mid) == 13
    mid = int(mid, 2)
    assert 0 <= mid < 3**8
    for i in range(11, 3, -1):
        x = mid % 3
        board[i] = x - 1
        mid = (mid - x) // 3
    board[14] = 7 - (atHome + sum([i == 1 for i in board[0:14]]))
    board[21] = 7 - (oAtHome + sum([i == -
                                    1 for i in board[15:19] + board[4:12] + board[19:21]]))
    return board


def gameOver(board):
    """ True if game on board is over, False otherwise. """

    return board[14] == 7 or board[21] == 7


def typeBearOff(board):
    """ True if board is in *bear-off* mode. (i.e. no more contact possible). """

    return sum(board[12:15]) == 7 or -sum(board[19:21]) + board[21] == 7


# Board iterators


def bitsIterator(k, n):
    """ Iterate over all placements of *k* identical pieces in *n* locations. """

    if k == 0:
        yield (0,)*n
    elif k == n:
        yield (1,)*n
    else:
        for v in bitsIterator(k-1, n-1):
            yield (1,) + v
        for v in bitsIterator(k, n-1):
            yield (0,) + v

# faster, non recursive


def bitsIterator(k, n):
    """ Iterate over all placements of *k* identical pieces in *n* locations. """

    if k == 0:
        yield (0,)*n
    elif k == n:
        yield (1,)*n
    else:
        b = [1]*k + [0]*(n-k)
        yield list(b)

        while True:
            i = 0
            while b[i] == 0:
                i += 1
            j = i + 1
            while j < n and b[j] == 1:
                j += 1
            if j >= n:
                return

            # 0 1 2 ... i ... j .
            # 0 0 0 ... 0 1 1 1 0
            for k in range(j-i-1):
                b[i+k] = 0
                b[k] = 1
            b[j-1] = 0
            b[j] = 1  # assert b == [1]*(j-i-1) + [0]*(i+1) + [1] + b[j+1:]
            yield list(b)


# def gIterator(gOff = 0):
#   """ Iterate over all green pieces positions with *gOff* pieces off board. """

#   gMen = 7-gOff
#   b = [0]*22
#   b[GR_OFF] = gOff
#   for gHome in range(gMen, -1, -1):
#     gOnBoard = gMen - gHome
#     for gOnMine in range(min(6,gOnBoard), -1, -1):
#       for onMine in bitsIterator(gOnMine, 6):
#         b[:4] = onMine[:4]
#         b[12:14] = onMine[4:]
#         for onStrip in bitsIterator(gOnBoard - gOnMine, 8):
#           b[4:12] = onStrip
#           yield list(b)


def gIterator(gOff=0):
    """ Iterate over all green pieces positions with *gOff* pieces off board. """

    gMen = 7-gOff
    b = [0]*22
    b[GR_OFF] = gOff
    for gHome in range(gMen, -1, -1):
        gOnBoard = gMen - gHome
        for gOnMine in range(min(6, gOnBoard), -1, -1):
            for onStrip in bitsIterator(gOnBoard - gOnMine, 8):
                b[4:12] = onStrip
                for onMine in bitsIterator(gOnMine, 6):
                    b[:4] = onMine[:4]
                    b[12], b[13] = onMine[4], onMine[5]
                    yield list(b)


def rIterator(board, rOff=0):
    """ Iterate over all red pieces positions with *rOff* pieces off board, conditional on present
    green pieces as given in *board*. """

    b = list(board)
    b[RD_OFF] = rOff
    rMen = 7-rOff
    bStrip = b[4:12]
    for rHome in range(rMen, -1, -1):
        rOnBoard = rMen - rHome
        for rOnMine in range(min(6, rOnBoard), -1, -1):
            oo = list(bitsIterator(rOnMine, 6))
            for onStrip in bitsIterator(rOnBoard - rOnMine, 8):
                if any([x == 1 and y == 1 for x, y in zip(onStrip, bStrip)]):
                    continue
                b[4:12] = [-1 if x else y for x, y in zip(onStrip, bStrip)]
                for onMine in oo:
                    b[15:19] = [-x for x in onMine[:4]]
                    b[19], b[20] = -onMine[4], -onMine[5]
                    yield list(b)


# def rIterator(board, rOff = 0):
#   """ Iterate over all red pieces positions with *rOff* pieces off board, conditional on present
#   green pieces as given in *board*. """

#   b = list(board)
#   b[RD_OFF] = rOff
#   rMen = 7-rOff
#   bStrip = b[4:12]
#   for rHome in range(rMen, -1, -1):
#      rOnBoard = rMen - rHome
#      for rOnMine in range(min(6,rOnBoard), -1, -1):
#        for onMine in bitsIterator(rOnMine, 6):
#          b[15:19] = [-x for x in onMine[:4]]
#          b[19:21] = [-x for x in onMine[4:]]
#          for onStrip in bitsIterator(rOnBoard - rOnMine, 8):
#            if any([x == 1 and y == 1 for x,y in zip(onStrip, bStrip)]):
#              continue
#            b[4:12] = [-1 if x else y for x,y in zip(onStrip, bStrip)]
#            yield list(b)


def positionsIterator(gOff=0, rOff=0):
    """ Iterate over all positions with *gOff*/*rOff* Green/Red pieces (respectively) off. """

    for b in gIterator(gOff):
        for b1 in rIterator(b, rOff):
            yield list(b1)

# m on one side, n on the other


def countPosOnBoard(m, n):
    assert m >= n
    tot = 0
    for m1 in range(min(m, 6)+1):
        m2 = m - m1
        tot += bmap[6, m1] * bmap[8, m2] * bmap[14-m2, n]
    return tot


nPositionsOnBoard = dict()
for m in range(8):
    for n in range(m+1):
        nPositionsOnBoard[m, n] = countPosOnBoard(m, n)
        if m != n:
            nPositionsOnBoard[n, m] = nPositionsOnBoard[m, n]


def countOff(gOff, yOff):
    tot = 0
    gAvail = 7 - gOff
    for gHome in range(gAvail+1):
        gOnBoard = gAvail - gHome
        yAvail = 7 - yOff
        for yHome in range(yAvail+1):
            yOnBoard = yAvail - yHome
            tot += nPositionsOnBoard[gOnBoard, yOnBoard]
    return tot


nPositionsOff = dict()
for m in range(8):
    for n in range(m+1):
        nPositionsOff[m, n] = countOff(m, n)
        if m != n:
            nPositionsOff[n, m] = nPositionsOff[m, n]

totalPositions = sum(nPositionsOff.values())

# 0 <= Men on board <= 7


def startPoint(gOff, rOff, gHome, rHome):
    n = 0
    for i in range(gOff):
        for j in range(7+1):
            n += nPositionsOff[i, j]
    for j in range(rOff):
        n += nPositionsOff[gOff, j]

    n1 = 0
    for k in range(gHome):
        for l in range((7-rOff) + 1):
            g, r = 7 - (k + gOff), 7 - (l + rOff)
            n1 += nPositionsOnBoard[g, r]

    for l in range(rHome):
        g, r = 7 - (gHome + gOff), 7 - (l + rOff)
        n1 += nPositionsOnBoard[g, r]
    return n + n1


def partialSums(gMen, rMen):
    tot = 0
    ps = [tot]
    for m1 in range(min(gMen, 6)+1):
        m2 = gMen - m1
        tot += bmap[6, m1] * bmap[8, m2] * bmap[14-m2, rMen]
        ps.append(tot)
    return ps


def bitsIndex(bits):
    k = sum(bits)
    N = len(bits)
    i = 0
    for b in bits:
        if b:
            i += bmap[N-1, k]
            k -= 1
        N -= 1
    return i


def i2bits(i, k, N):
    bits = [0]*N
    j = 0
    while N > 0:
        bnk = bmap[N-1, k]
        if i >= bnk:
            bits[j] = 1
            i -= bnk
            k -= 1
        N -= 1
        j += 1
    return bits

# Ur positions are laid in 64 main blocks. the i*8+j block contains all positions with 'i' Green men
# and 'j' Red men (respectively) off the board (i.e. not at home or on the board). (i,j) pairs are
# sorted lexicographicaly. (0,0),(0,1)...,(0,7),(1,0),(1,1)...(7,7)
#
# The (i,j) block is dividied into (7-i)*(7-j) subblocks. the subblock 'k * (7-j) + l' contains all
# positions with k Green men at home and (and i off), and l Green men home (j off). Again (k,l)
# subblocks are sorted lexicographicaly.
#
# The subblock with g (= 7-i-k) Green men and r (= 7-j-l) on board (respectively) has size
#  P_(g,r) = sum m=0..min(6,g) B(6,m) * B(8,g - m) * B(14 - (g-m), r)
#


startings = [(startPoint(gOff, rOff, gHome, rHome), gOff, rOff, gHome, rHome)
             for gOff in range(8) for rOff in range(8)
             for gHome in range(8-gOff) for rHome in range(8-rOff)]
assert len(set([x[0] for x in startings])) == len([x[0] for x in startings])
spoints = [x[0] for x in startings]
spMap = dict([(tuple(x[1:]), x[0]) for x in startings])
pSums = dict([((gMen, rMen), partialSums(gMen, rMen))
              for gMen in range(8) for rMen in range(8)])


def __board2Index(board):
    gOff = board[GR_OFF]
    rOff = board[RD_OFF]

    gSafe = board[:4] + board[12:14]
    m = sum(gSafe)
    partSafeG = bitsIndex(gSafe)
    bits = [x == 1 for x in board[4:12]]
    gStrip = bitsIndex(bits)
    gMen = sum(bits) + m
    bits = [x == -1 for x in (board[15:19] + board[4:12] + board[19:21]) if x != 1]
    partR = bitsIndex(bits)
    rMen = sum(bits)
    gHome, rHome = 7 - (gMen + gOff), 7 - (rMen + rOff)

    i0 = spMap[gOff, rOff, gHome, rHome]

    ps = pSums[gMen, rMen]
    i1 = ps[m]
    i2 = partSafeG * bmap[8, gMen - m] + gStrip
    i3 = i2 * bmap[14 - (gMen-m), rMen] + partR
    assert i3 < ps[m+1] - ps[m]
    return i0 + i1 + i3


def __index2Board(index):
    i = bisect.bisect(spoints, index)
    assert startings[i-1][0] <= index < (startings[i]
                                         [0] if i < len(startings) else totalPositions)

    gOff, rOff, gHome, rHome = startings[i-1][1:]

    index -= startings[i-1][0]
    assert index >= 0

    gMen, rMen = 7 - (gOff + gHome), 7 - (rOff + rHome)
    ps = pSums[gMen, rMen]
    m = 0
    while not (ps[m] <= index < ps[m+1]):
        m += 1
    index -= ps[m]
    u = bmap[14 - (gMen-m), rMen]
    i2 = index // u
    partR = index - i2 * u
    u = bmap[8, gMen - m]
    partSafeG = i2 // u
    gStrip = i2 - u * partSafeG

    gSafe = i2bits(partSafeG, m, 6)
    b4_12 = i2bits(gStrip, gMen - m, 8)
    bOther = i2bits(partR, rMen, 14 - (gMen-m))

    b = [0]*22
    b[14], b[21] = gOff, rOff
    b[:4] = gSafe[:4]
    b[12:14] = gSafe[4:]
    b[4:12] = b4_12
    b[15:19] = [-x for x in bOther[:4]]

    i = 4
    for k in range(4, 12):
        if b[k] == 0:
            if bOther[i]:
                b[k] = -1
            i += 1
    b[19:21] = [-x for x in bOther[i:]]
    return b


def index2Board(index):
    i = bisect.bisect(spoints, index)
    #assert startings[i-1][0] <= index < (startings[i][0] if i < len(startings) else totalPositions)
    st = startings[i-1]
    gOff, rOff, gHome, rHome = st[1:]

    return irogaur.index2Board(index - st[0], gOff, rOff, gHome, rHome, pSums)


def board2Index(board):
    return irogaur.board2Index(board, spMap, pSums)


#  LocalWords:  bytearrays
