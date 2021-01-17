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

from royalur import *
from royalur.humanStrategies import totPips2s


def ply1PartsFullRecpt(board, rboard, db):
    pWinOnMove = 0
    prReverse = 0
    rest = []

    # [pWinOnMove, [ [[gside] [rside]] , [[gside] [rside]] , ...      ], pNoMove]
    #                       1                   2                  4

    for pr, pips in ((1, 0), (4, 1), (6, 2), (4, 3), (1, 4)):
        am = allMoves(board, pips)
        if pips == 0 or (len(am) == 1 and not am[0][1] and am[0][0] == rboard):
            prReverse += pr
            if pips > 0:
                rest.append(None)
            continue

        for b, e in am:
            if gameOver(b):
                assert pWinOnMove == 0
                pWinOnMove = pr
                break
        if pWinOnMove > 0:
            rest.append(None)
            continue

        brds = [[], []]
        for b, e in am:
            brds[0 if e else 1].append(db.board2key(b))
        rest.append(brds)
    return [pWinOnMove, prReverse, rest]


def ply1BothFullRecpt(board, db):
    r = reverseBoard(board)
    A = ply1PartsFullRecpt(board, r, db)
    B = ply1PartsFullRecpt(r, board, db)
    return (A, B)


def ply1fr(recpt, db):
    rest = recpt[2]
    sm = 0
    for cans, p in zip(rest, (4, 6, 4, 1)):
        if cans:
            g, r = cans
            if not g:
                m = max([(1-db.get(k)) for k in r])
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
    A, p1 = ply1fr(gr, db), gr[1]
    B, p2 = ply1fr(rd, db), rd[1]

    X = (16*A + p1 * (16 - B - p2)) / (256. - p1*p2)
    Y = (B + p2 * (1 - X)) / 16.
    if not (0 <= X <= 1 and 0 <= Y <= 1):
        assert False
    return X, Y


def halfList(added, db):
    supdateList = set()
    updateList = []

    for k in reversed(added):
        assert k not in supdateList
        b = db.key2board(k)

        r = db.board2key(reverseBoard(b))
        if r not in supdateList:
            updateList.append((k, r))
            supdateList.add(k)

    return updateList


def main():
    db = PositionsWinProbs()

    filled = 0

    for g in range(7):
        for b in positionsIterator(7, g):
            db.set(db.board2key(b), 1.0)
            db.set(db.board2key(reverseBoard(b)), 0.0)
            filled += 2

    fnbase = "db"

    for gm in range(6, -1, -1):
        for rm in range(gm, -1, -1):
            print(gm, rm)
            added = []
            for b in positionsIterator(gm, rm):
                key = db.board2key(b)
                added.append(key)
                if db.get(key) is None:
                    db.set(key, 0.5)
                    filled += 1

                rk = db.board2key(reverseBoard(b))
                if db.get(rk) is None:
                    db.set(rk, 0.5)
                    filled += 1

            updateList = halfList(added, db)
            del added
            tot = len(updateList)
            print("{0} position pairs.".format(tot))

            # Heuristic: sort positions by total (X+O) pip count. The total pip count is a good
            # indicator on how "deep" the positions are in the game tree. This way positions
            # closer to game end are more likely to update first, speeding up convergence.
            #
            updateList.sort(key=lambda i2: totPips2s(db.key2board(i2[0])))

            frct = []
            k = 0
            for key, rkey in updateList:
                frct.append(ply1BothFullRecpt(db.key2board(key), db))
                k += 1
                if k % (36*1024) == 0:
                    print("%.0f" % (k*100./tot), end=" ")
            print()

            round = 1
            maximum_error = 1
            while maximum_error > 1e-6:
                print("round {0} ({1} {2})".format(round, gm, rm))
                dif = 0.0
                maximum_error = -1
                count = 0
                for key, rkey in updateList:
                    p1, p2 = ply1bfr(frct[count], db)

                    error1 = abs(db.get(key) - p1)
                    error2 = abs(db.get(rkey) - p2)
                    dif += error1 + error2
                    if max(error1, error2) > maximum_error:
                        maximum_error = max(error1, error2)
                    db.set(key,  p1)
                    db.set(rkey, p2)
                    count += 1
                    if count % (36*1024) == 0:
                        print(count, int((100.*count)/tot), "%.3g" % maximum_error, ".")
                round += 1
                print(maximum_error, dif, dif/(2*tot), tot, filled)
            del frct
            del updateList
            db.save("{0}.inpro.bin".format(fnbase))


if __name__ == "__main__":
    main()
