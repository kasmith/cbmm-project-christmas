from physicsTable import *
from physicsTable.constants import REDGOAL, GREENGOAL
import os, glob, json

JSON_TRS = os.path.join('..','psiturk-rg-cont','templates','trials')

SKIPJSON = map(lambda nm: os.path.join(JSON_TRS,nm+'.json'),
               ['ConditionList','InstTr1','InstTr2','InstTr3','InstTr4'])

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

def whichOnLeft(tr):
    if tr.goals[0][2] == REDGOAL:
        rg = tr.goals[0]
        gg = tr.goals[1]
    else:
        rg = tr.goals[1]
        gg = tr.goals[0]

    # Check that red goal is completely to the left of the green goal
    if rg[1][0] < gg[0][0]:
        return 'R'
    elif gg[1][0] < rg[0][0]:
        return 'G'
    else:
        return 'None'

with open('TrialPos.csv','w') as ofl:
    ofl.write('Trial,WhichOnLeft\n')
    for trnm in glob.glob(os.path.join(JSON_TRS,'*.json')):
        print trnm
        if trnm not in SKIPJSON:
            tr = loadFromJSON(trnm)
            ofl.write(tr.name + ',' + whichOnLeft(tr) + '\n')