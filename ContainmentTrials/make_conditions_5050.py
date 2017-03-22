import json, os

odir = "ConditionLists"
cont_types = [['porous', 'a'],
              ['size', 'c'],
              ['stopper', 'a'],
              ['complex', 'b']]
n_ea_cont = 6
n_ct = len(cont_types)
n_conds = 3
n_reg_trial = 24 # 80% of trials

lists = [[] for i in range(n_conds)]

# List for easy lookup / mixing of conditions
cont_conds = ['forward','static','reverse']

# Make the conditions for the contained trials
i = 0
for ci in range(n_ct):
    ctype = cont_types[ci]
    for cn in range(n_ea_cont):
        basenm = ctype[0] + '_' + str(cn+1) + '_' + ctype[1] + '.json'
        for condn in range(n_conds):
            direc = cont_conds[(i+condn) % n_conds]
            lists[condn].append( (basenm, direc) )
        i += 1

# Make the conditions for the regular trials
for i in range(n_reg_trial):
    trnm = "regular_" + str(i) + ".json"
    for condn in range(n_conds):
        if (condn + i) % 3 == 0:
            direc = "static"
        else:
            direc = "forward"
        lists[condn].append( (trnm, direc) )

with open(os.path.join(odir, "ConditionList5050.json"), 'w') as ofl:
    json.dump(lists, ofl)
