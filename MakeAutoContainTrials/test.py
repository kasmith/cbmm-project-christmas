from TopoModels import *
from get_flood_length import Flooder
from trial_generator import get_trial
from physicsTable import *
import pygame as pg
import json


jtr = json.loads(get_trial('sample', 10))
tr = loadJSON(jtr, 'redgreen')

#tr = loadTrialFromJSON('tmp.json')
#tr = loadTrialFromJSON('tmp_tr.json')

topo = TopologyModel(tr, True)
print "ACD:", topo.acd
print "Triangulation:", topo.triangulation

flood = Flooder(tr, False)
print "Flood:", flood.run()

pg.init()
s = pg.display.set_mode((1000, 620))
topo.draw_acd()
topo.draw_triangles()

tr.jsonify('tmp_tr.json', askoverwrite=False)