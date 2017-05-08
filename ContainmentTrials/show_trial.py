from physicsTable import *
import pygame as pg
from pygame.constants import KEYDOWN
import sys

def wait_4_kp(draw_fn, hz=20):
    clk = pg.time.Clock()
    while True:
        draw_fn()
        pg.display.flip()
        for e in pg.event.get():
            if e.type == KEYDOWN:
                return
        clk.tick(hz)

if __name__ == '__main__':
    tr = loadTrialFromJSON(sys.argv[1])
    pg.init()
    pg.display.set_mode((1000,620))
    tb = tr.makeTable()
    wait_4_kp(lambda: tb.draw())