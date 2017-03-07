library(ggplot2)
library(tidyr)
library(dplyr)

# load model and simulation data
simRegFwd = read.csv('regular_forward_model/sim_data.csv')
modelRegFwd = read.csv('regular_forward_model/model_pred.csv') 

simContFwd = read.csv('contained_forward_model/sim_data.csv')
modelContFwd = read.csv('contained_forward_model/model_pred.csv') 

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


# filter forward contained trials
contFwdDat = gooddat %>% filter(Class=='contained', MotionDirection=='Fwd') %>% group_by(Trial) %>%
  summarize(lRT = mean(LogRT), MedRT = median(RT), Acc = mean(Response==Goal), GoodRT = median(RT[Response==Goal]))

# Fit models
THRESH = 2
modelThreshRegFwd = modelRegFwd %>% filter(Threshold == THRESH) %>% select(Trial,ExpectedAccuracy,ExpectedNumSamples) %>% merge(regFwdDat %>% select(Trial, lRT, Acc)) %>% merge(simRegFwd %>% select(Trial, AvgBounces, AvgTime))
modelThreshContFwd = modelContFwd %>% filter(Threshold == THRESH) %>% select(Trial,ExpectedAccuracy,ExpectedNumSamples) %>% merge(contFwdDat %>% select(Trial, lRT, Acc)) %>% merge(simContFwd %>% select(Trial, AvgBounces, AvgTime))

ggplot(data=modelThreshContFwd, aes(y=lRT, x=ExpectedNumSamples)) + geom_point()

lmRegFwd = lm(lRT ~ ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples, data=modelThreshRegFwd)
modelThreshRegFwd$RFPred = predict(lmRegFwd)
modelThreshContFwd$CFPred = predict(lmRegFwd, newdata=modelThreshContFwd)

ggplot(data=modelThreshRegFwd, aes(y=lRT,x=RFPred)) + geom_point()
ggplot(data=modelThreshContFwd, aes(y=lRT,x=CFPred)) + geom_point()

#regAll = regAll %>% merge(modelThreshFwd %>% mutate(FThreshAcc=ExpectedAccuracy, FSamples=ExpectedNumSamples) %>% select(Trial, FPred, FThreshAcc, FSamples)) %>%
#  merge(modelThreshNone %>% mutate(NThreshAcc=ExpectedAccuracy, NSamples=ExpectedNumSamples) %>% select(Trial, NPred, NThreshAcc, NSamples))

with(modelThreshRegFwd, cor(lRT, RFPred))
with(modelThreshContFwd, cor(lRT, CFPred))

# Are there systematic errors across the two?
modelThreshRegFwd$RFErr = with(modelThreshRegFwd, lRT - RFPred)
modelThreshContFwd$CFErr = with(modelThreshContFwd, lRT - CFPred)
#qplot(NErr, FErr, data=regAll)
with(modelThreshContFwd, cor(CFErr, lRT)) # Damn... correlations between errors and observations remain... there's data left to explain