__author__ = 'ksmith'
from physicsTable import *
from physicsTable.constants import *
import pygame as pg
import copy

sc = pg.display.set_mode((1000,620))

def checkN(tb,goalret,kapv=20,kapb=15,kapm=50000,perr=25):
    i = 0
    while True:
        i += 1
        ntb = makeNoisy(tb,kapv,kapb,kapm,perr)
        ntb.set_timestep(.05)
        opos = ntb.balls.getpos()
        ovel = ntb.balls.getvel()

        running = True
        while running:
            r = ntb.step(.1)
            if r is not None:
                if r == goalret:
                    print 'Found'
                    np = ntb.balls.getpos()
                    ntb.balls.setpos(opos)
                    ntb.balls.setvel(ovel)
                    ntb.tm = tb.tm
                    return ntb, np
                else:
                    print 'Not right goal;', i
                    running = False
            if ntb.tm > 60: running = False


tr = loadTrial('QTr5.ptr')
tb = tr.makeTable()
for i in range(5): tb.step(.1)
print tb.tm
#tb.balls.setpos([772.5080259377155, 223.9640488649363])
#tb.demonstrate(timesteps=.05)

ntb, bpos = checkN(tb, GREENGOAL)
print bpos
tb.balls.setpos(bpos)
tb.demonstrate()
#ntb = makeNoisy(tb,20,15,50000,25)
#ntb.set_timestep(.05)
#print ntb.balls.getpos()
ntb.demonstrate(timesteps=.05)