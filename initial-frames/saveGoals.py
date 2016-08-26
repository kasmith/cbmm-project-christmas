from extractInfo import getGoal
from physicsTable import loadTrial
import os 
import pickle

output_dir = '/home/ubuntu/frames'
trdir = os.path.join('..','python-trials', 'trials')

if __name__ == '__main__':
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    goal_dict = {}
    if os.path.exists(os.path.join(output_dir, 'goal_dict.pickle')):
        with open(os.path.join(output_dir, 'goal_dict.pickle'), 'rb') as handle:
            goal_dict = pickle.load(handle)

    counter = 0
    for tr in os.listdir(trdir):
        if tr[:-4] not in goal_dict:
            counter += 1
            print 'Trial ' + tr
            goal = getGoal(loadTrial(os.path.join(trdir, tr)))
            goal_dict[tr[:-4]] = int(goal == 'green')
        
            if counter % 1000 == 0:
                print 'Saving first ' + str(counter) + ' examples'
                with open(os.path.join(output_dir, 'goal_dict' + str(counter) +'.pickle'), 'wb') as handle:
                      pickle.dump(goal_dict, handle)


    with open(os.path.join(output_dir, 'goal_dict.pickle'), 'wb') as handle:
          pickle.dump(goal_dict, handle)
