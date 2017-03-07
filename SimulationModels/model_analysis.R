library(ggplot2)
library(tidyr)
library(dplyr)

# load model and simulation data
simRegFwd = read.csv('regular_forward_model/sim_data.csv')
modelRegFwd = read.csv('regular_forward_model/model_pred.csv') 

simRegNone = read.csv('regular_nomotion_model/sim_data.csv')
modelRegNone = read.csv('regular_nomotion_model/model_pred.csv') 

simContFwd = read.csv('contained_forward_model/sim_data.csv')
modelContFwd = read.csv('contained_forward_model/model_pred.csv') 

simContNone = read.csv('contained_nomotion_model/sim_data.csv')
modelContNone = read.csv('contained_nomotion_model/model_pred.csv') 

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

# iterate through threshold values
samplesCors = vector()
accCors = vector()
#for (t in names(table(select(modelRegFwd, Threshold)))) 
#for (t in 1:10)
t=2
{
  cur = modelRegFwd %>% filter(Threshold == t) %>% select(Trial,ExpectedAccuracy,ExpectedNumSamples) %>% merge(regFwdDat %>% select(Trial, lRT, Acc)) %>% merge(simRegFwd %>% select(Trial, AvgBounces, AvgTime))
  ggplot(data=cur, aes(y=lRT,x=ExpectedNumSamples)) + geom_point() + geom_smooth(method='lm', col='red')
  
  samplesCors[t] = cor(cur$lRT, cur$ExpectedNumSamples)
  accCors[t] = cor(cur$ExpectedAccuracy, cur$Acc)
  
  print(paste('================ [', t, '] ================'))
  #print(samplesCors[t])
  #print(summary(lm(cur$lRT ~ cur$ExpectedNumSamples)))
  print(summary(lm(lRT ~ ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples, data=cur)))
}

# filter nomotion regular trials
regNoneDat = gooddat %>% filter(Class=='regular', MotionDirection=='None') %>% group_by(Trial) %>%
  summarize(lRT = mean(LogRT), MedRT = median(RT), Acc = mean(Response==Goal), GoodRT = median(RT[Response==Goal]))

# iterate through threshold values
samplesCors = vector()
accCors = vector()
#for (t in names(table(select(modelRegNone, Threshold)))) 
for (t in 1:10)
{
  cur = modelRegNone %>% filter(Threshold == t) %>% select(Trial,ExpectedAccuracy,ExpectedNumSamples) %>% merge(regNoneDat %>% select(Trial, lRT, Acc)) %>% merge(simRegNone %>% select(Trial, AvgBounces, AvgTime))
  ggplot(data=cur, aes(y=lRT,x=ExpectedNumSamples)) + geom_point() + geom_smooth(method='lm', col='red')
  
  samplesCors[t] = cor(cur$lRT, cur$ExpectedNumSamples)
  accCors[t] = cor(cur$ExpectedAccuracy, cur$Acc)
  
  print(paste('================ [', t, '] ================'))
  #print(samplesCors[t])
  #print(summary(lm(cur$lRT ~ cur$ExpectedNumSamples)))
  print(summary(lm(lRT ~ ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples, data=cur)))
}








# filter forward contained trials
contFwdDat = gooddat %>% filter(Class=='contained', MotionDirection=='Fwd') %>% group_by(Trial) %>%
  summarize(lRT = mean(LogRT), MedRT = median(RT), Acc = mean(Response==Goal), GoodRT = median(RT[Response==Goal]))

# iterate through threshold values
samplesCors = vector()
accCors = vector()
#for (t in names(table(select(modelRegFwd, Threshold)))) 
for (t in 2:2)
{
  cur = modelContFwd %>% filter(Threshold == t) %>% select(Trial,ExpectedAccuracy,ExpectedNumSamples) %>% merge(contFwdDat %>% select(Trial, lRT, Acc)) %>% merge(simContFwd %>% select(Trial, AvgBounces, AvgTime))
  ggplot(data=cur, aes(y=lRT,x=ExpectedNumSamples)) + geom_point() + geom_smooth(method='lm', col='red')
  
  samplesCors[t] = cor(cur$lRT, cur$ExpectedNumSamples)
  accCors[t] = cor(cur$ExpectedAccuracy, cur$Acc)
  
  print(paste('================ [', t, '] ================'))
  #print(samplesCors[t])
  #print(summary(lm(cur$lRT ~ cur$ExpectedNumSamples)))
  print(summary(lm(lRT ~ ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples, data=cur)))
}

# filter nomotion regular trials
contNoneDat = gooddat %>% filter(Class=='contained', MotionDirection=='None') %>% group_by(Trial) %>%
  summarize(lRT = mean(LogRT), MedRT = median(RT), Acc = mean(Response==Goal), GoodRT = median(RT[Response==Goal]))

# iterate through threshold values
samplesCors = vector()
accCors = vector()
#for (t in names(table(select(modelRegNone, Threshold)))) 
for (t in 1:10)
{
  cur = modelContNone %>% filter(Threshold == t) %>% select(Trial,ExpectedAccuracy,ExpectedNumSamples) %>% merge(contNoneDat %>% select(Trial, lRT, Acc)) %>% merge(simContNone %>% select(Trial, AvgBounces, AvgTime))
  ggplot(data=cur, aes(y=lRT,x=ExpectedNumSamples)) + geom_point() + geom_smooth(method='lm', col='red')
  
  samplesCors[t] = cor(cur$lRT, cur$ExpectedNumSamples)
  accCors[t] = cor(cur$ExpectedAccuracy, cur$Acc)
  
  print(paste('================ [', t, '] ================'))
  #print(samplesCors[t])
  #print(summary(lm(cur$lRT ~ cur$ExpectedNumSamples)))
  print(summary(lm(lRT ~ ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples, data=cur)))
}
