from __future__ import division, print_function
from physicsTable import *
from physicsTable.constants import *
from physicsTable.models import PointSimulation
import os, json, glob, sys

KAP_V_NORM = 20 # simulation for conditions with motion (small noise in velocity)
KAP_V_NOMOT = 1e-10 # simulation for no motion condition (very high noise, ie almost uniform distribution)
KAP_B = 25
KAP_M = 50000
P_ERR = 25

TIMEUP = 50.

N_SIMS = 5000
CPUS = 1

WRITE_JSON = True

# Regex used to list trials that are going to be simulated
TRIAL_REGEX_CONT = '*_*_*.json' # containment trials
TRIAL_REGEX_REG = 'regular_*.json' # regular trials

def run_single_sim(table, n_sims, kap_v, kap_b, kap_m, p_err, timeup, cpus):
    ps = PointSimulation(table, kap_v, kap_b, kap_m, p_err, nsims=n_sims, cpus=cpus, maxtime=timeup)
    ps.runSimulation()
    outcomes = ps.getOutcomes()
    bounces = ps.getBounces()
    times = ps.getTimes()
    p_green = outcomes[GREENGOAL]/n_sims
    p_red = outcomes[REDGOAL]/n_sims
    p_timeup = 1 - p_green - p_red
    avg_bounces = sum(bounces) / len(bounces)
    avg_time = sum(times) / len(times)
    return p_green, p_red, p_timeup, avg_bounces, avg_time


def get_sim_data(sim_write_name, n_sims=N_SIMS, kap_v_norm=KAP_V_NORM, kap_v_nomot = KAP_V_NOMOT, kap_b=KAP_B, kap_m=KAP_M, p_err=P_ERR, timeup = TIMEUP, cpus=CPUS):
    goal_dict = get_goal_dict()

    with open(sim_write_name, 'w') as csv_out:
        csv_out.write('Trial,IsContained,Direction,Goal,PGreen,PRed,PTimeUp,AvgBounces,AvgTime\n')
        json_dict = {}

        os_path_c = os.path.join('..', 'psiturk-rg-cont', 'templates', 'trials', TRIAL_REGEX_CONT)
        for f in glob.iglob(os_path_c):
            trial_name = f.split(os.path.sep)[-1][:-5]
            print('Running simulations for: ' + trial_name)

            tr = loadFromJSON(f)
            json_dict[trial_name] = {}

            for dir in ['forward','reverse','none']:
                tab = tr.makeTable()
                if dir == 'reverse':
                    tab.balls.setvel(map(lambda x: -x, tab.balls.getvel()))
                if dir == 'none':
                    kap_v = kap_v_nomot
                else:
                    tab.step(.5)
                    kap_v = kap_v_norm
                p_green, p_red, p_timeup, avg_bounces, avg_time = run_single_sim(tab, n_sims, kap_v, kap_b, kap_m, p_err, timeup, cpus)
                goal = goal_dict[trial_name]
                csv_line = ','.join(
                    (trial_name, 'contained',dir, goal, str(p_green), str(p_red), str(p_timeup), str(avg_bounces), str(avg_time))) + '\n'
                csv_out.write(csv_line)

                if WRITE_JSON:
                    json_dict[trial_name][dir] = {'goal': goal, 'p_green': p_green, 'p_red': p_red, 'avg_bounces': avg_bounces, 'avg_time': avg_time}

        os_path_r = os.path.join('..', 'psiturk-rg-cont', 'templates', 'trials', TRIAL_REGEX_REG)
        for f in glob.iglob(os_path_r):
            trial_name = f.split(os.path.sep)[-1][:-5]
            print('Running simulations for: ' + trial_name)

            tr = loadFromJSON(f)
            json_dict[trial_name] = {}

            for dir in ['forward', 'none']:
                tab = tr.makeTable()
                if dir == 'none':
                    kap_v = kap_v_nomot
                else:
                    tab.step(.5)
                    kap_v = kap_v_norm
                p_green, p_red, p_timeup, avg_bounces, avg_time = run_single_sim(tab, n_sims, kap_v, kap_b, kap_m,
                                                                                 p_err, timeup, cpus)
                goal = goal_dict[trial_name]
                csv_line = ','.join(
                    (trial_name, 'regular', dir, goal, str(p_green), str(p_red), str(p_timeup), str(avg_bounces),
                     str(avg_time))) + '\n'
                csv_out.write(csv_line)

                json_dict[trial_name][dir] = {'goal': goal, 'p_green': p_green, 'p_red': p_red,
                                         'avg_bounces': avg_bounces, 'avg_time': avg_time}


    if WRITE_JSON:
        with open('sim_data_full.json', 'w') as json_out:
            json.dump(json_dict, json_out)

    return json_dict

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


def get_model_pred(sim_data, model_pred_name, json_pred_name):

    model_pred = {}
    with open(model_pred_name, 'w') as csv_out:
        csv_out.write('Trial,Direction,Threshold,ExpectedAccuracy,ExpectedNumSamples\n')

        for trial_name in sim_data:
            print('Running model for: ' + trial_name)
            trdat = sim_data[trial_name]
            model_pred[trial_name] = {}
            for dir in trdat:
                model_pred[trial_name][dir] = {}
                if trdat[dir]['goal'] == 'G':
                    p_in = trdat[dir]['p_green']
                    p_out = trdat[dir]['p_red']
                else:
                    p_in = trdat[dir]['p_red']
                    p_out = trdat[dir]['p_green']
                p_none = 1 - p_in - p_out
                p_igh = p_in / (p_in + p_out) # Probability of going in given there wasn't a time-up event

                for threshold in range(1, 11):
                    expected_accuracy = p_igh ** threshold / (p_igh ** threshold + (1-p_igh) ** threshold)
                    expected_num_samples = threshold / (1-2*p_igh) - 2*threshold / (1-2*p_igh) * (1-((1-p_igh)/p_igh)**threshold) / (1-((1-p_igh)/p_igh)**(2*threshold))
                    expected_num_samples /= (1 - p_none) # Adjust for "wasted" trials with no evidence

                    csv_line = ','.join((trial_name, dir, str(threshold), str(expected_accuracy), str(expected_num_samples))) + '\n'
                    csv_out.write(csv_line)
                    model_pred[trial_name][dir][threshold] = {'expected_accuracy': expected_accuracy, 'expected_num_samples': expected_num_samples}

    with open(json_pred_name, 'w') as json_out:
        json.dump(model_pred, json_out)

def do_time_modeling(timeup_val):
    t_str = str(timeup_val)
    sdat = get_sim_data("sim_data_full_"+t_str+".csv", timeup = timeup_val)
    get_model_pred(sdat, "model_pred_full"+t_str+".csv", "model_json_full"+t_str+".csv")
    return

if __name__ == '__main__':
    try:
        tlim = float(sys.argv[1])
        do_time_modeling(tlim)
    except:
        print("Incorrect time input")