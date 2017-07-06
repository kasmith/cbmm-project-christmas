import pygame as pg
from physicsTable import *
from textParse import *

SCOREWID = 100
BUTTONWID = 200

DISPSIZE = (1024,768)

WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)


def drawTable(table, redOnRight, score, fillButton = True):
    tabledims = table.dim
    midx = int(DISPSIZE[0]/2.)
    assert tabledims[0] < DISPSIZE[0] and tabledims[1] < (DISPSIZE[1] - 100), "Table too big for the screen"
    sc = pg.Surface(DISPSIZE)
    # Find offsets and draw the table
    tboffset = (int((DISPSIZE[0]-tabledims[0])/2.), int((DISPSIZE[1]-tabledims[1]-100)/2.))
    tbdraw = table.draw()
    sc.fill(WHITE)
    pg.draw.rect(sc, BLACK, pg.Rect(tboffset[0]-2,tboffset[0]-2,tabledims[0]+4,tabledims[1]+4))
    print tabledims, tboffset, DISPSIZE
    sc.blit(tbdraw, tboffset)
    # Draw the score
    scoretop = justifyText("Score:", FONT_L, (midx, tabledims[1]+20), CENTER, TOP)
    scorebottom = justifyText(str(score), FONT_L, (midx, tabledims[1] + 60), CENTER, TOP)
    sc.blit(scoretop[0], scoretop[1])
    sc.blit(scorebottom[0], scorebottom[1])
    # Draw the buttons
    if redOnRight:
        rcol = RED
        lcol = GREEN
    else:
        rcol = GREEN
        lcol = RED
    lbrect = pg.Rect(int(midx - SCOREWID/2. - BUTTONWID), tabledims[1], BUTTONWID, 60)
    rbrect = pg.Rect(int(midx + SCOREWID/2.), tabledims[1], BUTTONWID, 60)
    if fillButton:
        pg.draw.rect(sc,rcol,rbrect)
        pg.draw.rect(sc,lcol,lbrect)
        rto, rtr = justifyText("m", FONT_VL, (int(midx + SCOREWID/2. + BUTTONWID/2.), tabledims[1]+50))
        sc.blit(rto, rtr)
        lto, ltr = justifyText("z", FONT_VL, (int(midx - SCOREWID/2. - BUTTONWID/2.), tabledims[1]+50))
        sc.blit(lto, ltr)
    else:
        pg.draw.rect(sc, rcol, rbrect, 4)
        pg.draw.rect(sc, lcol, lbrect, 4)
    return sc

tr = loadTrialFromJSON('Trials/regular_1.json')
pg.init()
s = pg.display.set_mode(DISPSIZE)
tb = tr.makeTable()
s.blit(drawTable(tb, True, 0), (0,0))
pg.display.flip()
screenPause()