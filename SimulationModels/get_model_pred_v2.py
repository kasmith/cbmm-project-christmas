from __future__ import division, print_function
from physicsTable import *
from physicsTable.constants import *
from physicsTable.models import PointSimulation
import os, json, glob

def get_model_pred():
    with open('sim_data_full.json', 'r') as f:
        sim_data = json.load(f)

    model_pred = {}
    with open('model_pred_full.csv', 'w') as csv_out:
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

    with open('model_pred.json', 'w') as json_out:
        json.dump(model_pred, json_out)

if __name__ == '__main__':
    get_model_pred()
