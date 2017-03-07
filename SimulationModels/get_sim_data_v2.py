from __future__ import division, print_function
from physicsTable import *
from physicsTable.constants import *
from physicsTable.models import PointSimulation
import os, json, glob

#KAP_V = 20 # simulation for conditions with motion (small noise in velocity)
KAP_V = 1e-10 # simulation for no motion condition (very high noise, ie almost uniform distribution)
KAP_B = 25
KAP_M = 50000
P_ERR = 25

N_SIMS = 5000
CPUS = 1

WRITE_JSON = True

# Regex used to list trials that are going to be simulated
TRIAL_REGEX = '*_*_*.json' # containment trials
#TRIAL_REGEX = 'regular_*.json' # regular trials

def get_sim_data(n_sims=N_SIMS, kap_v=KAP_V, kap_b=KAP_B, kap_m=KAP_M, p_err=P_ERR, cpus=CPUS):
    goal_dict = get_goal_dict()

    with open('sim_data.csv', 'w') as csv_out:
        csv_out.write('Trial,Goal,PGreen,PRed,AvgBounces,AvgTime\n')
        json_dict = {}

        os_path = os.path.join('..', 'psiturk-rg-cont', 'templates', 'trials', TRIAL_REGEX)
        for f in glob.iglob(os_path):
            trial_name = f.split(os.path.sep)[-1][:-5]
            print('Running simulations for: ' + trial_name)

            tr = loadFromJSON(f)
            tab = tr.makeTable()
            # I believe the table settings are from the beginning, so if you want an accurate model of what people see in the 'towards'
            #  case, you should move the ball forward 500ms
            tab.step(.5)

            ps = PointSimulation(tab, kap_v, kap_b, kap_m, p_err, nsims = n_sims, cpus=cpus)
            ps.runSimulation()
            outcomes = ps.getOutcomes()
            bounces = ps.getBounces()
            times = ps.getTimes()

            goal = goal_dict[trial_name]
            p_green = outcomes[GREENGOAL]/N_SIMS
            p_red = outcomes[REDGOAL]/N_SIMS
            avg_bounces = sum(bounces) / len(bounces)
            avg_time = sum(times) / len(times)

            csv_line = ','.join((trial_name, goal, str(p_green), str(p_red), str(avg_bounces), str(avg_time))) + '\n'
            csv_out.write(csv_line)

            if WRITE_JSON:
                json_dict[trial_name] = {'goal': goal, 'p_green': p_green, 'p_red': p_red, 'avg_bounces': avg_bounces, 'avg_time': avg_time}

    if WRITE_JSON:
        with open('sim_data.json', 'w') as json_out:
            json.dump(json_dict, json_out)

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

def get_goal_dict():
    goal_dict = {}
    data_path = os.path.join('..', 'ContainmentAnalysis', 'rawdata.csv')
    with open(data_path, 'r') as f:
        for line in f:
            line_split = line.split(',')
            trial_name = line_split[2]
            if trial_name not in goal_dict:
                goal_dict[trial_name] = line_split[-4]
    return goal_dict



if __name__ == '__main__':
    get_sim_data()
