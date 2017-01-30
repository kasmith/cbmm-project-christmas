from __future__ import division
from physicsTable import *
from physicsTable.constants import *
from SpatialParsing import *
import os,sys

trpath = os.path.join('..','ContainmentTrials','exp_trials')
trials = []
for tnm in os.listdir(trpath):
    if tnm[-4:] == '.ptr':
        trials.append(os.path.join(trpath, tnm))

if __name__ == '__main__':

    f = open('ParsingTest.csv','w')
    f.write('Trial,Type,GReach,GLen,RReach,RLen,TotalSteps,IsContained\n')

    for tr in trials:
        t = loadTrial(tr)

        sp = SpatialParse(t)
        result = sp.run()

        greach = result[0] > 0
        rreach = result[1] > 0
        is_contained = (greach and not rreach) or (rreach and not greach)

        f.write(t.name + ',Parsing,' + str(greach) + ',' + str(result[0]) + ',' + 
                str(rreach) + ',' + str(result[1]) + ',' + str(result[2]) + ',' +
                str(is_contained) + '\n')

        print tr, "done"

    f.close()
