#! /usr/bin/env python
## This file is part of royalUr.
## Copyright (C) 2018 Joseph Heled.
## Author: Joseph Heled <jheled@gmail.com>
## See the file LICENSE for copying conditions.
#
from __future__ import print_function
from __future__ import absolute_import

import argparse, sys
import curses, random

from royalur import *
from royalur.humanStrategies import getByNicks, bestHumanStrategySoFar

flog = None
options = None
player = None
wCell = 7
hCell = 5

green, red ,yellow, col6 = None, None, None, None

opmap = {'a' :  15, 'b' : 16, 'c' : 17, 'd' : 18, 'y' : 19, 'z' : 20,
         '1' : 4, '2' :  5, '3' : 6, '4' : 7, '5' : 8, '6' : 9, '7' : 10, '8' : 11,
         'e' : 0}

def cell(window, y, x, name) :
  box1 = window.subwin(hCell, wCell, y, x)
  box1.box()
  box1.addch(3, 1, name)
  return box1


def colorsMagic(window) :
  global green, red, yellow, col6
  curses.start_color()
  curses.use_default_colors()
  for i in range(0, curses.COLORS):
    curses.init_pair(i + 1, i, -1)
  green = curses.color_pair(3) | curses.A_STANDOUT
  red = curses.color_pair(2) | curses.A_STANDOUT
  yellow = curses.color_pair(7) | curses.A_STANDOUT
  col6 = curses.color_pair(6) | curses.A_STANDOUT

def drawHome(nHome, what, off, color, window) :
  for i in range(3):
    if nHome == 0:
      what = ' '
    else:
      nHome -= 1
    window.addch(2 + off + 1 + i, 2+wCell*4, what, 0 if what == ' ' else color)
    if nHome == 0:
      what = ' '
    else:
      nHome -= 1
    window.addch(2 + off + 1 + i, 2+wCell*4+1, what, 0 if what == ' ' else color)
  if nHome == 0:
    what = ' '
  else:
    nHome -= 1
  window.addch(2 + off + 2, 2+wCell*4+2, what, 0 if what == ' ' else color)
  window.refresh()

def drawOff(nOff, what, off, color, window) :
  for i in range(3):
    if nOff == 0:
      what = ' '
    else:
      nOff -= 1
    window.addch(2 + off + 1 + i, 2+6*wCell-1, what, 0 if what == ' ' else color)
    if nOff == 0:
      what = ' '
    else:
      nOff -= 1
    window.addch(2 + off + 1 + i, 2+6*wCell-2, what, 0 if what == ' ' else color)
  if nOff == 0:
    what = ' '
  else:
    nOff -= 1
  window.addch(2 + off + 2, 2+6*wCell-3, what, 0 if what == ' ' else color)
  window.refresh()

def initBoard(window) :
  bboard = [None]*22
  bboard[15:19] = [cell(window, 2, 2+wCell*(3-i), chr(ord('A') + i)) for i in range(4)]
  bboard[19:21] = [cell(window, 2, 2+wCell*6 + wCell*(1-i), chr(ord('Y') + i)) for i in range(2)]
  bboard[4:12] = [cell(window, 2 + hCell, 2+wCell*i, chr(ord('1') + i)) for i in range(8)]
  bboard[0:4] = [cell(window, 2 + 2*hCell, 2+wCell*(3-i), chr(ord('a') + i)) for i in range(4)]
  bboard[12:14] = [cell(window, 2 + 2*hCell, 2+wCell*6 + wCell*(1-i), chr(ord('y') + i)) for i in range(2)]

  drawHome(7, 'X', 2*hCell, green, window)
  drawHome(7, 'O', 0, red, window)

  for i in (3,18,13,20) :
    bboard[i].chgat(3, wCell-2, 1, yellow)
    bboard[i].chgat(1, wCell-2, 1, yellow)
    bboard[i].chgat(1, 1, 1, yellow)
    bboard[i].chgat(3, 1, 1, yellow)
    bboard[i].refresh()

  bboard[7].chgat(3, wCell-2, 1, col6)
  bboard[7].chgat(1, wCell-2, 1, col6)
  bboard[7].chgat(1, 1, 1, col6)
  bboard[7].chgat(3, 1, 1, col6)
  bboard[7].refresh()

  return bboard

def showInfo(msg, info) :
  info.clear()
  info.addstr(0,0, msg, curses.color_pair(5))
  info.refresh()

def getDBmove(moves, db) :
  mvs = [(db.aget(b),b,e) for b,e in moves]
  if not all([p is not None for p,b,e in mvs]) :
    return bestHumanStrategySoFar(moves)
  p,b,e = max([(p if e else 1 - p,b,e) for p,b,e in mvs])
  return [(b,e)]

def dbdPlayer(moves, db) :
  mvs = [(int(db.aget(b)*64)/64.,b,e) for b,e in moves]
  ps = [(p if e else 1 - p,b,e) for p,b,e in mvs]
  mp = max(ps)[0]
  return [(b,e) for p,b,e in ps if p == mp]

def opAddPips(i, pips) :
  return reverseBoardIndex(reverseBoardIndex(i) + pips)

def redraw(newBoard, oldBoard, bboard, window) :
  for i in range(21) :
    if i == 14:
      continue
    #import pdb; pdb.set_trace()
    if newBoard[i] != oldBoard[i] :
      if newBoard[i] == 1 :
        bboard[i].addch(2, (wCell-1)/2, 'X', green)
      elif newBoard[i] == -1 :
        bboard[i].addch(2, (wCell-1)/2, 'O', red)
      else:
        bboard[i].addch(2, (wCell-1)/2, ' ')
      bboard[i].refresh()
    hAfter,hBefore = homes(newBoard), homes(oldBoard)
    if hAfter[0] != hBefore[0]:
      drawHome(hAfter[0], 'X', 2*hCell, green, window)
    if hAfter[1] != hBefore[1]:
      drawHome(hAfter[1], 'O', 0, red, window)
    if newBoard[14] != oldBoard[14] :
      drawOff(newBoard[14], 'X', 2*hCell, green, window)
    if newBoard[21] != oldBoard[21] :
      drawOff(newBoard[21], 'O', 0, red, window)

def ut_interface(window):
  curses.curs_set(0)
  colorsMagic(window)
  bboard = initBoard(window)
  info = window.subwin(3, 50, 4 + 3*hCell + 1, 3)
  showInfo("Press space to advance the action. 'q' to exit,\n" +
           "'e' to enter. Landing in a marked cell gives an\n" +
           "extra turn. Cell 4 is protected from hits.", info)

  ch = None
  while ch != ' ':
    ch = window.getkey()

  interaction = window.subwin(1, 100, 2 + 3*hCell + 1, 3)

  debug = window.subwin(1, 120, 8 + 3*hCell + 1, 3)

  # board will be always from human/X/0 side
  board = startPosition()
  opTurn = random.randint(0, 1) == 0

  if flog :
    print('Board: "' + str(board2Code(board)) + '"', file=flog)
    print("X is %s, O is %s" % (options.name, options.player), file=flog)

  while not gameOver(board) :
    #showInfo(repr(board), debug)

    dice = [random.randint(0, 1) for _ in range(4)]
    pips = sum(dice)
    if flog :
      print("#", board2Code(board), file=flog)
      print("OX"[opTurn] + ': ' + str(pips), file=flog)

    sdice = "%d (" % pips + "".join([str(x) for x in dice]) + ")"
    if opTurn:
      if pips == 0 :
        showInfo("Your roll is 0, hit space to continue.", interaction)
        opTurn = not opTurn
        if flog :
          print('', file=flog)
      else :
        am = allMoves(reverseBoard(board), pips)
        if len(am) == 1 and am[0][0] == board :
          showInfo("Your roll: " + sdice + " No legal moves. space to continue.", interaction)
          opTurn = False
          pips = 0
          if flog :
            print('', file=flog)
        else :
          showInfo("Your roll: " + sdice + " Enter move...", interaction)
    else :
      if pips == 0 :
        showInfo("%s rolls 0, hit space to roll." % options.player, interaction)
        opTurn = True
        if flog :
          print('', file=flog)
      else :
        am = allMoves(board, pips)
        if len(am) == 1 and am[0][0] == reverseBoard(board):
          showInfo(options.player + " rolls: " + sdice + ". No legal moves. Space to continue.", interaction)
          opTurn = True
          pips = 0
          if flog :
            print('', file=flog)
        else :
          showInfo(options.player +" rolls: " + sdice, interaction)

    ch = window.getkey()
    if ch == 'q' or ch == 'Q':
      break

    if pips == 0 :
      while ch != ' ':
        ch = window.getkey()
      continue

    if not opTurn :
      while ch != ' ':
        ch = window.getkey()

    if opTurn :
      ok = False
      clearInfo = False
      while not ok:
        if ch.lower() in "abcdyz12345678e ":
          if ch == ' ':
            frms = []
            am = allMoves(reverseBoard(board), pips, frms)
            if len(am) == 1:
              if frms[0] == -1 :
                i = 0
                t = 14 + pips
                ch = 'e'
              else :
                i = reverseBoardIndex(frms[0])
                ch = boardPos2CH[i]
                t = opAddPips(i,pips)
              ok = True
            else :
              showInfo("Multiple moves possible. Please select one.", info)
              clearInfo = True
              ch = window.getkey()
              continue
          else :
            # see if legal
            i = opmap[ch.lower()]
            if i == 0 :
              t = 14 + pips
              ok = homes(board)[1] > 0 and board[t] == 0
            else :
              t = opAddPips(i,pips)
              ok = board[i] == -1 and t <= 21 and (t == 21 or board[t] == 0 or (board[t] == 1 and t != 7))
              #if not ok:
                #showInfo(repr(board) + " %d %d %d" % (i,pips,t), debug)
        if ok:
          if flog :
            print(ch.lower(), file=flog)
          break
        showInfo("Illegal move. Try again.", info)
        clearInfo = True
        ch = window.getkey()
      if clearInfo:
        info.clear()
        info.refresh()

      oldBoard = list(board)
      if i == 0:
        board[t] = -1
      else :
        assert board[i] == -1
        board[i] = 0
        if t == 21:
          board[t] += 1
        else :
          board[t] = -1
      if t ==  18 or t == 7 or t == 20:
        pass
      else :
        opTurn = False
      assert validBoard(board),str(board)

      redraw(reverseBoard(board), reverseBoard(oldBoard), bboard, window)
    else :
      pips = sum(dice)
      am = allMoves(board, pips)
      if len(am) == 1:
        m,e = am[0]
      else :
        am = player(am)
        m,e = random.choice(am)

      if not e:
        bForUpdate = reverseBoard(m)
        opTurn = True
      else :
        bForUpdate = m

      if flog:
        ch = None
        for i in range(14) :
          if board[i] == 1 and bForUpdate[i] == 0:
            ch = "abcd12345678yz"[i]
            break
        if ch is None:
          assert homes(board)[0] - 1 == homes(bForUpdate)[0]
          ch = 'e'
        print(ch.upper(), file=flog)

      redraw(reverseBoard(bForUpdate), reverseBoard(board), bboard, window)
      board = bForUpdate
    if flog:
      flog.flush()

  if flog:
    if gameOver(board) :
      if board[14] == 7 :
        print("O: wins", file=flog)
      else:
        print("X: wins", file=flog)
    flog.close()

  interaction.clear()
  interaction.refresh()

  if gameOver(board) :
    showInfo("Game over.", info)
    ch = window.getkey()

curses.wrapper(ut_interface)

def main():
  global flog, options, player
  parser = argparse.ArgumentParser(description="""Play ROGOUR, Man against the Machine.""")

  parser.add_argument("--record", "-r", metavar="FILE", help = "Record the match in FILE.")

  parser.add_argument("--name", "-n", metavar="STR", default = "Human", help = "Your name.")

  parser.add_argument("--player", "-p", metavar="OPPONENT",
                      choices=["SimpleSam", "Joe", "Santa", "Expert", "Ishtar"], default = "Santa",
                      help = "SimpleSam (1650), Joe (1730), Santa (1820), Expert (1880), Ishtar (2000)")

  options = parser.parse_args()
  try :
    flog = open(options.record, 'a') if options.record else None
  except:
    print("Error opening match log.", file=sys.stderr)
    sys.exit(1)

  if options.player == "SimpleSam" :
    player = getByNicks("hit;Donkey;safe;homestretch;bear")
  elif options.player == "Joe" :
    player = getByNicks('safe;homestretch;hit;Extra;Chuck;Frank;bear;Donkey')
  elif options.player == "Santa" :
    player = bestHumanStrategySoFar
  elif options.player == "Expert" or options.player == "Ishtar":
    print("loading database...,", file=sys.stderr)
    db = PositionsWinProbs(royalURdataDir + "/db16.bin")
    print("done.", file=sys.stderr)
    if options.player == "Expert" :
      player = lambda m : dbdPlayer(m, db)
    else :
      player = lambda m : getDBmove(m, db)
  else :
    assert False


if __name__ == "__main__":
  main()
