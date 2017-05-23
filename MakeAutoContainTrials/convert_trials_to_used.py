import json
import os
from shutil import copyfile
from physicsTable import *
from physicsTable.constants import *

# Takes in the selected trials file, copies random trials to those used in the experiment

selected_trial_fl = "SelectedTrials.csv"
rtr_dir = "AutoGenTrials"
used_dir = "UsedTrials"


S_PER_STEP = 0.025
PRESTEPS = 20
POST_SPEEDUP = 2
S_PER_POST_STEP = S_PER_STEP*POST_SPEEDUP


def get_trial_number(trname):
    return int(trname.split('_')[1])

def next_dir(curdir):
    if curdir == "forward":
        return "reverse"
    elif curdir == "reverse":
        return "static"
    elif curdir == "static":
        return "forward"
    else:
        raise Exception("not the right direction")

def getrpos(tb, digits = 2):
    p = tb.balls.getpos()
    return [round(p[0],digits), round(p[1], digits)]

n_conds = 3
trial_lists = [[] for _ in range(n_conds)]
fake_lists = [[] for _ in range(n_conds)]
idx = 0
dir_idx = 0
with open(selected_trial_fl, 'rU') as sel_tr:
    sel_tr.next()
    for ln in sel_tr:
        l = ln.strip('\n').split(',')
        trnm = l[0].strip('"')
        tr_num = get_trial_number(trnm)
        if tr_num >= 2000:
            trdir = os.path.join(rtr_dir,"Randoms_2000")
        elif tr_num >= 1000:
            trdir = os.path.join(rtr_dir, "Randoms_1000")
        else:
            trdir = os.path.join(rtr_dir, "Randoms_0000")
        copyfile(os.path.join(trdir, trnm+'.json'), os.path.join(used_dir, trnm+'.json'))

        # Figure out the motion paths for the ball
        tr = loadTrialFromJSON(os.path.join(trdir, trnm+'.json'))
        # Forward path
        ftb = tr.makeTable()
        fwd_pres = []
        fwd_posts = []
        fwd_pres.append(getrpos(ftb))
        for i in range(PRESTEPS):
            ftb.step(S_PER_STEP)
            fwd_pres.append(getrpos(ftb))
        run_f = True
        while run_f:
            r = ftb.step(S_PER_POST_STEP)
            if r is not None:
                run_f = False
                if r == GREENGOAL:
                    fwd_goal = "G"
                elif r == REDGOAL:
                    fwd_goal = "R"
                else:
                    raise Exception("Got an illegal goal type")
            fwd_posts.append(getrpos(ftb))
        # Reverse path
        rtb = tr.makeTable()
        rev_pres = []
        rev_posts = []
        rtb.step(PRESTEPS*S_PER_STEP)
        rv = rtb.balls.getvel()
        rtb.balls.setvel((-rv[0], -rv[1]))
        rev_pres.append(getrpos(rtb))
        for i in range(PRESTEPS):
            rtb.step(S_PER_STEP)
            rev_pres.append(getrpos(rtb))
        run_r = True
        while run_r:
            r = rtb.step(S_PER_POST_STEP)
            if r is not None:
                run_r = False
                if r == GREENGOAL:
                    rev_goal = "G"
                elif r == REDGOAL:
                    rev_goal = "R"
                else:
                    raise Exception("Got an illegal goal type")
            rev_posts.append(getrpos(rtb))
        # Static path
        stb = tr.makeTable()
        stat_pres = []
        stat_posts = []
        stat_pres.append(getrpos(stb))
        for i in range(PRESTEPS):
            stat_pres.append(getrpos(stb))
        run_s = True
        while run_s:
            r = stb.step(S_PER_POST_STEP)
            if r is not None:
                run_s = False
                if r == GREENGOAL:
                    stat_goal = "G"
                elif r == REDGOAL:
                    stat_goal = "R"
                else:
                    raise Exception("Got an illegal goal type")
            stat_posts.append(getrpos(stb))

        fwd_part = [trnm+".json", "forward", fwd_pres, fwd_posts, fwd_goal]
        rev_part = [trnm+".json", "reverse", rev_pres, rev_posts, rev_goal]
        stat_part = [trnm+".json", "static", stat_pres, stat_posts, stat_goal]
        parts = [fwd_part, rev_part, stat_part]

        for j in range(n_conds):
            trial_lists[j].append(parts[(dir_idx+j) % 3])

        if idx < 3:
            for k in range(3):
                fake_lists[k].append(parts[idx])


        print trnm, "done"

        idx += 1
        if (idx % 16) == 0:
            dir_idx += 1

with open(os.path.join(used_dir, "trial_list.json"), 'w') as tfl:
    json.dump(trial_lists, tfl)
with open(os.path.join(used_dir, "fake_trial_list.json"), 'w') as tfl:
    json.dump(fake_lists, tfl)