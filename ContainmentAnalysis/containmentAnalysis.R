library(dplyr)
library(ggplot2)
library(tidyr)
library(lme4)

dat = read.csv('rawdata.csv')
incompletes = names(table(dat$WID)[which(table(dat$WID) != 120)])
gooddat = subset(dat, !(WID %in% incompletes) & (WasBad=="False") & (RawResponse != 'NA'))
gooddat$LogRT = log(gooddat$RT)

# Check that regular trials have faster simulation RTs
regdat = gooddat %>% subset(Class=='regular') %>% group_by(Trial, MotionDirection) %>%
  summarize(lRT = mean(LogRT), MedRT = median(RT), Acc = mean(Response==Goal), GoodRT = median(RT[Response==Goal]))
regdat_lrt = regdat %>% select(Trial, MotionDirection, lRT) %>% spread(MotionDirection, lRT) %>% subset(None > -99999999) # last part is hack
regdat_rt = regdat %>% select(Trial, MotionDirection, MedRT) %>% spread(MotionDirection, MedRT)
regdat_acc = regdat %>% select(Trial, MotionDirection, Acc) %>% spread(MotionDirection, Acc)

ggplot(regdat_lrt, aes(x=exp(None), y=exp(Fwd))) + geom_abline(intercept=0,slope=1) + geom_point() + 
  xlim(c(0,1)) + ylim(c(0,1)) + xlab('None') + ylab('Fwd')
with(regdat_lrt, t.test(Fwd,None,paired=T))

ggplot(regdat_rt, aes(x=None,y=Fwd)) + geom_abline(intercept=0,slope=1) + geom_point() + xlim(c(0,2)) + ylim(c(0,2))
with(regdat_rt, t.test(Fwd,None,paired=T)) # Faster with simulation than no simulation

ggplot(regdat_acc, aes(x=None,y=Fwd)) + geom_abline(intercept=0,slope=1) + geom_point() + xlim(c(0,1)) + ylim(c(0,1))
with(regdat_acc, t.test(Fwd,None, paired=T)) # Accuracy is the same - cannot be driven just by 

# Containment
containdat = subset(gooddat, Class=='contained')
agg_contain_bytrial = containdat %>% group_by(Trial, ContainmentType, ContainmentLevel, MotionDirection) %>%
  summarize(MedRT = median(RT), GoodRT = median(RT[Response=='G']), BadRT = median(RT[Response=='R']),
            MeanSpeed = mean(1/RT), GoodSpeed = mean(1/RT[Response=='G']), BadSpeed = mean(1/RT[Response=='R']),
            Acc = mean(Response=='G'))
agg_contain_all = agg_contain_bytrial %>%
  group_by(ContainmentType, ContainmentLevel, MotionDirection) %>%
  summarize(RT = mean(MedRT), RTsd = sd(MedRT), RTse = sd(MedRT)/sqrt(length(MedRT)),
            Speed = mean(MeanSpeed), Speedsd = sd(MeanSpeed), Speedse = sd(MeanSpeed)/sqrt(length(MeanSpeed)))
agg_contain_good = agg_contain_bytrial %>% subset(!is.na(GoodRT)) %>%
  group_by(ContainmentType, ContainmentLevel, MotionDirection) %>%
  summarize(RT = mean(GoodRT), RTsd = sd(GoodRT), RTse = sd(GoodRT)/sqrt(length(GoodRT)),
            Speed = mean(GoodSpeed), Speedsd = sd(GoodSpeed), Speedse = sd(GoodSpeed)/sqrt(length(GoodSpeed)))


(plot_all_rt = ggplot(agg_contain_all, aes(x=MotionDirection, y=RT, ymax=RT+RTse, ymin=RT-RTse)) +
    geom_point() + geom_linerange() + ylim(0,NA) + facet_grid(ContainmentType ~ ContainmentLevel))
(plot_good_rt = ggplot(agg_contain_good, aes(x=MotionDirection, y=RT, ymax=RT+RTse, ymin=RT-RTse)) +
  geom_point() + geom_linerange() + ylim(0,NA) + facet_grid(ContainmentType ~ ContainmentLevel))
(plot_good_speed = ggplot(agg_contain_good, aes(x=MotionDirection, y=Speed, ymax=Speed+Speedse, ymin=Speed-Speedse)) +
    geom_point() + geom_linerange() + facet_grid(ContainmentType ~ ContainmentLevel))

# Plot RTs by trial
plot_bytrial_complex = ggplot(subset(containdat, ContainmentType=='complex'), aes(x=MotionDirection, y=RT, color=(Response==Goal))) +
  geom_point() + facet_grid(TrialNum~ContainmentLevel)

plot_bytrial_porous = ggplot(subset(containdat, ContainmentType=='porous'), aes(x=MotionDirection, y=RT, color=(Response==Goal))) +
  geom_point() + facet_grid(TrialNum~ContainmentLevel)

plot_bytrial_stopper = ggplot(subset(containdat, ContainmentType=='stopper'), aes(x=MotionDirection, y=RT, color=(Response==Goal))) +
  geom_point() + facet_grid(TrialNum~ContainmentLevel)

plot_bytrial_size = ggplot(subset(containdat, ContainmentType=='size'), aes(x=MotionDirection, y=RT, color=(Response==Goal))) +
  geom_point() + facet_grid(TrialNum~ContainmentLevel)

# Model containment RTs & remake generic trial
mod_all_lrt = lmer(data=gooddat, LogRT ~ ContainmentType*ContainmentLevel*MotionDirection + 
                     (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
mod_contain_lrt = lmer(data=containdat, LogRT ~ ContainmentType*ContainmentLevel*MotionDirection + 
                         (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
generic_trials = agg_contain_all %>% select(ContainmentType, ContainmentLevel, MotionDirection)
generic_trials$WID = 'genericperson'
generic_trials$Trial = 'generictrial'
generic_trials$LogRT = predict(mod_all_lrt, newdata=generic_trials, allow.new.levels=T)
generic_trials$RT = exp(generic_trials$LogRT)
ggplot(generic_trials, aes(x=MotionDirection, y=RT)) + geom_point() + ylim(0,1) +
  facet_grid(ContainmentType ~ ContainmentLevel)

# Reduced model testing
mod_all_lrt_noct = lmer(data=gooddat, LogRT ~ ContainmentLevel*MotionDirection + 
                                                (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
mod_all_lrt_nocl = lmer(data=gooddat, LogRT ~ ContainmentType*MotionDirection + 
                                                (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
mod_all_lrt_nomd = lmer(data=gooddat, LogRT ~ ContainmentType*ContainmentLevel + 
                                                (1|WID) + (1|Trial))

mod_contain_lrt_noct = lmer(data=containdat, LogRT ~ ContainmentLevel*MotionDirection + 
                                            (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
mod_contain_lrt_nocl = lmer(data=containdat, LogRT ~ ContainmentType*MotionDirection + 
                                            (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
mod_contain_lrt_nomd = lmer(data=containdat, LogRT ~ ContainmentType*ContainmentLevel + 
                                            (1|WID) + (1|Trial))

mod_contain_lrt_mdonly = lmer(data=containdat, LogRT ~ MotionDirection + (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
mod_contain_base = lmer(data=containdat, LogRT ~ 1 + (1|WID) + (1|Trial))
