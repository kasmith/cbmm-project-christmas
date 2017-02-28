from __future__ import division, print_function
from physicsTable import *
from physicsTable.constants import *
from physicsTable.models import PointSimulation
import os, json, glob

def get_model_pred():
    with open('sim_data.json', 'r') as f:
        sim_data = json.load(f)

    model_pred = {}
    with open('model_pred.csv', 'w') as csv_out:
        csv_out.write('Trial,Threshold,ExpectedAccuracy,ExpectedNumSamples\n')

        for trial_name in sim_data:
            print('Running model for: ' + trial_name)
            model_pred[trial_name] = {}
            if sim_data[trial_name]['goal'] == 'G':
                p = sim_data[trial_name]['p_green']
            else:
                p = sim_data[trial_name]['p_red']

            for threshold in range(1, 11):
                expected_accuracy = p ** threshold / (p ** threshold + (1-p) ** threshold)
                expected_num_samples = threshold / (1-2*p) - 2*threshold / (1-2*p) * (1-((1-p)/p)**threshold) / (1-((1-p)/p)**(2*threshold))

                csv_line = ','.join((trial_name, str(threshold), str(expected_accuracy), str(expected_num_samples))) + '\n'
                csv_out.write(csv_line)
                model_pred[trial_name][threshold] = {'expected_accuracy': expected_accuracy, 'expected_num_samples': expected_num_samples}

    with open('model_pred.json', 'w') as json_out:
        json.dump(model_pred, json_out)

if __name__ == '__main__':
    get_model_pred()
