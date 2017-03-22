from sqlalchemy import create_engine, MetaData, Table
import json, sys, os, collections
import pandas as pd
from physicsTable.constants import *

responsedict = {REDGOAL : "R", GREENGOAL : "G", 299 : "NA"}
motiondict = {0 : "None", 1 : "Fwd", -1 : "Rev"}
db_url = "mysql://k2smith:ptdbpw227@psiturkdb.cfk6ynxmnsif.us-west-2.rds.amazonaws.com:3306/psiturkdb"
table_name = 'contain'
data_column_name = 'datastring'

def reverse(rawresp):
    if rawresp == 'NA':
        return 'NA'
    elif rawresp == 'R':
        return 'G'
    else:
        return 'R'

def load_data_by_exp(experimentlist):
    if not (hasattr(experimentlist, '__iter__') and not isinstance(experimentlist, (str, bytes))):
        experimentlist = [experimentlist]
    experimentlist = [str(e) for e in experimentlist]
    # boilerplace sqlalchemy setup
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.bind = engine
    table = Table(table_name, metadata, autoload=True)
    # make a query and loop through
    s = table.select()
    rows = s.execute()

    rawdata = []
    conds = []
    #status codes of subjects who completed experiment
    statuses = [3,4,5,7]
    # if you have workers you wish to exclude, add them here
    exclude = []
    for row in rows:
        # only use subjects who completed experiment and aren't excluded
        if row['status'] in statuses and row['uniqueid'] not in exclude and row['codeversion'] in experimentlist:
            rawdata.append(row[data_column_name])
            conds.append(row["cond"])

    # Now we have all participant datastrings in a list.
    # Let's make it a bit easier to work with:

    # parse each participant's datastring as json object
    # and take the 'data' sub-object
    data = [json.loads(part)['data'] for part in rawdata]

    # insert uniqueid field into trialdata in case it wasn't added
    # in experiment:
    for part in data:
        for record in part:
            # Kludge... if saved as a list (should only be first exp) then we know the ordering
            if type(record['trialdata']) == list:
                rdict = {'WID' : record['uniqueid'],
                         'Condition': record['trialdata'][9],
                         'Trial' : record['trialdata'][0],
                         'TrialOrder' : record['trialdata'][1],
                         'RT' : record['trialdata'][2],
                         'RawResponse' : responsedict[record['trialdata'][3]],
                         'MotionDirection' : motiondict[record['trialdata'][4]],
                         'Switched' : record['trialdata'][5],
                         'Score': record['trialdata'][6],
                         'RealGoal' : responsedict[record['trialdata'][7]],
                         'WasBad' : record['trialdata'][8]
                         }
                record['trialdata'] = rdict
            else:
                record['trialdata']['WID'] = record['uniqueid']

    # flatten nested list so we just have a list of the trialdata recorded
    # each time psiturk.recordTrialData(trialdata) was called.
    data = [record['trialdata'] for part in data for record in part]

    # Put all subjects' trial data into a dataframe object from the
    # 'pandas' python library: one option among many for analysis
    return pd.DataFrame(data)



# Changes data from loading into the right form for Experiment 1.1 (&2?)
def transform_prediction(records):
    records['Response'] = [reverse(r) if s else r for r,s in zip(records['RawResponse'],records['Switched'])]
    records['Goal'] = [reverse(g) if s else g for g,s in zip(records['RealGoal'],records['Switched'])]
    trnm = records['Trial']
    trspls = [t.split('_') for t in trnm]
    records['TrialBase'] = ['_'.join(ts[:2]) for ts in trspls]
    records['Class'] = ['regular' if len(ts) == 2 else 'contained' for ts in trspls]
    records['ContainmentType'] = [ts[0] if len(ts) == 3 else "NA" for ts in trspls]
    records['ContainmentLevel'] = [ts[2] if len(ts) == 3 else "NA" for ts in trspls]
    records['TrialNum'] = [ts[1] for ts in trspls]

    newdf = records[['WID','Condition','Trial','TrialBase','Class','ContainmentType','ContainmentLevel',
                     'TrialNum','MotionDirection','Response','RT','Goal','Switched','RawResponse','WasBad']]

    return newdf


if __name__ == '__main__':
    transform_prediction(load_data_by_exp([1.1])).to_csv("exp1_data.csv", index = False)