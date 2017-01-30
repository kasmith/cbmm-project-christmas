from __future__ import division
from physicsTable import *
from physicsTable.constants import *
from GetFloodLength import *
from GetRRT import *
import os,sys

trpath = os.path.join('..','ContainmentTrials','exp_trials')
trials = []
for tnm in os.listdir(trpath):
    if tnm[-4:] == '.ptr':
        trials.append(os.path.join(trpath, tnm))

if __name__ == '__main__':

    ofl = open('FloodTest.csv','w')
    ofl.write('Trial,Type,GReach,GLen,RReach,RLen,TotalSteps,IsContained\n')

    for tr in trials:
        t = loadTrial(tr)

        fl = Flooder(t,False)
        flo = fl.run()
        greach = flo[0] != -1
        rreach = flo[1] != -1
        is_contained = (greach and not rreach) or (rreach and not greach)
        ofl.write(t.name + ',Flood,' + str(greach) + ',' + str(flo[0]) + ',' + 
                str(rreach) + ',' + str(flo[1]) + ',' + str(flo[2]) + ',' +
                str(is_contained) + '\n')

        print tr, "done"

    ofl.close()
