from __future__ import division
from physicsTable import *
from physicsTable.models import PointSimulation
from get_flood_length import Flooder
from view_trial_parsing import view_trial_parsing
import glob, os, sys

MAX_WALLS_DEL = 5
MIN_WALLS_DEL = 1

def get_noncontained_walls(tr, enforce_goal_switch=False, 
        min_walls_del=MIN_WALLS_DEL, max_walls_del=MAX_WALLS_DEL):
    orig_goal = get_goal(tr)
    orig_rev_goal = get_goal(tr, reverse_dir=True)
    walls = list(tr.normwalls)
    new_walls = None
    num_walls_del = min_walls_del
    min_flood_dist = 9999999 # big integer
    while new_walls is None and num_walls_del <= min_walls_del:
        for i in range(len(tr.normwalls) - num_walls_del + 1):
            for _ in range(num_walls_del):
                tr.normwalls.remove(tr.normwalls[i])
            fl = Flooder(tr, useBallSize=True)
            fl.run()
            # assumes gsteps is steps to the outside goal
            if fl.gsteps != -1 and fl.gsteps < min_flood_dist:
                new_goal = get_goal(tr)
                new_rev_goal = get_goal(tr, reverse_dir=True)
                if not enforce_goal_switch or (orig_goal != new_goal 
                        and orig_rev_goal != new_rev_goal):
                    min_flood_dist = fl.gsteps
                    new_walls = tr.normwalls
            tr.normwalls = list(walls)
        num_walls_del += 1
    if new_walls is not None:
        print 'Removed ' + str(num_walls_del - 1) + ' walls.'
    return new_walls

def get_noncontained_walls_same_path(tr):
    orig_path = get_path(tr)
    orig_rev_path = get_path(tr, reverse_dir=True)
    walls = list(tr.normwalls)
    new_walls = None
    min_flood_dist = 9999999 # big integer
    for i in range(len(tr.normwalls)):
        tr.normwalls.remove(tr.normwalls[i])
        fl = Flooder(tr, useBallSize=True)
        fl.run()
        # assumes gsteps is steps to the outside goal
        if fl.gsteps != -1 and fl.gsteps < min_flood_dist:
            new_path = get_path(tr)
            new_rev_path = get_path(tr, reverse_dir=True)
            if orig_path == new_path and orig_rev_path == new_rev_path:
                min_flood_dist = fl.gsteps
                new_walls = tr.normwalls
        tr.normwalls = list(walls)
    return new_walls

def get_path(tr, reverse_dir=False):
    tb = tr.makeTable()
    if reverse_dir:
        bvel = tr.ball[1]
        tb.balls.setvel([-bvel[0], -bvel[1]])
    return tb.simulate(return_path=True)[1]

def get_goal(tr, reverse_dir=False):
    tb = tr.makeTable()
    if reverse_dir:
        bvel = tr.ball[1]
        tb.balls.setvel([-bvel[0], -bvel[1]])
    return tb.simulate()
    
if __name__ == '__main__':
    assert len(sys.argv) == 2, "Need trial or directory"

    if sys.argv[1][-4:] == 'json':
        tr = loadTrialFromJSON(sys.argv[1])
        tr.normwalls = get_noncontained_walls(tr)
        if tr.normwalls is None:
            print 'No wall can be removed.'
        else:
            view_trial_parsing(tr, view_parsing=False)
    else:
        print 'Reading trials in directory ' + sys.argv[1]
        for tr_path in glob.iglob(sys.argv[1] + '/*.json'):
            if tr_path[-15:] == 'trial_list.json':
                continue
            print 'Processing ' + tr_path
            tr = loadTrialFromJSON(tr_path)
            tr.normwalls = get_noncontained_walls(tr)
            if tr.normwalls is None:
                print 'No wall can be removed.'
                continue
            tr.jsonify(tr_path[:-5] + '_noncont.json', askoverwrite=False)
