from physicsTable import *
from physicsTable.constants import REDGOAL, GREENGOAL
import os, glob, json

#CONT_TRS = 'exp_trials'
REACH_DIR = 'reach_trials'
EXP_DIR = 'exp_trials'
JSON_REACH_TRS = 'reach_JSON'

TRNAMES_BASIC = ['porous_2_a'] + ['stopper_' + str(n)+ '_a' for n in range(1,7)]
TRNAMES = ['porous_reach_2_a'] + ['stopper_reach_'+str(n)+'_a' for n in range(1,7)]
print TRNAMES

def getLen(tr, reverse = False):
    tab = tr.makeTable()
    if reverse:
        tab.balls.setvel(map(lambda x: -x, tab.balls.getvel()))
    while tab.step(.01) is None:
        pass
    return tab.tm, tab.balls.bounces

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

for tnmr, tnmb in zip(TRNAMES, TRNAMES_BASIC):
    print "Checking", tnmb
    basic_tr = loadTrial(os.path.join(EXP_DIR,tnmb+'.ptr'))
    reach_tr = loadTrial(os.path.join(REACH_DIR,tnmr+'.ptr'))
    print "Basic Fwd:", getLen(basic_tr)
    print "Reach Fwd:", getLen(reach_tr)
    print "Basic Rev:", getLen(basic_tr,True)
    print "Reach Rev:", getLen(reach_tr,True)

'''
with open('TrialLengths.csv','w') as ofl:
    ofl.write('Trial,Type,Direction,Time,Bounces\n')
    for trnm in glob.glob(os.path.join(JSON_TRS,'*.json')):
        print trnm
        if trnm not in SKIPJSON:
            tr = loadFromJSON(trnm)
            tm, bn = getLen(tr)
            if tr.name[:3] == 'reg':
                ofl.write(tr.name + ',Regular,Fwd,' + str(tm) + ',' + str(bn) + '\n')
            else:
                # Check against raw ptr
                sametr = loadTrial(os.path.join(CONT_TRS, tr.name + ".ptr"))
                stm, sbn = getLen(sametr)
                if stm != tm or sbn != bn:
                    print tr.name, 'does not check out:', (tm,bn), (stm,sbn)
                else:
                    print tr.name, 'checks out'
                tmr, bnr = getLen(tr,True)
                ofl.write(tr.name + ',Contain,Fwd,'+str(tm)+','+str(bn)+'\n'+tr.name+',Contain,Rev,'+str(tmr)+','+str(bnr)+'\n')
'''
