library(plyr)

dat = read.csv('OnlineRGGoodData.csv')

getFromTrial = function(wid, trnm) {
  
  sdat = subset(dat, Worker == wid & Trial == trnm)
  if(nrow(sdat)==0) {return(NA)}
  sdat = sdat[order(sdat$Time),] # Just to make sure
  
  fg = which(sdat$NormPrediction=='G')
  fr = which(sdat$NormPrediction=='R')
  
  if(length(fg)==0 & length(fr)==0) {
    return(NA)
  } else if(length(fg)==0) {
    return('R')
  } else if(length(fr)==0) {
    return('G')
  } else {
    if(fg[1] < fr[1]) {
      return('G')
    } else {
      return('R')
    }
  }
}

wids = unique(dat$Worker)
trnms = unique(dat$Trial)
retdat = data.frame(WID = rep(wids,each=length(trnms)),
                    Trials = rep(trnms, times=length(wids)))
retdat$First = mapply(getFromTrial,retdat$WID,retdat$Trials)

write.csv(retdat, 'FullFirst.csv', row.names=F)

trdat = ddply(retdat, 'Trials', summarize, Green = mean(First=='G',na.rm=T), 
              Red = mean(First=='R',na.rm=T))
names(trdat)[1] = 'Trial'
goalinfo = unique(dat[c('Trial','NormGoal')])
names(goalinfo)[2] = 'Goal'
trdat = merge(trdat, goalinfo)
trdat$Accuracy = with(trdat,ifelse(Goal=='R',Red,Green))
write.csv(trdat,'FirstGoal.csv',row.names=F)
