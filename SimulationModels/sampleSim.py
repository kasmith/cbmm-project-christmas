from __future__ import division
from physicsTable import *
from physicsTable.constants import *
from physicsTable.models import PointSimulation
import os, json

def loadFromJSON(jsonfl):
    with open(jsonfl,'rU') as jfl:
        j = json.load(jfl)
        tr = RedGreenTrial(j['Name'], j['Dims'], j['ClosedEnds'])
        b = j['Ball']
        tr.addBall(b[0],b[1],b[2],b[3],b[4])
        for w in j['Walls']:
            tr.addWall(w[0],w[1],w[2],w[3])
        for o in j['Occluders']:
            tr.addOcc(o[0],o[1],o[2])
        for g in j['Goals']:
            tr.addGoal(g[0],g[1],g[2],g[3])
    return tr



tr = loadFromJSON(os.path.join('..','psiturk-rg-cont','templates','trials','regular_5.json'))
tab = tr.makeTable()
# I believe the table settings are from the beginning, so if you want an accurate model of what people see in the 'towards'
#  case, you should move the ball forward 500ms
tab.step(.5)

KAP_V = 20
KAP_B = 25
KAP_M = 50000
P_ERR = 25

ps = PointSimulation(tab, KAP_V, KAP_B, KAP_M, P_ERR, nsims = 500, cpus=1)
ps.runSimulation()
outcomes = ps.getOutcomes()
bounces = ps.getBounces()

print "N(Green) =", outcomes[GREENGOAL]
print "N(Red) =", outcomes[REDGOAL]
print "Avg N bounces =", sum(bounces)/len(bounces)