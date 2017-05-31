from physicsTable import *
from TopoModels import TopologyModel
import pygame as pg
from pygame.constants import *
import sys

def view_trial_parsing(tr, view_parsing=True):
    if view_parsing:
        topo = TopologyModel(tr, acd_convexity_by_ball_rad=[1,2,4])
    pg.init()
    s = pg.display.set_mode((1000,620))
    tb = tr.makeTable()
    if view_parsing:
        for i in range(3):
            topo.draw_acd(i)
    tb.demonstrate()

if __name__ == '__main__':
    assert len(sys.argv) == 2, "Need trial"
    tr = loadTrialFromJSON(sys.argv[1])
    view_trial_parsing(tr)
