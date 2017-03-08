library(ggplot2)
library(tidyr)
library(dplyr)
library(broom)

DATA_FOLDER = "timeup_models"
TIMEUPS = seq(10,50,by=5)
MODFORM = EmpRT ~ ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples
#MODFORM = EmpRT ~ ExpectedNumSamples + AvgBounces:ExpectedNumSamples

# load human data
ADD_RT = FALSE
rawdat = read.csv('../ContainmentAnalysis/rawdata.csv')
incompletes = names(table(rawdat$WID)[which(table(rawdat$WID) != 120)])
gooddat = subset(rawdat, !(WID %in% incompletes) & (WasBad=="False") & (RawResponse != 'NA') & RT > .01)
if (ADD_RT) gooddat$RT = gooddat$RT + .5
gooddat$LogRT = log(gooddat$RT)
gooddat$WasCorrect = with(gooddat, Response == Goal)

trialdat = gooddat %>% mutate(Direction=MotionDirection) %>% group_by(Trial, Direction) %>%
  summarize(N = length(WID), EmpAcc = mean(WasCorrect), EmpLogRT = mean(LogRT), EmpLogRTSD = sd(LogRT)) %>% 
  mutate(EmpRT = exp(EmpLogRT))
levels(trialdat$Direction) = c('forward', 'none', 'reverse')

# Function for fitting specific RT data
fit_rt = function(fit_data) {
  fitlm = lm(MODFORM, data=fit_data)
  ret = list(llh = logLik(fitlm),
             r = cor(fit_data$EmpRT, predict(fitlm)),
             coefs = coef(fitlm),
             model = fitlm)
  return(ret)
}

# Function for analyzing the best fitting time cutoff 
analyze_timeup = function(timeup_val, fit_on_regular = F, fit_on_forward = F) {
  # Load the data
  sim_dat = read.csv(paste(DATA_FOLDER, "/sim_data_full_", timeup_val, ".0.csv", sep=""))
  thresh_dat = read.csv(paste(DATA_FOLDER, "/model_pred_full_", timeup_val, ".0.csv", sep=""))  
  dat = merge(trialdat, sim_dat) %>% merge(thresh_dat) %>% arrange(Trial, Direction, Threshold)
  
  # Filter the data for specific fits
  fitdat = dat
  if(fit_on_regular) fitdat = fitdat %>% filter(IsContained == 'regular')
  if(fit_on_forward) fitdat = fitdat %>% filter(Direction == 'forward')
  
  # Apply the linear model across all thresholds
  thresholds = unique(fitdat$Threshold)
  fitllhs = sapply(thresholds, function(t) {fit_rt(fitdat %>% filter(Threshold == t))$llh})
  names(fitllhs) = thresholds
  
  # Figure out which is the best fit (by log-likelihood)
  bestllh = fitllhs[which(fitllhs == max(fitllhs))]
  bestthresh = as.integer(names(bestllh))
  
  # Reapply the model to the best threshold fit
  modlist = fit_rt(fitdat %>% filter(Threshold == bestthresh))
  bestmod = modlist$model
  bestdat = dat %>% filter(Threshold == bestthresh)
  bestdat$ModelRT = predict(bestmod, newdata=bestdat)
  rbycond = bestdat %>% group_by(Direction, IsContained) %>% summarize(r = cor(EmpRT, ModelRT))
  ret = list(data = bestdat,
             r = with(bestdat, cor(EmpRT, ModelRT)),
             model = bestmod,
             corbycond = rbycond,
             threshold = bestthresh,
             fitllh = modlist$llh,
             all_llhs = fitllhs,
             mse = with(bestdat, sum((EmpRT-ModelRT)^2)))
  return(ret)
}

# Fit across different timeups
analyze_model = function(fit_on_regular = F, fit_on_forward = F) {
  fits = lapply(TIMEUPS, function(t) analyze_timeup(t, fit_on_regular = fit_on_regular, fit_on_forward = fit_on_forward))
  fits_llh = sapply(fits, function(x) x$fitllh)
  names(fits_llh) = TIMEUPS
  best_tup_idx = which(fits_llh == max(fits_llh))
  best_tup = TIMEUPS[best_tup_idx]
  best_fit = fits[[best_tup_idx]]
  best_fit$timeup = best_tup
  best_fit$llh_grid = fits_llh
  return(best_fit)
}

# Do some analysis on the best fitting model
analyzed = analyze_model(fit_on_regular = T, fit_on_forward = F)
best_dat = analyzed$data
best_tup = analyzed$timeup
best_thresh = analyzed$threshold
best_corlist = analyzed$corbycond
best_model = analyzed$model

#llh_grid = data.frame(Thresh = rep(1:10, times=length(TIMEUPS)), TUp = rep(TIMEUPS, each=10))


best_corlist = best_corlist %>%
  merge(best_dat %>% group_by(Direction, IsContained) %>% 
          summarize(rByTime = cor(AvgTime, EmpRT), rByBounce = cor(AvgBounces, EmpRT), rBySamp = cor(ExpectedNumSamples, EmpRT)))

best_dat = best_dat %>% mutate(EmpRT_Lwr = exp(EmpLogRT - 2*EmpLogRTSD/sqrt(N)), EmpRT_Upr = exp(EmpLogRT + 2*EmpLogRTSD/sqrt(N)))
ggplot(best_dat, aes(x=ModelRT, y=EmpRT, ymin = EmpRT_Lwr, ymax = EmpRT_Upr, shape = Direction, color = IsContained)) +
  geom_abline(intercept=0, slope=1, linetype = 'dashed') + 
  #geom_linerange() + 
  geom_point(alpha = .7) + 
  theme_bw()

# Just the data plotted in CogSci Fig 5
mot_dat = best_dat %>% filter(Direction != "none") %>% mutate(TrType = ifelse(IsContained=='regular','non-topo', as.character(Direction)))
mot_dat = mot_dat %>% 
  merge(read.csv('../ContainmentTrials/TrialLengths.csv') %>% 
          mutate(TrType = ifelse(Type=='Regular', 'non-topo', ifelse(Direction=='Fwd','forward','reverse')), ActTime=Time) %>%
          select(Trial, TrType, ActTime))

ggplot(mot_dat, aes(x=ModelRT, y=EmpRT, ymin = EmpRT_Lwr, ymax = EmpRT_Upr, color = TrType)) +
  geom_abline(intercept=0, slope=1, linetype = 'dashed') + 
  #geom_linerange() + 
  geom_point(alpha = .7) + 
  #xlim(.3,1) + # Miss two outliers with ridiculous travel times if you use this limit
  theme_bw() + ylim(0,1)
with(mot_dat, cor(EmpRT, ModelRT))
with(mot_dat, cor(EmpRT, ModelRT, method='spearman'))

# Repeat of Fig 5 but with average sim time
ggplot(mot_dat, aes(x=AvgTime, y=EmpRT, ymin = EmpRT_Lwr, ymax = EmpRT_Upr, color = TrType)) +
  geom_point(alpha = .7) + 
  theme_bw() + ylim(0, 1)
with(mot_dat, cor(EmpRT, AvgTime))
with(mot_dat, cor(EmpRT, AvgTime, method='spearman'))


cortype = "pearson"
# cortype = "spearman"
mot_dat %>% group_by(TrType) %>% summarize(mod_r = cor(EmpRT, ModelRT, method=cortype), 
                                           simt_r = cor(EmpRT, AvgTime, method=cortype), 
                                           act_r = cor(EmpRT, ActTime, method=cortype), 
                                           timecor = cor(AvgTime, ActTime))

# Figure out slope / bias over conditions
bias_means = best_dat %>% group_by(Direction, IsContained) %>%
  summarize(MeanRT = mean(EmpRT), MeanModRT = mean(ModelRT))

bias_table = best_dat %>% group_by(Direction, IsContained) %>%
  do(tmplm = lm(EmpRT ~ ModelRT, data= .)) %>%
  mutate(Intercept = coef(tmplm)[1], Slope = coef(tmplm)[2]) %>% select(-tmplm) %>%
  merge(bias_means)

bias_table_noint = best_dat %>% group_by(Direction, IsContained) %>%
  do(tmplm = lm(EmpRT ~ ModelRT + 0, data= .)) %>%
  mutate(Slope = coef(tmplm)[1]) %>% select(-tmplm) %>%
  merge(bias_means)

# Looking at only the contained trials...
ctype = strsplit(as.character(best_dat$Trial),'_')
ctype_c = sapply(ctype, function(x) x[1])
ctype_l = sapply(ctype, function(x) x[3])
best_dat$ContType = with(best_dat, ifelse(IsContained != 'contained', NA,
                                          ctype_c))
best_dat$ContLevel = ctype_l
rm(ctype, ctype_c, ctype_l)
ggplot(best_dat %>% filter(IsContained == 'contained'), aes(x=ModelRT, y=EmpRT, color=ContType, shape=Direction)) +
  geom_abline(intercept=0, slope=1, linetype = 'dashed') +
  geom_point()
best_dat %>% filter(IsContained == 'contained') %>% group_by(ContType, Direction) %>% 
  summarize(MSE = mean((ModelRT - EmpRT)^2), r = cor(ModelRT, EmpRT))


# Test whether contained trials are fit better by aggregation or this model
mod_agg_cont = lm(EmpRT ~ ContType * ContLevel * Direction, data=best_dat %>% filter(IsContained == 'contained'))
cor(with(best_dat %>% filter(IsContained == 'contained'), EmpRT), predict(mod_agg_cont)) # r = .68
with(best_dat %>% filter(IsContained == 'contained'), cor(EmpRT, ModelRT)) # r = .50
# So not quite as good as knowing the average across each trial type, level, and direction

# Redo plot across conditions with model (no CIs though)
agg_cont = best_dat %>% filter(IsContained == 'contained') %>% group_by(ContType, ContLevel, Direction) %>%
  summarize(AvgRT = mean(EmpRT), AvgModRT = mean(ModelRT))
ggplot(agg_cont, aes(x=Direction)) + geom_point(aes(y=AvgModRT), color='red') + geom_point(aes(y=AvgRT)) +
  facet_grid(ContType ~ ContLevel) + ylim(0,.8) + theme_bw()


ggplot(best_dat %>% filter(IsContained=='contained'), 
       aes(x=ModelRT, y=EmpRT, color=ContType, shape=ContLevel)) + 
  geom_abline(intercept=0, slope=1, linetype='dashed') +
  geom_point() +
  facet_grid(. ~ Direction) + 
  theme_bw() + xlim(0,1.6) + ylim(0,1.6)

ggplot(best_dat, 
       aes(x=ModelRT, y=EmpRT, color=IsContained)) + 
  geom_abline(intercept=0, slope=1, linetype='dashed') +
  geom_point(alpha = .8) +
  facet_grid(. ~ Direction) + 
  theme_bw() + xlim(0,1.6) + ylim(0,1.6)

ggplot(best_dat, 
       aes(x=ModelRT, y=EmpRT, color=Direction)) + 
  geom_abline(intercept=0, slope=1, linetype='dashed') +
  geom_point(alpha = .8) +
  facet_grid(. ~ IsContained) + 
  theme_bw() + xlim(0,1.6) + ylim(0,1.6)

best_dat %>% group_by(IsContained) %>% summarize(r = cor(EmpRT, ModelRT), r_sp = cor(EmpRT, ModelRT, method='spearman'))


#
# Fitting everything... should be more targeted
#
# timeups_allfit = lapply(TIMEUPS, analyze_timeup)
# timeups_allfit_cor = sapply(timeups_allfit, function(x) x$r)
# timeups_allfit_thresh = sapply(timeups_allfit, function(x) x$thresh)
# timeups_allfit_fitllh = sapply(timeups_allfit, function(x) x$fitllh)
# timeups_allfit_mse = sapply(timeups_allfit, function(x) x$mse)
# 
# timeups_fwdonly = lapply(TIMEUPS, function(t) analyze_timeup(t, fit_on_forward = T))
# timeups_fwdonly_cor = sapply(timeups_fwdonly, function(x) x$r)
# timeups_fwdonly_thresh = sapply(timeups_fwdonly, function(x) x$thresh)
# timeups_fwdonly_fitllh = sapply(timeups_fwdonly, function(x) x$fitllh)
# timeups_fwdonly_mse = sapply(timeups_fwdonly, function(x) x$mse)
# 
# timeups_regonly = lapply(TIMEUPS, function(t) analyze_timeup(t, fit_on_regular = T))
# timeups_regonly_cor = sapply(timeups_regonly, function(x) x$r)
# timeups_regonly_thresh = sapply(timeups_regonly, function(x) x$thresh)
# timeups_regonly_fitllh = sapply(timeups_regonly, function(x) x$fitllh)
# timeups_regonly_mse = sapply(timeups_regonly, function(x) x$mse)
# 
# timeups_regfwd = lapply(TIMEUPS, function(t) analyze_timeup(t, fit_on_regular = T, fit_on_forward = T))
# timeups_regfwd_cor = sapply(timeups_regfwd, function(x) x$r)
# timeups_regfwd_thresh = sapply(timeups_regfwd, function(x) x$thresh)
# timeups_regfwd_fitllh = sapply(timeups_regfwd, function(x) x$fitllh)
# timeups_regfwd_mse = sapply(timeups_regfwd, function(x) x$mse)
