library(plyr)
library(ggplot2)

dat = read.csv('FullFirst.csv')
wids = as.character(unique(dat$WID))

spl.half = function() {
  
  nws = length(wids)
  w1 = sample(wids, nws/2)
  w2 = wids[which(!(wids %in% w1))]
  
  samp1 = ddply(subset(dat, WID %in% w1), 'Trials', summarize,
                Green_1 = mean(First =='G',na.rm=T), Red_1 = mean(First=='R',na.rm=T))
  samp2 = ddply(subset(dat, WID %in% w2), 'Trials', summarize,
                Green_2 = mean(First =='G',na.rm=T), Red_2 = mean(First=='R',na.rm=T))
  
  return(merge(samp1,samp2))
}

sh.cor = function() {return(with(spl.half(), cor(Green_1,Green_2)))}
half.cor = mean(replicate(100, sh.cor()))
