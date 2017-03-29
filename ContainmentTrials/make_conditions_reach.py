import os, glob, random, json

# List of lists of different conditions, change this to generate ConditionList
CONDITIONS = [['forward', 'reverse', 'static'], ['in', 'out']]
# Regex to get list of trials to be matched to conditions
TRIAL_REGEX = '*_*_*.json'
# Directory with json trial, also output directory
DIR = os.path.join('..', 'psiturk-rg-reach', 'templates', 'trials')

# Creates all possible tuples of different conditions
condition_combinations = [[]]
for l in CONDITIONS:
    temp = condition_combinations
    condition_combinations = []
    for c1 in temp:
        for c2 in l:
            condition_combinations.append(c1 + [c2])

# Get number of different conditions
num_conditions = len(condition_combinations)

# Get list of trial names (in DIR) to be matched to different conditions
trial_list = glob.glob(os.path.join(DIR, TRIAL_REGEX))
trial_list = [x.split(os.sep)[-1] for x in trial_list]

# Generate the different experimental conditions (trials matched to conditions)
experiment_conditions = [[] for i in range(num_conditions)]
conditions_idx = 0
for trial in trial_list:
    for i in range(num_conditions):
        idx = (conditions_idx + i) % num_conditions
        experiment_conditions[i].append([trial] + condition_combinations[idx])
    conditions_idx += 1

# Save ConditionList
with open(os.path.join(DIR, 'ConditionList.json'), 'w') as f:
    json.dump(experiment_conditions, f)
