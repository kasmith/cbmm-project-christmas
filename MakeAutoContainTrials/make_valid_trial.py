from __future__ import division
from physicsTable import *
from physicsTable.constants import *
from trial_generator import get_trial
import numpy as np
import random
import json
import time

def _get_red_goal_mid(trial):
    rgoal = None
    for g in trial.goals:
        if g[2] == REDGOAL:
            rgoal = g[:2]
    goalmid = np.array([(rgoal[0][0] + rgoal[1][0]) / 2., (rgoal[0][1] + rgoal[1][1]) / 2.])
    return goalmid

def _get_goal_heading(bpos, goal_mid):
    diff = goal_mid - bpos
    return np.arctan2(diff[1], diff[0])

def _randomize_heading(orig_head, sigma, bvel = 300.):
    hdiff = np.random.normal(0, sigma, 1)[0]
    dir = (orig_head + hdiff) % (2*np.pi)
    return np.array([bvel*np.cos(dir), bvel*np.sin(dir)])

# Makes a valid trial subject to validity conditions
# Inputs:
#  trname: name of the trial (string)
#  rectrange: two integers determining the bounds of the number of rectangles that can be made
#  min_fwd_time: the shortest amount of time the ball can go before hitting the goal
#  max_fwd_time: the longest amount of time the ball can go before hitting the goal
#  max_rev_time: the longest amount of time the ball can go starting opposite of forward
#  min_time_diff: the minimum difference between the forward and reverse times
#  min_goal_dist: minimum distance between the ball and the red goal
#  n_ball_placement_tries: number of times to try to replace the ball before starting over
#  bvel_mag: ball velocity magnitude, in px / s
#  print_debug: verbose output to describe what's going on in the middle
# Outputs:
#  [trial, forwards_time, reverse_time, n_rects_used]
def make_valid_trial(trname, rectrange = [5,15], min_time = 2., max_fwd_time = 10., max_rev_time = 15.,
                     min_time_diff = 5., min_goal_dist=150, n_ball_placement_tries = 100, bvel_mag=300.,
                     print_debug = False):
    nrects = random.randint(rectrange[0], rectrange[1])
    trjstring = get_trial(trname, nrects)
    tr = loadJSON(json.loads(trjstring))
    # Store some characteristics we'll be using later
    brad = tr.ball[2]
    bcol = tr.ball[3]
    belast = tr.ball[4]
    # For ease of randomness, find the contained area to put the ball in
    min_x = tr.dims[0]
    max_x = 0
    min_y = tr.dims[1]
    max_y = 0
    for w in tr.normwalls:
        # Get left wall - further than max_x?
        if w[0][0] > max_x:
            max_x = w[0][0]
        # Get right wall - further than min_x?
        if w[1][0] < min_x:
            min_x = w[1][0]
        # Get top wall - further than min_y?
        if w[0][1] < min_y:
            min_y = w[0][1]
        # Bottom wall
        if w[1][1] > max_y:
            max_y = w[1][1]
    min_x += brad
    max_x -= brad
    min_y += brad
    max_y -= brad

    rg_mid = _get_red_goal_mid(tr)

    if print_debug:
        print "Random configuration made -- trying ball placements"

    n_tries = 1

    while n_tries < n_ball_placement_tries:
        # Add the ball
        newbpos = [random.randint(min_x, max_x), random.randint(min_y, max_y)]
        heading = _get_goal_heading(np.array(newbpos), rg_mid)
        newbvel = _randomize_heading(heading, np.pi / 4., bvel_mag)
        tr.ball = [newbpos, newbvel, brad, bcol, belast]

        # Is it far enough away from the goal?
        gdist = np.linalg.norm(np.array(newbpos) - rg_mid)
        if gdist < min_goal_dist:
            if print_debug:
                print "Retry: Ball is too close to the goal"
            n_tries += 1
        else:
            # Does the ball overlap with a wall?
            tb = tr.makeTable()
            brect = tb.balls.getboundrect()
            has_col = False
            for w in tb.walls:
                has_col = has_col or brect.colliderect(w.r)
            if has_col:
                if print_debug:
                    print "Retry: Ball overlaps with wall"
                n_tries += 1
            else:
                # Does the ball reach the red goal in time?
                hit_goal = tb.step(max_fwd_time)
                if hit_goal is None:
                    if print_debug:
                        print "Retry: Ball doesn't hit a goal in time"
                    n_tries += 1
                elif hit_goal == GREENGOAL:
                    if print_debug:
                        print "Retry: Ball is outside the container"
                    n_tries += 1
                elif tb.tm < min_time:
                    if print_debug:
                        print "Retry: Ball hits the forward goal too quickly"
                    n_tries += 1
                else:
                    ftime = tb.tm
                    tbr = tr.makeTable()
                    tbr.balls.setvel([-newbvel[0], -newbvel[1]])
                    rev_hit_goal = tbr.step(max_rev_time)
                    rtime = tbr.tm
                    if rev_hit_goal is None:
                        if print_debug:
                            print "Retry: Ball doesn't hit a goal in reverse in time"
                        n_tries += 1
                    elif rev_hit_goal == GREENGOAL:
                        print "ERROR: Somehow the ball escaped the container in reverse!"
                        print "Restarting trial making"
                        n_tries += n_ball_placement_tries
                    elif rtime < min_time:
                        if print_debug:
                            print "Retry: ball hits the reverse goal too quickly"
                        n_tries += 1
                    else:
                        if (rtime - ftime) < min_time_diff:
                            if print_debug:
                                print "Retry: Too close in movement time for forward and reverse"
                            n_tries += 1
                        else:
                            if print_debug:
                                print "Good to go!"
                            data_dict = {
                                'rects': nrects,
                                'walls': len(tr.normwalls),
                                'fwd_time': ftime,
                                'rev_time': rtime,
                                'dist_to_goal': gdist
                            }
                            return tr, data_dict
    # Failure case: restart
    if print_debug:
        print "Hard restart: Too many placement attempts"
    return make_valid_trial(trname, rectrange, min_time , max_fwd_time, max_rev_time,
                     min_time_diff, min_goal_dist, n_ball_placement_tries, bvel_mag,print_debug)

if __name__ == '__main__':

    #stime = time.time()
    #for _ in range(100):
    #    tr, data = make_valid_trial('test', print_debug=False)
    #print "Time:", round(time.time() - stime, 3)

    tr, data = make_valid_trial('test')
    #import pygame as pg
    #pg.init()
    #s = pg.display.set_mode((1000,620))
    #tb = tr.makeTable()
    #tb.demonstrate()


