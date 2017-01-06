import json, os

odir = "JSON"
cont_types = ['porous','size','stopper','complex']
n_ea_cont = 6
n_ct = len(cont_types)
n_conds = 9
n_reg_trial = 96 # 80% of trials

lists = [[] for i in range(n_conds)]

# List for easy lookup / mixing of conditions
cont_conds = [['a', 'forward'],
              ['b', 'reverse'],
              ['c', 'static'],
              ['a', 'reverse'],
              ['b', 'static'],
              ['c', 'forward'],
              ['a', 'static'],
              ['b', 'forward'],
              ['c', 'reverse']]

# Make the conditions for the contained trials
i = 0
for ci in range(n_ct):
    ctype = cont_types[ci]
    for cn in range(n_ea_cont):
        basenm = ctype + '_' + str(cn+1) + '_'
        for condn in range(n_conds):
            ltr, direc = cont_conds[(i+condn) % n_conds]
            lists[condn].append( (basenm+ltr+'.json', direc) )
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

with open(os.path.join(odir, "ConditionList.json"), 'w') as ofl:
    json.dump(lists, ofl)
