import os, json

iflnm = os.path.join('..','psiturk-rg-cont','trialdata.csv')
oflnm = "rawdata.csv"

with open(iflnm, 'rU') as ifl, open(oflnm, 'w') as ofl:
    ofl.write('WID,Condition,Trial,TrialBase,Class,ContainmentType,ContainmentLevel,TrialNum,MotionDirection,Response,RT,Goal,Switched,RawResponse,WasBad\n')
    for rln in ifl:
        rln = rln.strip('\n')
        wid, _, _, rdat = rln.split(',',3)
        dat = json.loads(rdat.strip("\"'").replace("\"\"", "\""))
        if isinstance(dat[5], bool):
            trnm, order, rt, rawresp, mottype, wassw, score, realgoal, wasbad, cond = dat
            trspl = trnm.split('_')
            dowrite = True
            trbase = trspl[0] + '_' + trspl[1]
            tnum = trspl[1]
            if trspl[0] == 'regular':
                trclass = "regular"
                conttype = "NA"
                contlevel = "NA"
            else:
                trclass = "contained"
                conttype = trspl[0]
                contlevel = trspl[2]
            if not wassw:
                wassw = "False"
                if rawresp == 201:
                    actresp = "R"
                    normresp = "R"
                elif rawresp == 202:
                    actresp = "G"
                    normresp = "G"
                elif rawresp == 299:
                    actresp = "NA"
                    normresp = "NA"
                else:
                    dowrite = False
                if realgoal == 201:
                    rg = "R"
                elif realgoal == 202:
                    rg = "G"
                else:
                    dowrite = False
            else:
                wassw = "True"
                if rawresp == 201:
                    actresp = "R"
                    normresp = "G"
                elif rawresp == 202:
                    actresp = "G"
                    normresp = "R"
                elif rawresp == 299:
                    actresp = "NA"
                    normresp = "NA"
                else:
                    dowrite = False
                if realgoal == 201:
                    rg = "G"
                elif realgoal == 202:
                    rg = "R"
                else:
                    dowrite = False
            if mottype == 1:
                mot = 'Fwd'
            elif mottype == 0:
                mot = 'None'
            else:
                mot = 'Rev'
            if wasbad:
                wb = 'True'
            else:
                wb = 'False'



            if dowrite:
                ofl.write(wid + ',' + str(cond) + ',' + trnm + ',' + trbase + ',' + trclass + ',' + conttype + ',' + contlevel + ',' + tnum + ',')
                ofl.write(mot + ',' + normresp + ',' + str(rt) + ',' + rg + ',' + wassw + ',' + actresp + ',' + wb + '\n')

