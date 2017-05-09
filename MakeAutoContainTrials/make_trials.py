from __future__ import division
from physicsTable import *
from physicsTable.models import PointSimulation
from TopoModels import TopologyModel
from get_flood_length import Flooder
from make_valid_trial import make_valid_trial
import os
import sys
import numpy as np

TRIAL_DIR = "AutoGenTrials"

# Settings for trial validity
RECTRANGE = [5, 15]
MIN_TIME = 2.
MAX_FWD_TIME = 10.
MAX_REV_TIME = 15.
MIN_TIME_DIFF = 5.
MIN_GOAL_DIST = 150

# Settings for physics simulation
KAP_V = 30
KAP_B = 10
KAP_M = 30000
P_ERR = 10
N_SIMS = 100

# Settings for topology
ACD_CONVEX_RAD_TIMES = [1., 2., 4.]

if __name__ == '__main__':
    assert len(sys.argv) == 3, "Need two args: beginning index and number"
    beg_idx = int(sys.argv[1])
    n_trials = int(sys.argv[2])
    assert n_trials > 1, "Need at least one trial"

    sum_fl_nm = "summary_{:04d}.csv".format(beg_idx)
    with open(os.path.join(TRIAL_DIR, sum_fl_nm), 'w') as sum_fl:
        sum_fl.write("Name,NumRects,NumWalls,DistToGoal,FwdTime,RevTime,Sim_FwdTime,Sim_FwdBounce,")
        sum_fl.write("Sim_RevTime,Sim_RevBounce,Flood_Size,Flood_MaxGeodesic,Flood_MinToGoal,")
        for c in ACD_CONVEX_RAD_TIMES:
            hdr = "ACD_"+str(c)+"_"
            sum_fl.write(hdr+"Size,"+hdr+"MaxGeodesic,"+hdr+"MinToGoal,")
        sum_fl.write("Tri_Size,Tri_MaxGeodesic,Tri_MinToGoal\n")

        for i in range(n_trials):
            tidx = i+beg_idx
            tnm = "RandomTrial_{:04d}".format(tidx)
            tr, dat = make_valid_trial(tnm, RECTRANGE, MIN_TIME, MAX_FWD_TIME, MAX_REV_TIME,
                             MIN_TIME_DIFF, MIN_GOAL_DIST)
            sum_fl.write(tnm+','+str(dat['rects'])+','+str(dat['walls'])+','+str(dat['dist_to_goal'])+',')
            sum_fl.write(str(dat['fwd_time'])+','+str(dat['rev_time'])+',')

            # Simulation
            tb_fwd = tr.makeTable()
            ps_fwd = PointSimulation(tb_fwd, KAP_V, KAP_B, KAP_M, P_ERR, nsims=N_SIMS, cpus=1)
            _, _, bounces_fwd, times_fwd = ps_fwd.runSimulation()
            tb_rev = tr.makeTable()
            bvel = tr.ball[1]
            tb_rev.balls.setvel([-bvel[0], -bvel[1]])
            ps_rev = PointSimulation(tb_rev, KAP_V, KAP_B, KAP_M, P_ERR, nsims=N_SIMS, cpus=1)
            _, _, bounces_rev, times_rev = ps_rev.runSimulation()
            sum_fl.write(str(np.mean(times_fwd))+','+str(np.mean(bounces_fwd))+',')
            sum_fl.write(str(np.mean(times_rev))+','+str(np.mean(bounces_rev))+',')

            # Flooding
            fl = Flooder(tr, False)
            dat = fl.run()
            sum_fl.write(str(dat['size'])+','+str(dat['max_geodesic_dist'])+','+str(dat['min_dist_to_goal'])+',')

            # ACD and triangulation
            topo = TopologyModel(tr, acd_convexity_by_ball_rad=ACD_CONVEX_RAD_TIMES)
            topo_acds = topo.acd
            for c in ACD_CONVEX_RAD_TIMES:
                dat = topo_acds[c]
                sum_fl.write(
                    str(dat['size']) + ',' + str(dat['max_geodesic_dist']) + ',' + str(dat['min_dist_to_goal']) + ',')

            dat = topo.triangulation
            sum_fl.write(
                str(dat['size']) + ',' + str(dat['max_geodesic_dist']) + ',' + str(dat['min_dist_to_goal']) + '\n')
            tr.jsonify(os.path.join(TRIAL_DIR, tnm+'.json'),askoverwrite=False)
            print "Done:", tnm


