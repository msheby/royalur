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

""" This script creates the winning probabilities database for ROGOUR.
It will take a veeeeerrrry long time and eat your computer memory.
It is here for educational purposes.
"""
from __future__ import print_function
from __future__ import absolute_import

from royalur import allMoves, gameOver, positionsIterator, reverseBoard, PositionsWinProbs
from royalur.humanStrategies import totPips2s


def ply1PartsFullRecpt(board, reversed_board, db):
    pWinOnMove = 0
    prReverse = 0
    rest = []

    # [pWinOnMove, [ [[gside] [rside]] , [[gside] [rside]] , ...      ], pNoMove]
    #                       1                   2                  4

    for pr, pips in ((1, 0), (4, 1), (6, 2), (4, 3), (1, 4)):
        am = allMoves(board, pips)
        if pips == 0 or (len(am) == 1 and not am[0][1] and am[0][0] == reversed_board):
            prReverse += pr
            if pips > 0:
                rest.append(None)
            continue

        for b, _e in am:
            if gameOver(b):
                assert pWinOnMove == 0
                pWinOnMove = pr
                break
        if pWinOnMove:
            rest.append(None)
            continue

        brds = [[], []]
        for b, e in am:
            brds[0 if e else 1].append(db.board2key(b))
        rest.append(brds)
    return (pWinOnMove, prReverse, rest)


def ply1BothFullRecpt(board, reversed_board, db):
    a = ply1PartsFullRecpt(board, reversed_board, db)
    b = ply1PartsFullRecpt(reversed_board, board, db)
    return (a, b)


def ply1fr(recpt, db):
    rest = recpt[2]
    sm = 0
    for cans, p in zip(rest, (4, 6, 4, 1)):
        if cans:
            g, r = cans
            if not g:
                m = max([(1 - db.get(k)) for k in r])
            elif not r:
                m = max([db.get(k) for k in g])
            else:
                mg = max([db.get(k) for k in g])
                mr = max([(1 - db.get(k)) for k in r])
                m = max(mr, mg)
            sm += m * p
    return recpt[0] + sm  # (recpt[0] + sm)/16.


def ply1bfr(recpt, db):
    gr, rd = recpt
    a = ply1fr(gr, db)
    p1 = gr[1]
    b = ply1fr(rd, db)
    p2 = rd[1]

    x = (16 * a + p1 * (16 - b - p2)) / (256.0 - p1 * p2)
    y = (b + p2 * (1 - x)) / 16.0
    return x, y


def halfList(db, gm, rm):
    updateSet = set()
    for board in positionsIterator(gm, rm):
        key = db.board2key(board)
        rboard = reverseBoard(board)
        rkey = db.board2key(rboard)
        if rkey not in updateSet:
            updateSet.add(key)
            yield (totPips2s(board), key, rkey,
                   ply1BothFullRecpt(board, rboard, db))


def main():
    db = PositionsWinProbs()

    for g in range(7):
        for board in positionsIterator(7, g):
            db.set(db.board2key(board), 1)
            db.set(db.board2key(reverseBoard(board)), 0)

    fnbase = "db"

    for gm in range(6, -1, -1):
        for rm in range(gm, -1, -1):
            print(gm, rm)

            # Heuristic: sort positions by total (X+O) pip count. The total pip count is a good
            # indicator on how "deep" the positions are in the game tree. This way positions
            # closer to game end are more likely to update first, speeding up convergence.
            #
            updateList = sorted(halfList(db, gm, rm), key=lambda i2: i2[0])
            total = len(updateList)
            tenth = total // 10
            print("{0} position pairs.".format(total))
            print()

            count = 0
            iteration_round = 1
            maximum_error = 1.0
            while maximum_error > 1.0e-12:
                print("round {0} ({1} {2})".format(iteration_round, gm, rm))
                maximum_error = 0.0
                for _totalPips, key, rkey, data in updateList:
                    p1, p2 = ply1bfr(data, db)
                    possible_maximum_error = max(abs(db.get(key) - p1),
                                                 abs(db.get(rkey) - p2))
                    if possible_maximum_error > maximum_error:
                        maximum_error = possible_maximum_error
                    db.set(key,  p1)
                    db.set(rkey, p2)
                    count += 1
                    if count % tenth == 0:
                        print("{0} {1} {2}".format(count, int(100.0 * count / total), maximum_error))
                count = 0
                iteration_round += 1
                print("{0} {1}".format(maximum_error, total))
            del updateList
    db.save("{0}.inpro.bin".format(fnbase))


if __name__ == "__main__":
    main()
