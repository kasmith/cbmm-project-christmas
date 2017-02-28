library(ggplot2)
library(tidyr)
library(dplyr)

# load model and simulation data
simRegFwd = read.csv('regular_forward_model/sim_data.csv')
modelRegFwd = read.csv('regular_forward_model/model_pred.csv') 

simRegNone = read.csv('regular_nomotion_model/sim_data.csv')
modelRegNone = read.csv('regular_nomotion_model/model_pred.csv') 

simComb = simRegFwd %>% mutate(FGreen=PGreen, FRed = PRed, FBounce = AvgBounces, FTime = AvgTime) %>% 
  select(-PGreen,-PRed,-AvgBounces,-AvgTime) %>% 
  merge(simRegNone %>% mutate(NGreen=PGreen, NRed = PRed, NBounce = AvgBounces, NTime = AvgTime) %>% 
          select(-PGreen,-PRed,-AvgBounces,-AvgTime))
#with(simComb, cor(FGreen, NGreen))
#with(simComb, cor(FRed, NRed))
#with(simComb, cor(FBounce, NBounce))
#with(simComb, cor(FTime, NTime))

# load human data
ADD_RT = FALSE
rawdat = read.csv('../ContainmentAnalysis/rawdata.csv')
incompletes = names(table(rawdat$WID)[which(table(rawdat$WID) != 120)])
gooddat = subset(rawdat, !(WID %in% incompletes) & (WasBad=="False") & (RawResponse != 'NA') & RT > .01)
if (ADD_RT) gooddat$RT = gooddat$RT + .5
gooddat$LogRT = log(gooddat$RT)
gooddat$WasCorrect = with(gooddat, Response == Goal)

# filter forward regular trials
regFwdDat = gooddat %>% filter(Class=='regular', MotionDirection=='Fwd') %>% group_by(Trial) %>%
  summarize(lRT = mean(LogRT), MedRT = median(RT), Acc = mean(Response==Goal), GoodRT = median(RT[Response==Goal]))
regNoneDat = gooddat %>% filter(Class=='regular', MotionDirection=='None') %>% group_by(Trial) %>%
  summarize(lRT = mean(LogRT), MedRT = median(RT), Acc = mean(Response==Goal), GoodRT = median(RT[Response==Goal]))
regComb = regFwdDat %>% mutate(FlRT = lRT, FAcc = Acc) %>% select(Trial,FlRT,FAcc) %>%
  merge(regNoneDat %>% mutate(NlRT = lRT, NAcc = Acc) %>% select(Trial,NlRT,NAcc))
regAll = merge(regComb, simComb)

# Look at gross differences / similarities between human and model
# Where are there big differences in the model prediction of green across motion/no motion? Are they also there in people?
regAll$FEmpGreen = with(regAll,ifelse(Goal == 'G', FAcc, 1-FAcc))
regAll$NEmpGreen = with(regAll,ifelse(Goal == 'G', NAcc, 1-NAcc))
regAll$ModGoalDiff = with(regAll, FGreen - NGreen)
#ggplot(regAll, aes(x=NEmpGreen,y=FEmpGreen, color=ModGoalDiff)) + geom_point() + geom_abline(intercept=0,slope=1)
regAll$EmpGoalDiff = with(regAll, FEmpGreen - NEmpGreen)
with(regAll, cor(ModGoalDiff, EmpGoalDiff))
qplot(ModGoalDiff, EmpGoalDiff, data=regAll) + geom_abline(intercept=0, slope=1)

# Fit models
THRESH = 2
modelThreshFwd = modelRegFwd %>% filter(Threshold == THRESH) %>% select(Trial,ExpectedAccuracy,ExpectedNumSamples) %>% merge(regFwdDat %>% select(Trial, lRT, Acc)) %>% merge(simRegFwd %>% select(Trial, AvgBounces, AvgTime))
modelThreshNone = modelRegNone %>% filter(Threshold == THRESH) %>% select(Trial,ExpectedAccuracy,ExpectedNumSamples) %>% merge(regNoneDat %>% select(Trial, lRT, Acc)) %>% merge(simRegNone %>% select(Trial, AvgBounces, AvgTime))

lmFwd = lm(lRT ~ ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples, data=modelThreshFwd)
modelThreshFwd$FPred = predict(lmFwd)
modelThreshNone$NPred = predict(lmFwd, newdata=modelThreshNone)

regAll = regAll %>% merge(modelThreshFwd %>% mutate(FThreshAcc=ExpectedAccuracy, FSamples=ExpectedNumSamples) %>% select(Trial, FPred, FThreshAcc, FSamples)) %>%
  merge(modelThreshNone %>% mutate(NThreshAcc=ExpectedAccuracy, NSamples=ExpectedNumSamples) %>% select(Trial, NPred, NThreshAcc, NSamples))

with(regAll, cor(FlRT, FPred))
with(regAll, cor(NlRT, NPred))

# Are there systematic errors across the two?
regAll$FErr = with(regAll, FlRT - FPred)
regAll$NErr = with(regAll, NlRT - NPred)
qplot(NErr, FErr, data=regAll)
with(regAll, cor(NErr, NlRT)) # Damn... correlations between errors and observations remain... there's data left to explain

# Which is more parsimonious -- fitting RT on forward and applying to no motion or fitting RT on no motion
REGTRIALS = unique(regAll$Trial)

getCVCors = function() {
  fittrs = sample(REGTRIALS, floor(length(REGTRIALS)/2))
  cvtrs = REGTRIALS[!(REGTRIALS %in% fittrs)]
  fmod = lm(lRT ~ ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples, data=subset(modelThreshFwd, Trial %in% fittrs))
  nmod = lm(lRT ~ ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples, data=subset(modelThreshNone, Trial %in% fittrs))
  cvs = subset(modelThreshNone, Trial %in% cvtrs)
  cvs$CVFPred = predict(fmod, newdata=cvs)
  cvs$CVNPred = predict(nmod, newdata=cvs)
  return(with(cvs,c(Fwd=cor(CVFPred,lRT),None=cor(CVNPred,lRT))))
}
allcors = data.frame(t(replicate(500, getCVCors())))
t.test(allcors$Fwd,allcors$None,paired=T) # Clearly the forward model doesn't explain everything
qplot(None,Fwd,data=allcors) + geom_abline(intercept=0, slope=1)

