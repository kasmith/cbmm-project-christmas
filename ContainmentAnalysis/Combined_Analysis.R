
#' ---
#' title: Containment Analyses
#' author: Kevin A Smith
#' date: Apr 7, 2017
#' output:
#'    html_document:
#'      theme: default
#'      highlight: tango
#' ---

#+ General settings, echo = FALSE, results = 'hide', fig.width = 4, fig.height = 4 ------------------------------------------------------------------------------

knitr::opts_chunk$set(warning=F, message=F, cache = T, echo=F)
options(digits = 3)
kable = knitr::kable
export = F
FIGURE_DIR = "Figures/"
N_BOOT_SAMPS = 500 # Crank this up to ~1000 for the paper
USE_GOOD_ONLY = F
ADD_RT = F
TOOFAST = .01
# For the models
MODEL_FOLDER = "../SimulationModels/timeup_models"
MODEL_TIMEUP_CHOICES = seq(10,50,b=5)
#MODEL_FORMULA = EmpRT ~ ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples
#MODEL_FORMULA = EmpRT ~ ExpectedNumSamples + AvgBounces:ExpectedNumSamples
MODEL_FORMULA = EmpRT ~ HasMotion + ExpectedNumSamples + AvgTime:ExpectedNumSamples + AvgBounces:ExpectedNumSamples
MODEL_FIT_ON_REGULAR_ONLY = T
MODEL_FIT_ON_FORWARD_ONLY = F

library(parallel)
library(lme4)
library(ggplot2)
library(tidyr)
library(dplyr)
library(xtable) # Not directly used but helpful for latex translating
library(lmerTest)
library(lsmeans)
library(broom)
options(contrasts = c('contr.sum','contr.poly'))

# Helper functions
print.t.test = function(test) {
  return(paste("t(",round(test$parameter,1),")=",round(test$statistic,2),", p=",signif(test$p.value,3),sep=""))
}

print.binom.test = function(test) {
  return(paste('binomial test (', test$statistic, ' / ', test$parameter, '), p=', signif(test$p.value,3),sep=''))
}

print.model.anova.test = function(test) {
  return(paste("F(",test$Df[2],",",test$Res.Df[2],")=",signif(test$F[2],3),", p=",signif(test$Pr[2],3),sep=''))
}

print.slope.test = function(test, slopename) {
  smtst = summary(test)
  df = smtst$df[2]
  row = smtst$coefficients[slopename,]
  return(paste("t(",df,")=",signif(row['t value'],3),", p=",signif(row['Pr(>|t|)'],3),sep=''))
}

make.ci.from.lrt.lsm = function(lsmtest, sig = 3) {
  sumry = summary(lsmtest)
  mn = signif(exp(sumry$lsmean),sig)
  lwr = signif(exp(sumry$lower.CL),sig)
  upr = signif(exp(sumry$upper.CL),sig)
  return(paste(mn," (95% CI: [", lwr, ", ", upr, "])",sep = ""))
}

make.ci.from.ci.lsm = function(lsmtest, sig = 3) {
  sumry = summary(lsmtest)
  mn = signif(exp(sumry$estimate),sig)
  lwr = signif(exp(sumry$lower.CL),sig)
  upr = signif(exp(sumry$upper.CL),sig)
  return(paste(mn," (95% CI: [", lwr, ", ", upr, "])",sep = ""))
}

#+ Experiment 1: Loading ----------------------------------------------------------

# Original experiment
rawdat = read.csv('../ContainmentData/exp1_data.csv')
incompletes = names(table(rawdat$WID)[which(table(rawdat$WID) != 120)])
gooddat = subset(rawdat, !(WID %in% incompletes) & (WasBad=="False") & (RawResponse != 'NA') & RT > TOOFAST)
if (ADD_RT) gooddat$RT = gooddat$RT + .5
gooddat$LogRT = log(gooddat$RT)
gooddat$WasCorrect = with(gooddat, Response == Goal)
gooddat$HasMotion = factor(with(gooddat, ifelse(MotionDirection=='None','No','Yes')))

pct_bad = with(subset(rawdat, !(WID %in% incompletes)), mean(WasBad=='True'))
pct_na = with(subset(rawdat, !(WID %in% incompletes) & (WasBad=="False")), mean(is.na(RawResponse)))
pct_toofast = with(subset(rawdat, !(WID %in% incompletes) & (WasBad=="False") & (RawResponse != 'NA')), mean(RT < TOOFAST))
n_subjects = length(unique(gooddat$WID))

# Other information
trlen_dat = read.csv('../ContainmentTrials/TrialLengths.csv')

#+ Experiment 1: Results: RT -----------------------------------

# *********************
# Data subsetting to contained trials
# *********************
containdat = subset(gooddat, Class=='contained')
containdat$AltMD = factor(with(containdat, ifelse(MotionDirection == 'Fwd','Fwd','Other')))

if (USE_GOOD_ONLY) {containdat = subset(containdat, WasCorrect)}

bootstrap_overall_geort = function(subdat, ntimes = 500) {
  trnms = unique(subdat$Trial)
  rets = NULL
  for (i in 1:ntimes) {
    bsrts = NULL
    for (tr in trnms) {
      trsub = subset(subdat, Trial==tr)
      bsrts = rbind(bsrts, 
                    data.frame(Trial = tr, RT = with(trsub, base::sample(LogRT, length(LogRT), replace=T))))
    }
    rets = c(rets, mean(bsrts$RT))
  }
  return(rets)
}

# *********************
# Aggregate by containment type/level
# *********************

agg_contain_all = containdat %>% group_by(ContainmentType, ContainmentLevel, MotionDirection) %>%
  summarize(MeanLogRT = mean(LogRT), GoodLRT = mean(LogRT[Response=='G']), BadLRT = mean(LogRT[Response!='G']),
            Acc = mean(Response=='G'), N = length(Response))
agg_contain_all$LogRT_975 = agg_contain_all$LogRT_025 = NA
for (rn in 1:nrow(agg_contain_all)) {
  sdat = subset(containdat, ContainmentType==agg_contain_all$ContainmentType[rn] &
                  ContainmentLevel==agg_contain_all$ContainmentLevel[rn] &
                  MotionDirection==agg_contain_all$MotionDirection[rn])
  bssamps = bootstrap_overall_geort(sdat, N_BOOT_SAMPS)
  bsquantile = quantile(bssamps, c(.025, .975))
  agg_contain_all$LogRT_025[rn] = bsquantile[1]
  agg_contain_all$LogRT_975[rn] = bsquantile[2]
}

levels(agg_contain_all$MotionDirection) = c('Towards', 'No motion','Away')
levels(agg_contain_all$ContainmentLevel) = c('A','B','C')
levels(agg_contain_all$ContainmentType) = c('Complexity','Porousness','Size','Stopper')
agg_contain_all$ContainmentType = relevel(agg_contain_all$ContainmentType, "Stopper")
agg_contain_all$ContainmentType = relevel(agg_contain_all$ContainmentType, "Porousness")
agg_contain_all$ContainmentType = relevel(agg_contain_all$ContainmentType, "Size")

# *********************
# Plots of RTs by containment type/level
# *********************

plot_contain_all = ggplot(agg_contain_all, aes(x=MotionDirection, y=exp(MeanLogRT), ymax=exp(LogRT_975), ymin = exp(LogRT_025))) +
  geom_point() + geom_linerange() + ylim(0,NA) + facet_grid(ContainmentType ~ ContainmentLevel) +
  theme_bw() + xlab('Motion Condition') + ylab('Reaction Time (s)')
plot_contain_acc_all = ggplot(agg_contain_all, aes(x=MotionDirection, y=Acc)) +
  geom_bar(stat='identity') + ylim(0,1) + facet_grid(ContainmentType ~ ContainmentLevel) +
  theme_bw() + xlab('Motion Condition') + ylab('Accuracy')

aca = agg_contain_all
levels(aca$ContainmentLevel) = c("Level 1", "Level 2", "Level 3")
plot_contain_all_paper_a = ggplot(subset(aca, ContainmentType %in% c('Size','Porousness')), 
                                  aes(x=MotionDirection, y=1000*exp(MeanLogRT), ymax=1000*exp(LogRT_975), ymin = 1000*exp(LogRT_025))) +
  geom_point() + geom_linerange() + ylim(0,800) + facet_grid(ContainmentType ~ ContainmentLevel) +
  theme_bw() + xlab('Motion Condition') + ylab('Reaction Time (ms)') +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
plot_contain_all_paper_b = ggplot(subset(aca, ContainmentType %in% c('Stopper','Complexity')), 
                                  aes(x=MotionDirection, y=1000*exp(MeanLogRT), ymax=1000*exp(LogRT_975), ymin = 1000*exp(LogRT_025))) +
  geom_point() + geom_linerange() + ylim(0,800) + facet_grid(ContainmentType ~ ContainmentLevel) +
  theme_bw() + xlab('Motion Condition') + ylab('Reaction Time (ms)') +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
plot_contain_all_poster_full = ggplot(aca, 
                                      aes(x=MotionDirection, y=1000*exp(MeanLogRT), ymax=1000*exp(LogRT_975), ymin = 1000*exp(LogRT_025))) +
  geom_point() + geom_linerange() + ylim(0,800) + facet_grid(ContainmentType ~ ContainmentLevel) +
  theme_bw() + xlab('Motion Condition') + ylab('Reaction Time (ms)') +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

# *********************
# Building models of reaction times (contained)
# *********************

# Model with everything in it
mod_all_lrt = lmer(data=gooddat, LogRT ~ ContainmentType*ContainmentLevel*MotionDirection + 
                     (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
# Model with just the containment data
mod_contain_lrt = lmer(data=containdat, LogRT ~ ContainmentType*ContainmentLevel*MotionDirection + 
                     (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
# Reduced models
mod_contain_null = lmer(data=containdat, LogRT ~ 1 + (1|WID) + (1|Trial))
mod_contain_typeonly = update(mod_contain_null, ~ . + ContainmentType)
mod_contain_levelonly = update(mod_contain_null, ~ . + ContainmentLevel)
mod_contain_motiononly = update(mod_contain_null, ~ . + MotionDirection + (1|Trial:MotionDirection))

test_all_type = anova(mod_contain_null, mod_contain_typeonly)
test_all_level = anova(mod_contain_null, mod_contain_levelonly)
test_all_motion = anova(mod_contain_null, mod_contain_motiononly)


# *********************
# Linear contrasts of differences in RT model
# *********************

mod_contain_forcontrast = lmer(data=containdat, LogRT ~ ContainmentType*ContainmentLevel*AltMD + 
                                 (1|WID) + (1|Trial) + (1|Trial:MotionDirection))

lsmctr_motconds = lsmeans(mod_contain_lrt, "MotionDirection")
lsmctr_type = lsmeans(mod_contain_lrt, "ContainmentType")
lsmctr_level = lsmeans(mod_contain_lrt, "ContainmentLevel")

# Just the simplest (a) cases : does the Fwd RT differ from average of None/Rev?
lsmctr_bymotion_ina = lsmeans(mod_contain_forcontrast, "AltMD", at = list(ContainmentLevel='a'))
contrast_bymotion_ina = contrast(lsmctr_bymotion_ina, method='trt.vs.ctrl')

# Just the most complex (c) cases : does the Fwd RT differ from average of None/Rev?
lsmctr_bymotion_inc = lsmeans(mod_contain_forcontrast, "AltMD", at = list(ContainmentLevel='c'))
contrast_bymotion_inc = contrast(lsmctr_bymotion_inc, method='trt.vs.ctrl')

# Is this forward vs. other, or motion vs. none?
contrast_byindmotion_overall = contrast(lsmctr_motconds, method='trt.vs.ctrl')
lsmctr_motconds_granular = lsmeans(mod_contain_lrt, "MotionDirection", by = c('ContainmentType','ContainmentLevel'))
contrast_byindmotion_granular = contrast(lsmctr_motconds_granular, method='trt.vs.ctrl')

# *********************
# Modeling RT differences in the regular trials
# *********************

regdat = gooddat %>% subset(Class=='regular') %>% group_by(Trial, MotionDirection) %>%
  summarize(LogRT = mean(LogRT), GeomMeanRT = exp(mean(LogRT)), MedRT = median(RT), Acc = mean(Response==Goal), GoodRT = median(RT[Response==Goal]),
            NTotal = length(WasCorrect), NRight = sum(WasCorrect))
regdat_lrt = regdat %>% select(Trial, MotionDirection, LogRT) %>% spread(MotionDirection, LogRT) %>% subset(None > -99999999) # last part is hack
regdat_geolrt = regdat %>% select(Trial, MotionDirection, GeomMeanRT) %>% spread(MotionDirection, GeomMeanRT) %>% subset(None > -99999999) # last part is hack
regdat_acc = regdat %>% select(Trial, MotionDirection, Acc) %>% spread(MotionDirection, Acc)

# Test - are log RTs different between fwd and none motion for matched trials
reg_lrt_test = t.test(regdat_lrt$Fwd, regdat_lrt$None, paired = T)
# Test - is accuracy different between fwd and none motion for matched trials
reg_acc_test = t.test(regdat_acc$Fwd, regdat_acc$None, paired = T)
# Test - is accuracy above chance for motion information?
reg_acc_fwd_chance = with(subset(regdat, MotionDirection=='Fwd'), binom.test(sum(NRight),sum(NTotal)))
# Test - is accuracy above chance for no motion information?
reg_acc_none_chance = with(subset(regdat, MotionDirection=='None'), binom.test(sum(NRight),sum(NTotal)))
# Confidence intervals
reg_acc_fwd_ci = exp(t.test(regdat_lrt$Fwd)$conf.int)
reg_acc_none_ci = exp(t.test(regdat_lrt$None)$conf.int)

# Plot - RTs of matched trials
plot_reg_rt = ggplot(regdat_geolrt, aes(x=None, y=Fwd)) + geom_abline(intercept=0,slope=1,linetype='dashed') +
  geom_point(alpha = .8) + theme_bw() +
  xlim(0,1) + ylim(0,1) + xlab("No motion") + ylab("Motion") + ggtitle("Reaction Time")
# Plot - acc of matched trials
plot_reg_acc = ggplot(regdat_acc, aes(x=None, y=Fwd)) + geom_abline(intercept=0,slope=1,linetype='dashed') +
  geom_point(alpha = .8) + theme_bw() +
  xlim(0,1) + ylim(0,1) + xlab("No motion") + ylab("Motion") + ggtitle("Accuracy")


#+ Experiment 1: Results: Accuracy & Learning ----------------------------

# Test - is accuracy for contained trials above accuracy for non-contained
reg_vscont_acc_tab = with(gooddat, table(Class, WasCorrect))
reg_vscont_acc_sum = gooddat %>% group_by(Class) %>% summarize(Acc = mean(WasCorrect))
reg_vscont_acc = chisq.test(reg_vscont_acc_tab)

# Accuracy of contained vs regular trials
acc_tab = with(gooddat, table(Class, WasCorrect))
test_all_acc = chisq.test(acc_tab)
acc_tab_disp = gooddat %>% group_by(Class) %>% summarize(Accuracy = mean(WasCorrect))

# Modeling differences in accuracy by trial type
mod_acc_contain = glm(WasCorrect ~ ContainmentType*ContainmentLevel*MotionDirection, family=binomial, data=containdat)

# Are people spending more time deliberating on no motion & rev trials (and thus are more accurate)?
containdat_sz_cmplx = subset(containdat, ContainmentType %in% c('size','complex'))
mod_acc_limit = glm(data=containdat_sz_cmplx, family=binomial,
                    WasCorrect ~ ContainmentType*ContainmentLevel*MotionDirection)


acc_bymot = containdat %>% group_by(MotionDirection, ContainmentType) %>% 
  summarize(Acc = mean(WasCorrect)) %>% spread(MotionDirection, Acc)
contr_acc_bymot = lsmeans(mod_acc_limit, 'MotionDirection') %>% contrast(method='pairwise')

# Modeling learning over time
mod_learning = lmer(data=gooddat, LogRT ~ TrialNum + (1|WID) + (1|Trial))
learn_amt = exp(fixef(mod_learning)[2])
learn_ci = exp(confint(mod_learning)['TrialNum',])

#+ Experiment 1: Results: Writeout ------------------------------------------

#' # Experiment 1 - Results
#' 
#' All of these results are based on the data from `r n_subjects` participants. Participants minimized or hid their browser `r pct_bad` 
#' proportion of time. They did not indicate a prediction `r pct_na` proportion of the time. They made responses too quickly (under 
#' `r TOOFAST*1000`ms) `r pct_toofast` proportion of the time.
#' 
#' Simple check - are predictions faster with motion information than without? The regular trials with motion had shorter reaction times on average than the same trials 
#' without motion (geometric mean rt of `r mean(regdat_geolrt$Fwd)`s for motion, `r mean(regdat_geolrt$None)`s
#' for no motion, `r print.t.test(reg_lrt_test)`). This reaction time difference existed even with no reliable 
#' difference in accuracy across matched trials (mean accuracy of motion trials: `r mean(regdat_acc$Fwd)`, 
#' mean accuracy of no motion trials `r mean(regdat_acc$None)`, `r print.t.test(reg_acc_test)`).
#' 
#' The plot below displays the geometric mean of reaction times across all conditions and motion types.
#' The rows represent different dimensions of containment, while the columns represent the levels that 
#' vary along those dimensions. Bars represent 95% confidence intervals bootstrapped with `r N_BOOT_SAMPS` samples
#' 
print(plot_contain_all)
#' 
#' All analyses of reaction time were performed using log-RT (Whelan, 2008) but transformed into reaction
#' times for display and reporting.
#' 
#' We first test for gross differences across the trial types and motion conditions. This was accomplished
#' with a mixed-effects model using random effects for participants, trials, and the trial by motion condition
#' interaction (to control for any differences in how the motion information might affect simulation in 
#' a particular trial).
anova(mod_contain_lrt, type=1)

fef_contain = fixef(mod_contain_lrt)
#' Note: all numbers are given in seconds
#' 
#' The most important factor seems to be the motion condition, with 
#' Towards (`r make.ci.from.lrt.lsm(lsmctr_motconds[1,])`) being faster than Away
#' (`r make.ci.from.lrt.lsm(lsmctr_motconds[3,])`),
#' which in turn is faster than No Motion (`r make.ci.from.lrt.lsm(lsmctr_motconds[2,])`)
#' over all trial types.
#' 
#' The type of containment makes a difference as well, with the complex trials 
#' (`r make.ci.from.lrt.lsm(lsmctr_type[1,])`) being slower than the size trials
#' (`r make.ci.from.lrt.lsm(lsmctr_type[3,])`), the porous trials
#' (`r make.ci.from.lrt.lsm(lsmctr_type[2,])`), and the stopper trials
#' (`r make.ci.from.lrt.lsm(lsmctr_type[4,])`)
#' 
#' Finally, the level of containment made a difference in reaction times, with the
#' simplest / most contained trials being the fastest (`r make.ci.from.lrt.lsm(lsmctr_level[1,])`),
#' followed by the intermediate trials (`r make.ci.from.lrt.lsm(lsmctr_level[2,])`), followed by
#' the most complex / least contained (`r make.ci.from.lrt.lsm(lsmctr_level[3,])`)

#'
#' ## Post-hoc test for simulation across conditions
#' 
#' Given that the motion direction has a very strong effect but does not interact with anything
#' else, it seems as if simulation is used across all containment types and trials.
#' 
#' This post-hoc analysis is done to check for a "facilitation effect" of motion towards the goal: proportionally
#' how much faster do participants respond when they see motion towards the goal as compared to
#' either no motion or motion away? (The numbers below are calculated as $RT_{fwd}$ / $RT_{other}$)
#' 
#' If this number is less than 1, then the  time it takes to make predictions with forward motion is 
#' less than otherwise, which suggests people are using simulation to solve these trials.
#' 
#' As can be seen in the table below, *every* condition shows a numerical simulation facilitation
#' effect, and most of those cells also have 95% CIs that do not include 1 as well (Note: 
#' I need to double check the post-hoc corrections that the R package that calculated these is
#' using, so they might grow wider). This indicates that simulation is being used across the
#' board, no matter how simple the container is.

# Analysis for checking across *all* conditions - does forward speed facilitation compared to other?
lsmctr_all_fvo = lsmeans(mod_contain_forcontrast, 'AltMD', by = c('ContainmentLevel','ContainmentType'))
ctr_all_fvo = contrast(lsmctr_all_fvo, method='trt.vs.ctrl')
df_all_fvo = data.frame(confint(ctr_all_fvo))

df_print_fvo = df_all_fvo %>%
  mutate(words = paste(signif(1/exp(estimate),3), " [", signif(1/exp(upper.CL),3), ", ", signif(1/exp(lower.CL),3), "]",sep="")) %>%
  select(ContainmentLevel, ContainmentType, words) %>%
  spread(ContainmentLevel, words)
rownames(df_print_fvo) = df_print_fvo$ContainmentType
df_print_fvo = df_print_fvo %>% select(-ContainmentType)
df_print_fvo = df_print_fvo[c(3,2,4,1),]
rownames(df_print_fvo) = c("Size","Porousness","Stoppers","Complexity")
colnames(df_print_fvo) = c("A","B","C")

kable(df_print_fvo)
#xtable(df_print_fvo)

# Binomial tests of RT across matched trials
containdat_lrt_wide = containdat %>% group_by(Trial, MotionDirection) %>% summarize(LRT = mean(LogRT)) %>%
  spread(MotionDirection, LRT)
test_fvr_rt = with(containdat_lrt_wide, binom.test(sum(Rev > Fwd), length(Fwd)))
test_fvn_rt = with(containdat_lrt_wide, binom.test(sum(None > Fwd), length(Fwd)))
test_rvn_rt = with(containdat_lrt_wide, binom.test(sum(None > Rev), length(Fwd)))

#' Is this because of a small set of trials? No! Towards trials are mostly faster than away (`r print.binom.test(test_fvr_rt)`), mostly 
#' faster than no motion (`r print.binom.test(test_fvn_rt)`), though away trials are often faster than no motion (`r print.binom.test(test_rvn_rt)`).

#' ## Accuracy on contained trials
#' 
#' People did not perform perfectly even on the fully contained trials. This varied across trial types and 
#' motion directions. This isn't a point that we necessarily need to put weight on in the paper, but should 
#' report it
plot_contain_acc_all

#' Model testing suggests that 
#' the same things that affect reaction time also seem to affect accuracy:
anova(mod_acc_contain, test='Chisq')

#' Now, people are clearly not getting *every* contained trial correct, which in some cases can probably be considered misclicks or other errors in 
#' judgment (except possibly in the Porousness and Stopperage trials). However, these trials are much easier 
#' than non-contained trials (average accuracy for contained = `r acc_tab_disp$Accuracy[1]` vs non-contained = 
#' `r acc_tab_disp$Accuracy[2]`). And analyzing RTs for containment trials only in the cases where
#' participants indicated the correct goal does not lead to qualitatively different results.


#' Another explanation: people spend more time deliberating on the no motion and reverse trials 
kable(containdat %>% group_by(MotionDirection) %>% summarize(Acc=mean(WasCorrect)))

kable(acc_bymot)
print(contr_acc_bymot)

#' ## Is there learning?
#' 
#' Not statistically. People are `r (learn_amt-1)` proportionally slower each additional trial (95% CI: [`r learn_ci[1]-1`, `r learn_ci[2]-1`]).
print(anova(mod_learning))

#+ Experiment 1: Simulation: Versus ground truth ----------------------------------

# *********************
# Make simple plots
# *********************

aggcont_trial = gooddat %>% 
  group_by(Trial,Class,ContainmentType,ContainmentLevel,MotionDirection) %>% summarize(LRT = mean(LogRT)) %>%
  merge(trlen_dat %>% mutate(MotionDirection = Direction) %>% select(Trial,MotionDirection,Time,Bounces)) %>% mutate(RT = exp(LRT))
aggcont_trial$CondType = factor(with(aggcont_trial, ifelse(Class == 'regular','Filler',as.character(MotionDirection))))
aggcont_trial$Uncont = with(aggcont_trial, Class=='regular' | (ContainmentType == 'porous' & ContainmentLevel == 'c') |
                              (ContainmentType == 'stopper' & ContainmentLevel %in% c('b','c')))
aggcont_trial$CondType2 = factor(with(aggcont_trial, ifelse(Uncont, 'Uncontained',
                                                            ifelse(MotionDirection=='Fwd','Towards','Away'))),
                                 levels = c('Uncontained','Towards','Away'))

agct2 = aggcont_trial %>% subset(Class == 'regular' | !((ContainmentType == 'porous' & ContainmentLevel == 'c') |
                                                          (ContainmentType == 'stopper' & ContainmentLevel %in% c('b','c'))))

levels(aggcont_trial$CondType) = c('Filler','Towards','Away')
cor_plt = ggplot(aggcont_trial %>% mutate(Type = CondType), 
                 aes(x=Time, y=RT*1000, color=Type, shape=Type)) + geom_point(alpha = .8) + theme_bw() +
  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')

cor_plt2 = ggplot(aggcont_trial %>% mutate(Type = CondType2), 
                  aes(x=Time, y=RT*1000, color=Type, shape=Type)) + geom_point(alpha = .8) + theme_bw() +
  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')

cor_plt3 = ggplot(aggcont_trial %>% subset(!Uncont) %>% mutate(Type = CondType2), 
                  aes(x=Time, y=RT*1000, color=Type, shape=Type)) + geom_point(alpha = .8) + theme_bw() +
  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')

cor_plt4 = ggplot(agct2 %>% mutate(Type = CondType),
                  aes(x=Time, y=RT*1000, color=Type, shape=Type)) + geom_point(alpha = .8) + theme_bw() +
  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')

agt2 = aggcont_trial %>% mutate(ThisType = ifelse(Class=='regular','Non-Topo',ifelse(Uncont,'Topo-Uncontained',ifelse(MotionDirection=='Fwd','Topo-Towards','Topo-Away'))))
agt2$ThisType = factor(agt2$ThisType, levels = c('Non-Topo','Topo-Towards','Topo-Away','Topo-Uncontained'))
#ggplot(agt2, aes(x=Time, y=RT*1000, color=ThisType)) + geom_point(alpha = .8) + theme_bw() +
#  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')
#ggplot(agt2 %>% subset(ThisType != 'Topo-Uncontained'), aes(x=Time, y=RT*1000, color=ThisType)) + geom_point(alpha = .8) + theme_bw() +
#  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')

#anova(lm(RT ~ Time + Time:ThisType, data=agt2))

# *********************
# Make connected plots
# *********************

time_lm = lm(RT ~ Time + Time:CondType, data=aggcont_trial)
time_lm_base = lm(RT ~ Time, data=aggcont_trial)
time_lm_bounces = lm(RT ~ (Time + Bounces)*CondType, data=aggcont_trial)
#with(aggcont_trial, cor(Time, RT))

time_lm2 = lm(RT ~ Time + Time:CondType, data=subset(aggcont_trial, !Uncont))
time_lm3 = lm(RT ~ Time + Time:Uncont, data=aggcont_trial)

aggcont_trial_long = aggcont_trial %>% select(Trial, CondType, RT) %>% 
  spread(CondType, RT) %>% mutate(RT_Fwd = Towards, RT_Rev = Away, RT_Fill = Filler) %>% select(-Towards, -Away, -Filler) %>%
  merge(aggcont_trial %>% select(Trial, CondType, Time) %>%
          spread(CondType, Time) %>% mutate(Time_Fwd = Towards, Time_Rev = Away, Time_Fill = Filler) %>% select(-Towards, -Away, -Filler))
plot_cor_connect = ggplot(aggcont_trial_long) + 
  geom_point(aes(x=Time_Fill, y=RT_Fill*1000), color='darkgrey',shape=19, alpha=.8) + 
  geom_segment(aes(x=Time_Fwd,y=RT_Fwd*1000,xend=Time_Rev,yend=RT_Rev*1000, alpha=.8), linetype = 'dashed') + 
  geom_point(aes(x=Time_Fwd,y=RT_Fwd*1000), color='red', shape=19, alpha=.8) + 
  geom_point(aes(x=Time_Rev, y=RT_Rev*1000), color='blue',shape = 19, alpha=.8) + 
  xlab("Travel Time (s)") + ylab("Reaction Time (ms)") + theme_bw() + theme(legend.position='none')

col_df = data.frame(d = c(1,2,3), e = c(2,3,4))
col_df$col = factor(c('Towards','Away','Non-Topological'), levels = c('Towards','Away','Non-Topological'))
plot_cor_connect_legend = ggplot(col_df,
                                 aes(x=d,y=e,color=col)) + geom_point(alpha = .8) + theme_bw() +
  scale_color_manual(name = "Trial Type", values = c('Towards' = "red",'Away' = "blue",'Non-Topological' = "darkgrey"))


# *********************
# Models of RT vs travel time
# *********************

# Looking only at the topological trials
time_cor_cont = with(subset(aggcont_trial, CondType != "Filler"), cor(Time, RT))
time_lm_cont = lm(RT ~ Time + Time:CondType, data=subset(aggcont_trial, CondType != "Filler"))
time_lm_cont_base = lm(RT ~ Time, data=subset(aggcont_trial, CondType != "Filler"))
time_test_cont = anova(time_lm_cont_base, time_lm_cont)

# Excluding the non-contained topological trials
lme_cor_cont = with(subset(aggcont_trial, !Uncont), cor(Time,RT))
lme_lm_cont_fconly = lm(RT ~ Time + Time:CondType, data=subset(aggcont_trial, !Uncont))
lme_lm_cont_fconly_base = lm(RT ~ Time, data=subset(aggcont_trial, !Uncont))
lme_test_cont = anova(lme_lm_cont_fconly_base, lme_lm_cont_fconly)

# Including all trials with motion
allmot_cor_cont = with(aggcont_trial, cor(Time,RT))
allmot_lm_cont = lm(RT ~ Time + Time:CondType, data=aggcont_trial)
allmot_lm_cont_base = lm(RT ~ Time, data=aggcont_trial)
allmot_test_cont = anova(allmot_lm_cont_base, allmot_lm_cont)

#+ Experiment 1: Simulation: Versus model ------------------------------

# *****************
# Load in the model and check the best fitting time thresholds
# *****************

# Aggrgate by trial
trialdat = gooddat %>% mutate(Direction=MotionDirection) %>% group_by(Trial, Direction, HasMotion) %>%
  summarize(N = length(WID), EmpAcc = mean(WasCorrect), EmpLogRT = mean(LogRT), EmpLogRTSD = sd(LogRT)) %>% 
  mutate(EmpRT = exp(EmpLogRT))
levels(trialdat$Direction) = c('forward', 'none', 'reverse')

# Function for fitting specific RT data
fit_rt = function(fit_data) {
  fitlm = lm(MODEL_FORMULA, data=fit_data)
  ret = list(llh = logLik(fitlm),
             r = cor(fit_data$EmpRT, predict(fitlm)),
             coefs = coef(fitlm),
             model = fitlm)
  return(ret)
}

# Function for analyzing the best fitting time cutoff 
analyze_timeup = function(timeup_val, fit_on_regular = F, fit_on_forward = F) {
  # Load the data
  sim_dat = read.csv(paste(MODEL_FOLDER, "/sim_data_full_", timeup_val, ".0.csv", sep=""))
  thresh_dat = read.csv(paste(MODEL_FOLDER, "/model_pred_full_", timeup_val, ".0.csv", sep=""))  
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
  fits = lapply(MODEL_TIMEUP_CHOICES, function(t) analyze_timeup(t, fit_on_regular = fit_on_regular, fit_on_forward = fit_on_forward))
  fits_llh = sapply(fits, function(x) x$fitllh)
  names(fits_llh) = MODEL_TIMEUP_CHOICES
  best_tup_idx = which(fits_llh == max(fits_llh))
  best_tup = MODEL_TIMEUP_CHOICES[best_tup_idx]
  best_fit = fits[[best_tup_idx]]
  best_fit$timeup = best_tup
  best_fit$llh_grid = fits_llh
  return(best_fit)
}

# Look across all models
analyzed = analyze_model(MODEL_FIT_ON_REGULAR_ONLY, MODEL_FIT_ON_FORWARD_ONLY)

# Pull out the best fitting model
model_data = analyzed$data
model_timeup = analyzed$timeup
model_threshold = analyzed$threshold
model_corlist = analyzed$corbycond
rt_model = analyzed$model

# Transform the data
model_corlist = model_corlist %>%
  merge(model_data %>% 
          merge(trlen_dat %>% mutate(ActualTravelTime = Time, Direction = ifelse(Direction=='Fwd','forward',ifelse(Direction=='Rev','reverse','none'))) %>% 
                  select(Trial, Direction, ActualTravelTime), all=T) %>%
          group_by(Direction, IsContained) %>%
          summarize(rByTime = cor(AvgTime, EmpRT), rByBounce = cor(AvgBounces, EmpRT), rBySamp = cor(ExpectedNumSamples, EmpRT),
                    rByActTime = cor(ActualTravelTime,EmpRT), rSimTimeVsActTime = cor(ActualTravelTime, AvgTime)))

model_data = model_data %>% mutate(EmpRT_Lwr = exp(EmpLogRT - 2*EmpLogRTSD/sqrt(N)), EmpRT_Upr = exp(EmpLogRT + 2*EmpLogRTSD/sqrt(N)))

model_data_formerge = model_data %>% mutate(Class = IsContained, MotionDirection = ifelse(Direction=='forward','Fwd',ifelse(Direction=='reverse','Rev','None')), ModelRT = ModelRT*1000) %>%
  select(Trial, Class, MotionDirection, ModelRT)

model_rt_cor = with(model_data, cor(ModelRT, EmpRT))
model_rt_cor_regular = with(model_data %>% filter(IsContained != "contained"), cor(ModelRT, EmpRT))
model_rt_cor_topo = with(model_data %>% filter(IsContained == "contained"), cor(ModelRT, EmpRT))
model_acc_cor = with(model_data, cor(EmpAcc, ExpectedAccuracy))

# ***************
# Make model plots
# ***************

# Need to make this look nicer...
plot_modrt_vs_emprt = ggplot(model_data, aes(x=ModelRT, y=EmpRT, ymin = EmpRT_Lwr, ymax = EmpRT_Upr, shape = Direction, color = IsContained)) +
  geom_abline(intercept=0, slope=1, linetype = 'dashed') + 
  #geom_linerange() + 
  geom_point(alpha = .7) + 
  theme_bw()

plot_modacc_vs_empacc = ggplot(model_data, aes(x=ExpectedAccuracy, y=EmpAcc, ymin = EmpRT_Lwr, ymax = EmpRT_Upr, shape = Direction, color = IsContained)) +
  geom_abline(intercept=0, slope=1, linetype = 'dashed') + 
  #geom_linerange() + 
  geom_point(alpha = .7) + 
  theme_bw() + xlim(0,1) + ylim(0,1)

# Plot outcomes vs. model expectations
agg_model = model_data %>% filter(IsContained == 'contained') %>% 
  merge(gooddat %>% mutate(Direction = ifelse(MotionDirection=='Fwd','forward',ifelse(MotionDirection=='Rev','reverse','none'))) %>% select(Trial,Direction,ContainmentType,ContainmentLevel)) %>%
  group_by(ContainmentType, ContainmentLevel, Direction) %>% summarize(AvgModRT = mean(ModelRT))
levels(agg_model$ContainmentLevel) = c("A","B","C")
levels(agg_model$ContainmentType) = c("Complexity","Porousness","Size","Stopper")
agg_model$ContainmentType = relevel(agg_model$ContainmentType,"Stopper")
agg_model$ContainmentType = relevel(agg_model$ContainmentType,"Porousness")
agg_model$ContainmentType = relevel(agg_model$ContainmentType,"Size")
agg_model = agg_model %>% mutate(MotionDirection = factor(ifelse(Direction=='forward','Towards',ifelse(Direction=='reverse','Away','No motion')))) %>% select(-Direction)
agg_model = merge(agg_contain_all,agg_model)

plot_contain_withmod = ggplot(agg_model, aes(x=MotionDirection, y=exp(MeanLogRT), ymax=exp(LogRT_975), ymin = exp(LogRT_025))) +
  geom_line(aes(y=AvgModRT,group=ContainmentType), color='red') +
  geom_point() + geom_linerange() + 
  ylim(0,NA) + facet_grid(ContainmentType ~ ContainmentLevel) +
  theme_bw() + xlab('Motion Condition') + ylab('Reaction Time (s)')


#+ Experiment 1: Simulation: Writeout ----------------------------------

#' # Experiment 1 - Simulation
#' 
#' If these judgments are based on simulations, then RTs should be proportional to the actual trial length for moving trials. There is a correlation between 
#' travel time and RT for the contained trials (r = `r time_cor_cont`, `r print.slope.test(time_lm_cont_base,"Time")`). There was not statistical evidence of a difference 
#' between contained and uncontained trials: `r print.model.anova.test(time_test_cont)`.
#' 
#' If non-topological trials are included, there is little change in the slope (r = `r allmot_cor_cont`, `r print.slope.test(allmot_lm_cont_base, "Time")`), and still 
#' no evidence of difference: `r print.model.anova.test(allmot_test_cont)`. If only the fully contained trials are used, there is still little change in the slope 
#' (r = `r lme_cor_cont`, `r print.slope.test(lme_lm_cont_fconly_base, "Time")`), and still 
#' no evidence of difference: `r print.model.anova.test(lme_test_cont)`.

print(cor_plt)

#' ## Simulation modeling
#' 
#' We can use the model of Smith & Vul (2013) and Hamrick et al (2015) to determine how fast people should respond in topological trials according to a simulation model. 
#' Simulations were pulled from the S&V model with default parameters. We adapt the Hamrick et al model so that the time per simulation sample is a function of not 
#' just the number of bounces, but also the distance the ball travels in the simulation, and assume that no motion trials take slightly longer to set up motion. Thus the 
#' model formula has RT vary as a function of: `r as.character(MODEL_FORMULA)[3]`.
#' 
#' The model was fit on the non-topological trials only. Thus any explanations of RT in the topological trials are effectively zero-parameter fits.
#' 
#' Overall the model fits well (r = `r model_rt_cor`), though does slightly better on the non-topological trials on which it was fit (r = `r model_rt_cor_regular`) than 
#' on the topological trials (r = `r model_rt_cor_topo`).
#' 
print(plot_modrt_vs_emprt)

#' Aggregating by containment type, we find that this model explains the patterns in RT across topological trials fairly well (the red line is the model prediction and 
#' the black points are empirical RTs with 95% CIs)
print(plot_contain_withmod)

#' The model also does a good job of explaining accuracy across trials (r = `r model_acc_cor`):
print(plot_modacc_vs_empacc)

#' For more fine-grained correlations between model RT and empirical RT, see the table below:
kable(model_corlist %>% select(Direction,IsContained,r,rByActTime))


#+ Experiment 2: Loading ----------------------------------------
rawdat_5050 = read.csv('../ContainmentData/exp2_data.csv')
incompletes_5050 = names(table(rawdat_5050$WID)[which(table(rawdat_5050$WID) != 48)])
gooddat_5050 = subset(rawdat_5050, !(WID %in% incompletes_5050) & (WasBad=="False") & (RawResponse != 'NA') & RT > TOOFAST)
gooddat_5050$Response = factor(as.character(gooddat_5050$Response))
if (ADD_RT) gooddat_5050$RT = gooddat_5050$RT + .5
gooddat_5050$LogRT = log(gooddat_5050$RT)
gooddat_5050$WasCorrect = with(gooddat_5050, Response == Goal)

pct_bad_5050 = with(subset(rawdat_5050, !(WID %in% incompletes_5050)), mean(WasBad=='True'))
pct_na_5050 = with(subset(rawdat_5050, !(WID %in% incompletes_5050) & (WasBad=="False")), mean(is.na(RawResponse)))
pct_toofast_5050 = with(subset(rawdat_5050, !(WID %in% incompletes_5050) & (WasBad=="False") & (RawResponse != 'NA')), mean(RT < TOOFAST))
n_subjects_5050 = length(unique(gooddat_5050$WID))

#+ Experiment 2: Analysis ----------------------------------------

# Aggregate like exp 1

containdat_5050 = subset(gooddat_5050, Class=='contained')
containdat_5050$AltMD = factor(with(containdat_5050, ifelse(MotionDirection == 'Fwd','Fwd','Other')))

if (USE_GOOD_ONLY) {containdat_5050 = subset(containdat_5050, WasCorrect)}

agg_contain_all_5050 = containdat_5050 %>% group_by(ContainmentType, ContainmentLevel, MotionDirection) %>%
  summarize(MeanLogRT = mean(LogRT), GoodLRT = mean(LogRT[Response=='G']), BadLRT = mean(LogRT[Response!='G']),
            Acc = mean(Response=='G'), N = length(Response))
agg_contain_all_5050$LogRT_975 = agg_contain_all_5050$LogRT_025 = NA
for (rn in 1:nrow(agg_contain_all_5050)) {
  sdat = subset(containdat_5050, ContainmentType==agg_contain_all_5050$ContainmentType[rn] &
                  MotionDirection==agg_contain_all_5050$MotionDirection[rn])
  bssamps = bootstrap_overall_geort(sdat, N_BOOT_SAMPS)
  bsquantile = quantile(bssamps, c(.025, .975))
  agg_contain_all_5050$LogRT_025[rn] = bsquantile[1]
  agg_contain_all_5050$LogRT_975[rn] = bsquantile[2]
}

levels(agg_contain_all_5050$MotionDirection) = c('Towards', 'No motion','Away')
levels(agg_contain_all_5050$ContainmentLevel) = c('A','B','C')
levels(agg_contain_all_5050$ContainmentType) = c('Complexity','Porousness','Size','Stopper')
agg_contain_all_5050$ContainmentType = relevel(agg_contain_all_5050$ContainmentType, "Stopper")
agg_contain_all_5050$ContainmentType = relevel(agg_contain_all_5050$ContainmentType, "Porousness")
agg_contain_all_5050$ContainmentType = relevel(agg_contain_all_5050$ContainmentType, "Size")

# ***********************
# Plots of 50/50 exp
# ***********************
plot_5050_contain_all = ggplot(agg_contain_all_5050, aes(x=MotionDirection, y=exp(MeanLogRT), ymax=exp(LogRT_975), ymin = exp(LogRT_025))) +
  geom_point() + geom_linerange() + ylim(0,NA) + facet_grid(ContainmentType ~ .) +
  theme_bw() + xlab('Motion Condition') + ylab('Reaction Time (s)')



#+ Experiment 3: Reachability (loading)

rawdata_reach = read.csv('../ContainmentData/exp3_data.csv')
incompletes_reach = names(table(rawdata_reach$WID)[which(table(rawdata_reach$WID) != 24)])
gooddat_reach = subset(rawdata_reach, !(WID %in% incompletes_reach) & (WasBad=="False") & (Response != 'NA') & RT > TOOFAST)
if (ADD_RT) gooddat_reach$RT = gooddat_reach$RT + .5
gooddat_reach$LogRT = log(gooddat_reach$RT)
gooddat_reach$Response = factor(as.character(gooddat_reach$Response))
gooddat_reach$WasCorrect = with(gooddat_reach, Response == GoalReachable)
gooddat_reach$HasMotion = factor(with(gooddat_reach, ifelse(MotionDirection=='None','No','Yes')))

#gooddat_reach = gooddat_reach %>% filter(WasCorrect)

agg_contain_reach = gooddat_reach %>% group_by(ContainmentType, ContainmentLevel, MotionDirection, GoalReachable) %>%
  summarize(MeanLogRT = mean(LogRT), Acc = mean(WasCorrect), N = length(Response))
agg_contain_reach$LogRT_975 = agg_contain_reach$LogRT_025 = NA
for (rn in 1:nrow(agg_contain_reach)) {
  sdat = subset(gooddat_reach, ContainmentType==agg_contain_reach$ContainmentType[rn] &
                  MotionDirection==agg_contain_reach$MotionDirection[rn] & GoalReachable==agg_contain_reach$GoalReachable[rn])
  bssamps = bootstrap_overall_geort(sdat, N_BOOT_SAMPS)
  bsquantile = quantile(bssamps, c(.025, .975))
  agg_contain_reach$LogRT_025[rn] = bsquantile[1]
  agg_contain_reach$LogRT_975[rn] = bsquantile[2]
}

levels(agg_contain_reach$MotionDirection) = c('Towards', 'No motion','Away')
levels(agg_contain_reach$ContainmentLevel) = c('A','B','C')
levels(agg_contain_reach$ContainmentType) = c('Complexity','Porousness','Size','Stopper')
agg_contain_reach$ContainmentType = relevel(agg_contain_reach$ContainmentType, "Stopper")
agg_contain_reach$ContainmentType = relevel(agg_contain_reach$ContainmentType, "Porousness")
agg_contain_reach$ContainmentType = relevel(agg_contain_reach$ContainmentType, "Size")

agg_contain_reach_yes = agg_contain_reach %>% filter(GoalReachable == "True")
agg_contain_reach_no = agg_contain_reach %>% filter(GoalReachable == "False")

#' Temp - move me!
ggplot(agg_contain_reach, aes(x=MotionDirection,y=Acc,group=GoalReachable,fill=GoalReachable)) + 
  geom_bar(stat='identity',position='dodge') + facet_grid(. ~ ContainmentType)

mod_reach_lrt = lmer(data=gooddat_reach, LogRT ~ ContainmentType*GoalReachable*MotionDirection + 
                     (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
mod_reach_lrt_noreachtype = lmer(data=gooddat_reach, LogRT ~ ContainmentType*MotionDirection + 
                                   (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
anova(mod_reach_lrt_noreachtype, mod_reach_lrt)

mod_reach_lrt_sub_reach = lmer(data = gooddat_reach %>% filter(GoalReachable == "True"),
                               LogRT ~ ContainmentType*MotionDirection + 
                                 (1|WID) + (1|Trial) + (1|Trial:MotionDirection))
mod_reach_lrt_sub_noreach = lmer(data = gooddat_reach %>% filter(GoalReachable == "False"),
                               LogRT ~ ContainmentType*MotionDirection + 
                                 (1|WID) + (1|Trial) + (1|Trial:MotionDirection))

lsm_reach_gr = lsmeans(mod_reach_lrt, "MotionDirection", at = list(GoalReachable='True'))
lsm_reach_ngr = lsmeans(mod_reach_lrt, "MotionDirection", at = list(GoalReachable='False'))
contrast(lsm_reach_gr, method='trt.vs.ctrl')
contrast(lsm_reach_ngr, method='trt.vs.ctrl')

gooddat_reach %>% group_by(GoalReachable, MotionDirection) %>% summarize(Acc = mean(WasCorrect), LRT = mean(LogRT)) %>% mutate(RT = exp(LRT) *1000)

trialdat_reach = gooddat_reach %>% group_by(Trial, ContainmentType, GoalReachable, MotionDirection) %>% summarize(LRT = mean(LogRT), Acc=mean(WasCorrect))
trialdat_reach_spread = trialdat_reach %>% select(-Acc) %>% spread(GoalReachable, LRT)
names(trialdat_reach_spread)[4:5] = c("Unreachable", "Reachable")
trialdat_reach_spread = trialdat_reach_spread %>% mutate(RT_Reach = exp(Reachable)*1000, RT_NoReach = exp(Unreachable)*1000)
ggplot(trialdat_reach_spread, aes(x=RT_NoReach, y=RT_Reach, color=MotionDirection, shape=ContainmentType)) + 
  geom_abline(intercept=0,slope=1) + geom_point() + theme_bw()
with(trialdat_reach_spread, cor(RT_Reach, RT_NoReach))

#+ Aggregation across Exp ------------------------

acrossexp_data_1v2 = gooddat %>% group_by(Trial, Class, ContainmentType, MotionDirection) %>%
  summarize(LogRT_E1 = mean(LogRT), Acc_E1 = mean(WasCorrect)) %>% mutate(RT_E1 = exp(LogRT_E1)*1000) %>%
  merge(gooddat_5050 %>% group_by(Trial, Class, ContainmentType, MotionDirection) %>%
          summarize(LogRT_E2 = mean(LogRT), Acc_E2 = mean(WasCorrect)) %>% mutate(RT_E2 = exp(LogRT_E2)*1000)) %>%
  merge(model_data_formerge)

acrossexp_data_contained = gooddat %>% filter(Class == 'contained') %>% group_by(Trial, ContainmentType, MotionDirection) %>%
  summarize(LogRT_E1 = mean(LogRT), Acc_E1 = mean(WasCorrect)) %>% mutate(RT_E1 = exp(LogRT_E1)*1000) %>%
  merge(gooddat_5050 %>% filter(Class == 'contained') %>% group_by(Trial, ContainmentType, MotionDirection) %>%
          summarize(LogRT_E2 = mean(LogRT), Acc_E2 = mean(WasCorrect)) %>% mutate(RT_E2 = exp(LogRT_E2)*1000)) %>%
  merge(gooddat_reach %>% filter(GoalReachable == 'True') %>% group_by(Trial, ContainmentType, MotionDirection) %>%
          summarize(LogRT_E3_Reach = mean(LogRT), Acc_E3_Reach = mean(WasCorrect))) %>% mutate(RT_E3_Reach = exp(LogRT_E3_Reach)*1000) %>%
  merge(gooddat_reach %>% filter(GoalReachable == 'False') %>% group_by(Trial, ContainmentType, MotionDirection) %>%
          summarize(LogRT_E3_NoReach = mean(LogRT), Acc_E3_NoReach = mean(WasCorrect))) %>% mutate(RT_E3_NoReach = exp(LogRT_E3_NoReach)*1000) %>%
  merge(model_data_formerge)

accexp_rt_cors = acrossexp_data_contained %>% select(RT_E1, RT_E2, RT_E3_Reach, RT_E3_NoReach, ModelRT) %>% cor
accexp_rt_cors_motion = acrossexp_data_contained %>% filter(MotionDirection != "None") %>% select(RT_E1, RT_E2, RT_E3_Reach, RT_E3_NoReach, ModelRT) %>% cor
accexp_rt_cors_fwd = acrossexp_data_contained %>% filter(MotionDirection =='Fwd') %>% select(RT_E1, RT_E2, RT_E3_Reach, RT_E3_NoReach, ModelRT) %>% cor
accexp_rt_cors_rev = acrossexp_data_contained %>% filter(MotionDirection =='Rev') %>% select(RT_E1, RT_E2, RT_E3_Reach, RT_E3_NoReach, ModelRT) %>% cor
acrossexp_data_contained %>% select(RT_E1, RT_E2, RT_E3_Reach, RT_E3_NoReach, ModelRT) %>% plot

agg_contain_acrossexp = agg_model %>% 
  merge(agg_contain_all_5050 %>% mutate(LogRT_5050 = MeanLogRT, LogRT_025_5050 = LogRT_025, LogRT_975_5050 = LogRT_975) %>%
          select(ContainmentType, ContainmentLevel, MotionDirection, LogRT_5050, LogRT_025_5050, LogRT_975_5050)) %>%
  merge(agg_contain_reach_yes %>% mutate(LogRT_Reach = MeanLogRT, LogRT_025_Reach = LogRT_025, LogRT_975_Reach = LogRT_975) %>%
          select(ContainmentType, ContainmentLevel, MotionDirection, LogRT_Reach, LogRT_025_Reach, LogRT_975_Reach)) %>%
  merge(agg_contain_reach_no %>% mutate(LogRT_NoReach = MeanLogRT, LogRT_025_NoReach = LogRT_025, LogRT_975_NoReach = LogRT_975) %>%
          select(ContainmentType, ContainmentLevel, MotionDirection, LogRT_NoReach, LogRT_025_NoReach, LogRT_975_NoReach))
agg_contain_acrossexp = agg_contain_acrossexp %>% mutate(RT = exp(MeanLogRT)*1000, RT_025 = exp(LogRT_025)*1000, RT_975 = exp(LogRT_975)*1000,
                                 RT_5050 = exp(LogRT_5050)*1000, RT_025_5050 = exp(LogRT_025_5050)*1000, RT_975_5050 = exp(LogRT_975_5050)*1000,
                                 RT_Reach = exp(LogRT_Reach)*1000, RT_025_Reach = exp(LogRT_025_Reach)*1000, RT_975_Reach = exp(LogRT_975_Reach)*1000,
                                 RT_NoReach = exp(LogRT_NoReach)*1000, RT_025_NoReach = exp(LogRT_025_NoReach)*1000, RT_975_NoReach = exp(LogRT_975_NoReach)*1000)

APOFF = .12
plot_across_rts = ggplot(agg_contain_acrossexp, aes(x=MotionDirection)) + 
  geom_line(aes(y=AvgModRT*1000, group=ContainmentType), linetype = 'dashed') + 
  geom_linerange(aes(ymin=RT_025,ymax=RT_975, x=as.numeric(MotionDirection)-APOFF*1.5, color='Exp 1')) + geom_point(aes(y=RT, x=as.numeric(MotionDirection)-APOFF*1.5, color='Exp 1')) +
  geom_linerange(aes(ymin=RT_025_5050,ymax=RT_975_5050, x=as.numeric(MotionDirection)-APOFF*.5, color='Exp 2')) + geom_point(aes(y=RT_5050, x=as.numeric(MotionDirection)-APOFF*.5, color='Exp 2')) +
  geom_linerange(aes(ymin=RT_025_Reach,ymax=RT_975_Reach, x=as.numeric(MotionDirection)+APOFF*.5, color='Exp 3 (reachable)')) + geom_point(aes(y=RT_Reach, x = as.numeric(MotionDirection)+APOFF*.5, color = "Exp 3 (reachable)")) +
  geom_linerange(aes(ymin=RT_025_NoReach,ymax=RT_975_NoReach, x=as.numeric(MotionDirection)+APOFF*1.5, color='Exp 3 (unreachable)')) + geom_point(aes(y=RT_NoReach, x = as.numeric(MotionDirection)+APOFF*1.5, color= "Exp 3 (unreachable)")) +
  facet_grid(. ~ ContainmentType) + theme_bw() + ylim(0,1000) + ylab("Reaction Time (ms)") +
  scale_color_manual(values = c("Exp 1" = "blue", "Exp 2" = "red", "Exp 3 (reachable)" = "green", "Exp 3 (unreachable)" = "purple"), 
                     breaks= c("Exp 1", "Exp 2", "Exp 3 (reachable)", "Exp 3 (unreachable)")) +
  theme(legend.title = element_blank())

plot_across_rts

plot_e1v2_rt = ggplot(acrossexp_data_1v2, aes(x=RT_E1,y=RT_E2,color=Class,shape=MotionDirection)) + 
  geom_abline(intercept=0,slope=1,linetype='dashed') + geom_point() + theme_bw()
plot_e1v2_rt_contonly = ggplot(acrossexp_data_1v2 %>% filter(Class=='contained'), aes(x=RT_E1,y=RT_E2,color=ContainmentType,shape=MotionDirection)) + 
  geom_abline(intercept=0,slope=1,linetype='dashed') + geom_point() + theme_bw()

# Testing - is there a difference between exp 1 & 2 RTs by topology?
e1v2_gross_rt_compare = acrossexp_data_1v2 %>% group_by(Class, MotionDirection) %>% summarize(E1 = mean(RT_E1), E2 = mean(RT_E2), Mod=mean(ModelRT))

#' # Combining experiments

#' So far, this is just combining Exp 1 & Exp 2, demonstrating that 
plot_across_rts

#+ Filler trials -----------------------------------------------------



#' # Non-contained trials
#' 
#' To double check, we test whether there is any differentiation in reaction time for the non-contained trials between 
#' when there is motion and when there is not. If motion doesn't change reaction time *even when we know people 
#' are not using containment reasoning* then we won't be able to tell anything about the contained 
#' trials when simulation is ambiguous
#' 
#' 
#' 
#' Plots of geometric mean of RT and accuracy across trials (probably not to be used):
#' 
print(plot_reg_rt)
print(plot_reg_acc)


#+ Checking correlations with path length --------------------







time_lm_fill = lm(RT ~ Time, data=subset(aggcont_trial, CondType == "Filler"))
time_lm_fwd = lm(RT ~ Time, data=subset(aggcont_trial, CondType == "Towards"))
time_lm_rev = lm(RT ~ Time, data=subset(aggcont_trial, CondType == "Away"))

# STUFF TO USE



with(subset(aggcont_trial, CondType == "Filler"), cor(RT, Time))
with(subset(aggcont_trial, CondType == "Towards"), cor(RT, Time))
with(subset(aggcont_trial, CondType == "Away"), cor(RT, Time))
with(subset(aggcont_trial, CondType != "Filler"), cor(RT, Time))
with(subset(aggcont_trial, !Uncont), cor(RT,Time))

options(contrasts = c('contr.treatment','contr.poly'))
time_lm_trt = lm(RT ~ Time + Time:CondType, data=aggcont_trial)
aggcont_trial$CondType = relevel(aggcont_trial$CondType,'Towards')
time_lm_trt2 = lm(RT ~ Time + Time:CondType, data=aggcont_trial)
options(contrasts = c('contr.sum','contr.poly'))

#+ Check for left/right facilitation -----------------------
widlr = read.table('../psiturk-rg-cont/questiondata.csv', sep=',',
                   col.names = c("WID",'N',"RedOnLeft"))
trlr = read.csv('../ContainmentTrials/TrialPos.csv')

lrdat = gooddat %>% merge(widlr %>% select(-N)) %>% merge(trlr)
lrdat$SameSideGoal = with(lrdat, 
                          ifelse(WhichOnLeft == "None",
                          "Neither",
                          ifelse(((RedOnLeft=='True' & WhichOnLeft == 'R') | (RedOnLeft=='False' & WhichOnLeft=='G')),
                                 "Yes",
                                 "No")))
lrtab = with(lrdat, table(SameSideGoal, WasCorrect))

lrdat %>% group_by(SameSideGoal) %>% summarize(Acc = mean(WasCorrect), RT = exp(mean(LogRT)))

#+ Exports ------------------------------------------------

if (export) {
  # Figures of basic RTs
  ggsave('FigDataA.png',plot_contain_all_paper_a,width=4, height=11/4, units='in', dpi=300)
  ggsave('FigDataB.png',plot_contain_all_paper_b,width=4, height=11/4, units='in', dpi=300)
  ggsave('FigData_Full.png', plot_contain_all_poster_full, width=4, height= 5, units='in', dpi=300)
  
  # Figures of correlation between travel time and RT (basic)
  ggsave('FigCorPlt.png',cor_plt,width=4,height=3,units='in',dpi=300)
  ggsave('FigCorPlt2.png',cor_plt2,width=4,height=3,units='in',dpi=300)

  # Figures of correlation between travel time and RT (connected - in two parts)  
  ggsave("FigCorCon_Base.png",plot_cor_connect,width=4,height=4,units='in',dpi=300)
  ggsave("FigCorCon_Legend.png",plot_cor_connect_legend,width=5,height=4,units='in',dpi=300)
}
