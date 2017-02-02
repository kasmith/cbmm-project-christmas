
#' ---
#' title: Containment CogSci Analyses
#' author: Kevin A Smith
#' date: Jan 22, 2017
#' output:
#'    html_document:
#'      theme: default
#'      highlight: tango
#' ---

#+ General settings, echo = FALSE, results = 'hide', fig.width = 4, fig.height = 4 ------------------------------------------------------------------------------

knitr::opts_chunk$set(warning=F, message=F, cache = F, echo=F)
options(digits = 3)
kable = knitr::kable
export = F
FIGURE_DIR = "Figures/"
N_BOOT_SAMPS = 500 # Crank this up to ~1000 for the paper
USE_GOOD_ONLY = F
ADD_RT = F

#+ Initialization ----------------------------------------------------------

library(parallel)
library(lme4)
library(ggplot2)
library(tidyr)
library(dplyr)
library(xtable) # Not directly used but helpful for latex translating
library(lmerTest)
library(lsmeans)
options(contrasts = c('contr.sum','contr.poly'))

rawdat = read.csv('rawdata.csv')
incompletes = names(table(rawdat$WID)[which(table(rawdat$WID) != 120)])
gooddat = subset(rawdat, !(WID %in% incompletes) & (WasBad=="False") & (RawResponse != 'NA') & RT > .01)
if (ADD_RT) gooddat$RT = gooddat$RT + .5
gooddat$LogRT = log(gooddat$RT)
gooddat$WasCorrect = with(gooddat, Response == Goal)

pct_bad = with(subset(rawdat, !(WID %in% incompletes)), mean(WasBad=='True'))
pct_na = with(subset(rawdat, !(WID %in% incompletes) & (WasBad=="False")), mean(is.na(RawResponse)))
pct_toofast = with(subset(rawdat, !(WID %in% incompletes) & (WasBad=="False") & (RawResponse != 'NA')), mean(RT < .01))
n_subjects = length(unique(gooddat$WID))

print.t.test = function(test) {
  return(paste("t(",round(test$parameter,1),")=",round(test$statistic,2),", p=",signif(test$p.value,3),sep=""))
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

#+ Explanataion ---------------------------------------------

#' # Analysis logic
#' 
#' To test whether people are using simulation or containment processing, we measured reaction times across
#' the various types of containment (size, porousness, stopperage, and complexity), the levels of that dimension,
#' and the motion condition (Towards, No motion, or Away).
#' 
#' If people are relying on simulation for a given 
#' condition, then motion in the direction of the goal (Towards) should make simulation easier since 
#' those simulations should be shorter and involve fewer bounces than if the simulations are initialized 
#' in the other direction (Away), or not initialized so must travel in many different directions (No motion).
#' If reaction time is lower in the "Towards" motion condition as compared to the other two
#' conditions, this is used as an indication that people are in general using simulation for those
#' types of containment trials.
#' 
#' We varied four dimensions of containment at three levels each (refered to as A, B, and C, though 
#' what these dimension leters stand for differs by dimension):
#' 
#' ### Size
#' 
#' This dimension was used to test whether containment parsing works based on screen / DVA size, 
#' or whether it is based on the configuration of the scene. If people are trying to fill space around 
#' the ball at a constant rate then the time to parse containment should vary linearly with size. 
#' If, on the other hand, containment is based on more configural processing, or if flooding steps are 
#' relative to the local area, then we should see people be insensitive to this dimension.
#' 
#' These stimuli were created such that the relative configuration of objects doesn't change, but 
#' all of the walls and goals start from small (50% dimensions for category A), to medium (75% for category B),
#' to large (100% for category C).
#' 
#' If parsing works in screen / DVA space, then we should expect that reaction times should increase linearly
#' with size. But if we see that reaction times do not change from A to C, then we can conclude that either
#' people process containment by parsing the scene, or adaptively exploring the scene based on container size
#' 
#' ### Porousness
#' 
#' This dimension was used to test whether containment processing is broken by *any* gaps in a container,
#' or whether it is adaptive to the object that is being contained (e.g., the ball in this case).
#' 
#' These stimuli were created so that the geometry of the scene was the same, with the only difference ranging 
#' from the container being completely enclosed (level A), to having a gap or multiple gaps smaller than the ball
#' (level B), to having gaps larger than the ball (level C).
#' 
#' We would expect at a baseline a difference between how often people use simulation from level A to level C --
#' the containers are simple and unbroken in level A so there should be little difference between the RTs for
#' Towards motion and either No motion or Away motion, while the container does not actually contain the ball 
#' in level C and so we should see simulation causes Towards motion to produce faster responses.
#' 
#' The interesting comparison here is level B, where the wall has a small gap. If containment processing is 
#' broken by any gap, then we should see a response pattern similar to that of level C, where Towards motion 
#' is faster than other motion types. On the other hand, if people account for the size of the ball, then
#' we would expect that the small gaps should still be considered containing, and so reaction times should
#' not differ across the motion conditions.
#' 
#' ### Stopperage
#' 
#' This dimension was used to test whether containment processing uses information about motion or simply
#' computes reachability between two points.
#' 
#' The stimuli were all created so that in the A level the container is sealed by a goal. At the B level, the goal 
#' is moved away from the opening so that there is enough space for the ball to get through, but to do so 
#' would be physically implausible given the direction the ball must be going to get through that gap. At the C 
#' level, the goal is moved further away so that it is very possible for the ball to escape the container even 
#' using physical motion constraints
#' 
#' Similar to the porousness dimension, the interesting level is B. We expect no difference in RTs across 
#' motion conditions in level A because the ball is fully contained, whereas we expect simulation to be
#' facilitated in the Towards condition in level C because the configuration is no longer a container. 
#' However, in level B, if people take into account physically plausible motion when parsing containment,
#' we would expect that the scene is treated as contained and there is no difference in RTs across motion
#' conditions. Conversely, if containment processing disregards all motion information, we should see 
#' faster reaction times in the Towards condition
#' 
#' ### Complexity
#' 
#' This dimension was used to test how containment and simulation interact -- even in situations where 
#' the ball is fully contained will people use simulation if parsing the boundaries of the container is 
#' too difficult? Simulation can be accomplished by working with local obstacles, but parsing containment 
#' requires keeping track of the entire boundary, which can become difficult if it is made up of many 
#' different segments. Thus we want to test whether people switch to simulation when containment is difficult 
#' to see
#' 
#' The stimuli here were created such that in the simplest level (A) the scenes are made of very simple 
#' configurations (e.g. a box or a line separating two sides of the screen), but more internal and external 
#' structure is added in the (B) level, and more still in the (C) level. 
#' 
#' If complexity of the scene breaks containment processing, then participants should be 
#' equally fast to respond regardless of motion information in level A, but as the scene becomes more complex,
#' simulation should take over and reaction times should be sped in the Towards condition.

#+ Overall results -----------------------------------

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
ggsave('FigDataA.png',plot_contain_all_paper_a,width=4, height=11/4, units='in', dpi=300)
ggsave('FigDataB.png',plot_contain_all_paper_b,width=4, height=11/4, units='in', dpi=300)


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

#' # Results
#' 
#' All of these results are based on the data from `r n_subjects` participants.
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

# Binomial tests of RT across matched trials
containdat_lrt_wide = containdat %>% group_by(Trial, MotionDirection) %>% summarize(LRT = mean(LogRT)) %>%
  spread(MotionDirection, LRT)
with(containdat_lrt_wide, binom.test(sum(Rev > Fwd), length(Fwd)))
with(containdat_lrt_wide, binom.test(sum(None > Fwd), length(Fwd)))
with(containdat_lrt_wide, binom.test(sum(None > Rev), length(Fwd)))

#xtable(df_print_fvo)

#+ Model subsets ---------------------------------

#' ## Containment dimension analyses
#' 
#' Below are the pre-planned contrasts to check for the different sorts of containment processing.
#' This is not as important in light of the simulation findings, and might not be reported in the
#' paper
#'
#' ### Size

# Does the average processing time change from A to C?
lsmctr_atoc_insize = lsmeans(mod_contain_forcontrast, "ContainmentLevel",
                             at = list(ContainmentType='size', ContainmentLevel = c('a','c')))
ctr_atoc_insize = contrast(lsmctr_atoc_insize, method='trt.vs.ctrl')
ci_atoc_insize = confint(ctr_atoc_insize)
ci_atoc_insize_raw = confint(lsmctr_atoc_insize)

#' The average time to respond to the smallest trials is `r exp(ci_atoc_insize_raw$lsmean[1])`s (95% CI:
#' [`r exp(ci_atoc_insize_raw$lower.CL[1])`, `r exp(ci_atoc_insize_raw$upper.CL[1])`]), versus 
#' `r exp(ci_atoc_insize_raw$lsmean[2])`s in the largest trials (95% CI:
#' [`r exp(ci_atoc_insize_raw$lower.CL[2])`, `r exp(ci_atoc_insize_raw$upper.CL[2])`]). Linear contrasts 
#' suggest that the reaction time in the largest trials should only take `r exp(ci_atoc_insize$estimate)` times
#' as long as the smallest trials (95% CI = [`r exp(ci_atoc_insize$lower.CL)`, `r exp(ci_atoc_insize$upper.CL)`]).
#' 
#' 

#' ### Porousness

# Is there evidence of difference between Towards vs Other across the levels
lsmctr_all_inporous_bylev = lsmeans(mod_contain_forcontrast, "AltMD", by="ContainmentLevel",
                              at = list(ContainmentType="porous"))
ctr_bylev_inporous = contrast(lsmctr_all_inporous_bylev, method='trt.vs.ctrl')
ctr_within_inporous = contrast(lsmctr_all_inporous_bylev, interaction = c('pairwise','pairwise'))
ci_bylev_inporous = confint(ctr_bylev_inporous)
ci_within_inporous = confint(ctr_within_inporous)
#' The relative slowdown going from Towards motion to the average of No motion and Away along each 
#' level of porousness are:
#' 
#' * A (fully contained): `r exp(ci_bylev_inporous$estimate[1])` times slower (95% CI = [`r exp(ci_bylev_inporous$lower.CL[1])`, `r exp(ci_bylev_inporous$upper.CL[1])`])
#' * B (partially open): `r exp(ci_bylev_inporous$estimate[2])` times slower (95% CI = [`r exp(ci_bylev_inporous$lower.CL[2])`, `r exp(ci_bylev_inporous$upper.CL[2])`])
#' * C (fully open): `r exp(ci_bylev_inporous$estimate[3])` times slower (95% CI = [`r exp(ci_bylev_inporous$lower.CL[3])`, `r exp(ci_bylev_inporous$upper.CL[3])`])
#' 
#' Pairwise tests for differences between these conditions are not statistically significant:
ctr_within_inporous


#' ### Stopperage

# Is there evidence of difference between Towards vs Other across the levels
lsmctr_all_instop_bylev = lsmeans(mod_contain_forcontrast, "AltMD", by="ContainmentLevel",
                                    at = list(ContainmentType="stopper"))
ctr_bylev_instop = contrast(lsmctr_all_instop_bylev, method='trt.vs.ctrl')
ctr_within_instop = contrast(lsmctr_all_instop_bylev, interaction = c('pairwise','pairwise'))
ci_bylev_instop = confint(ctr_bylev_instop)
ci_within_instop = confint(ctr_within_instop)

#' The relative slowdown going from Towards motion to the average of No motion and Away along each 
#' level of stopperage are:
#' 
#' * A (fully contained): `r exp(ci_bylev_instop$estimate[1])` times slower (95% CI = [`r exp(ci_bylev_instop$lower.CL[1])`, `r exp(ci_bylev_instop$upper.CL[1])`])
#' * B (reachable but unlikely): `r exp(ci_bylev_instop$estimate[2])` times slower (95% CI = [`r exp(ci_bylev_instop$lower.CL[2])`, `r exp(ci_bylev_instop$upper.CL[2])`])
#' * C (fully open): `r exp(ci_bylev_instop$estimate[3])` times slower (95% CI = [`r exp(ci_bylev_instop$lower.CL[3])`, `r exp(ci_bylev_instop$upper.CL[3])`])
#' 
#' Pairwise tests for differences between these conditions are not statistically significant:
ctr_within_instop


#' ### Complexity

# Does the effect of towards vs other change from A to C?
lsmctr_atoc_incomplex = lsmeans(mod_contain_forcontrast, "AltMD", by = "ContainmentLevel",
                                at = list(ContainmentType='complex', ContainmentLevel = c('a','b','c')))
ctr_intpoly_incomplex = contrast(lsmctr_atoc_incomplex, interaction=c('trt.vs.ctrl','pairwise'))
ctr_bylev_incomplex = contrast(lsmctr_atoc_incomplex, method=c('trt.vs.ctrl'))
ci_bylev_incomplex = confint(ctr_bylev_incomplex)
#' The relative slowdown going from Towards motion to the average of No motion and Away along each 
#' level of complexity are:
#' 
#' * A (simple): `r exp(ci_bylev_incomplex$estimate[1])` times slower (95% CI = [`r exp(ci_bylev_incomplex$lower.CL[1])`, `r exp(ci_bylev_incomplex$upper.CL[1])`])
#' * B (slightly complex): `r exp(ci_bylev_incomplex$estimate[2])` times slower (95% CI = [`r exp(ci_bylev_incomplex$lower.CL[2])`, `r exp(ci_bylev_incomplex$upper.CL[2])`])
#' * C (very complex): `r exp(ci_bylev_incomplex$estimate[3])` times slower (95% CI = [`r exp(ci_bylev_incomplex$lower.CL[3])`, `r exp(ci_bylev_incomplex$upper.CL[3])`])
#' 
#' The critical test here is whether the use of simulation increases in the most complex trials vs. the 
#' simplest ones -- or a contrast between the advantage for Towards vs Others in level A vs C. However,
#' given that simulation is occurring and the test is not statistically signifiant, this doesn't tell 
#' us much about what complexity is changing in people's mental models.
ctr_intpoly_incomplex[2,]


#+ Accuracy --------------------------------------

#' ## Accuracy on contained trials
#' 
#' People did not perform perfectly even on the fully contained trials. This varied across trial types and 
#' motion directions. This isn't a point that we necessarily need to put weight on in the paper, but should 
#' report it

plot_contain_acc_all

acc_tab = with(gooddat, table(Class, WasCorrect))
test_all_acc = chisq.test(acc_tab)
acc_tab_disp = gooddat %>% group_by(Class) %>% summarize(Accuracy = mean(WasCorrect))

#' Model testing suggests that 
#' the same things that affect reaction time also seem to affect accuracy:

mod_acc_contain = glm(WasCorrect ~ ContainmentType*ContainmentLevel*MotionDirection, family=binomial, data=containdat)
anova(mod_acc_contain, test='Chisq')

#' Now, people are clearly not getting *every* contained trial correct, which in some cases can probably be considered misclicks or other errors in 
#' judgment (except possibly in the Porousness and Stopperage trials). However, these trials are much easier 
#' than non-contained trials (average accuracy for contained = `r acc_tab_disp$Accuracy[1]` vs non-contained = 
#' `r acc_tab_disp$Accuracy[2]`). And analyzing RTs for containment trials only in the cases where
#' participants indicated the correct goal does not lead to qualitatively different results.


#' Another explanation: people spend more time deliberating on the no motion and reverse trials 
#' 
containdat_sz_cmplx = subset(containdat, ContainmentType %in% c('size','complex'))
mod_acc_limit = glm(data=containdat_sz_cmplx, family=binomial,
                    WasCorrect ~ ContainmentType*ContainmentLevel*MotionDirection)


acc_bymot = containdat %>% group_by(MotionDirection, ContainmentType) %>% 
  summarize(Acc = mean(WasCorrect)) %>% spread(MotionDirection, Acc)
contr_acc_bymot = lsmeans(mod_acc_limit, 'MotionDirection') %>% contrast(method='pairwise')

kable(containdat %>% group_by(MotionDirection) %>% summarize(Acc=mean(WasCorrect)))

kable(acc_bymot)
print(contr_acc_bymot)

#+ Learning ----------------------------
mod_learning = lmer(data=gooddat, LogRT ~ TrialNum + (1|WID) + (1|Trial))
learn_amt = exp(fixef(mod_learning)[2])
learn_ci = exp(confint(mod_learning)['TrialNum',])

#+ Filler trials -----------------------------------------------------

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

# Test - is accuracy for contained trials above accuracy for non-contained
reg_vscont_acc_tab = with(gooddat, table(Class, WasCorrect))
reg_vscont_acc_sum = gooddat %>% group_by(Class) %>% summarize(Acc = mean(WasCorrect))
reg_vscont_acc = chisq.test(reg_vscont_acc_tab)

#' # Non-contained trials
#' 
#' To double check, we test whether there is any differentiation in reaction time for the non-contained trials between 
#' when there is motion and when there is not. If motion doesn't change reaction time *even when we know people 
#' are not using containment reasoning* then we won't be able to tell anything about the contained 
#' trials when simulation is ambiguous
#' 
#' The regular trials with motion had shorter reaction times on average than the same trials 
#' without motion (geometric mean rt of `r mean(regdat_geolrt$Fwd)`s for motion, `r mean(regdat_geolrt$None)`s
#' for no motion, `r print.t.test(reg_lrt_test)`). This reaction time difference existed even with no reliable 
#' difference in accuracy across matched trials (mean accuracy of motion trials: `r mean(regdat_acc$Fwd)`, 
#' mean accuracy of no motion trials `r mean(regdat_acc$None)`, `r print.t.test(reg_acc_test)`).
#' 
#' Plots of geometric mean of RT and accuracy across trials (probably not to be used):
#' 
print(plot_reg_rt)
print(plot_reg_acc)


#+ Checking correlations with path length --------------------
tmdat = read.csv('../ContainmentTrials/TrialLengths.csv')
aggcont_trial = gooddat %>% 
  group_by(Trial,Class,ContainmentType,ContainmentLevel,MotionDirection) %>% summarize(LRT = mean(LogRT)) %>%
  merge(tmdat %>% mutate(MotionDirection = Direction) %>% select(Trial,MotionDirection,Time,Bounces)) %>% mutate(RT = exp(LRT))
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
ggsave('FigCorPlt.png',cor_plt,width=4,height=3,units='in',dpi=300)

cor_plt2 = ggplot(aggcont_trial %>% mutate(Type = CondType2), 
                  aes(x=Time, y=RT*1000, color=Type, shape=Type)) + geom_point(alpha = .8) + theme_bw() +
  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')
ggsave('FigCorPlt2.png',cor_plt2,width=4,height=3,units='in',dpi=300)

cor_plt3 = ggplot(aggcont_trial %>% subset(!Uncont) %>% mutate(Type = CondType2), 
                  aes(x=Time, y=RT*1000, color=Type, shape=Type)) + geom_point(alpha = .8) + theme_bw() +
  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')

cor_plt4 = ggplot(agct2 %>% mutate(Type = CondType),
                  aes(x=Time, y=RT*1000, color=Type, shape=Type)) + geom_point(alpha = .8) + theme_bw() +
  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')

agt2 = aggcont_trial %>% mutate(ThisType = ifelse(Class=='regular','Non-Topo',ifelse(Uncont,'Topo-Uncontained',ifelse(MotionDirection=='Fwd','Topo-Towards','Topo-Away'))))
agt2$ThisType = factor(agt2$ThisType, levels = c('Non-Topo','Topo-Towards','Topo-Away','Topo-Uncontained'))
ggplot(agt2, aes(x=Time, y=RT*1000, color=ThisType)) + geom_point(alpha = .8) + theme_bw() +
  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')
ggplot(agt2 %>% subset(ThisType != 'Topo-Uncontained'), aes(x=Time, y=RT*1000, color=ThisType)) + geom_point(alpha = .8) + theme_bw() +
  xlab('Travel Time (s)') + ylab('Reaction Time (ms)')

anova(lm(RT ~ Time + Time:ThisType, data=agt2))

# Plot matched
time_lm = lm(RT ~ Time + Time:CondType, data=aggcont_trial)
time_lm_base = lm(RT ~ Time, data=aggcont_trial)
time_lm_bounces = lm(RT ~ (Time + Bounces)*CondType, data=aggcont_trial)
with(aggcont_trial, cor(Time, RT))

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

ggsave("FigCorCon_Base.png",plot_cor_connect,width=4,height=4,units='in',dpi=300)
ggsave("FigCorCon_Legend.png",plot_cor_connect_legend,width=5,height=4,units='in',dpi=300)


ggplot(subset(aggcont_trial,CondType != "Filler"), aes(x=Time, y=RT, color=CondType, shape=CondType)) + geom_point() + theme_bw()

ggplot(aggcont_trial, aes(x=Time,y=RT, color=Uncont, shape=CondType)) + geom_point() + theme_bw()

time_lm_fill = lm(RT ~ Time, data=subset(aggcont_trial, CondType == "Filler"))
time_lm_fwd = lm(RT ~ Time, data=subset(aggcont_trial, CondType == "Fwd"))
time_lm_rev = lm(RT ~ Time, data=subset(aggcont_trial, CondType == "Rev"))

# STUFF TO USE
time_lm_cont = lm(RT ~ Time + Time:CondType, data=subset(aggcont_trial, CondType != "Filler"))
time_lm_cont_base = lm(RT ~ Time, data=subset(aggcont_trial, CondType != "Filler"))

lme_lm_cont_fconly = lm(RT ~ Time + Time:CondType, data=subset(aggcont_trial, !Uncont))
lme_lm_cont_fconly_base = lm(RT ~ Time, data=subset(aggcont_trial, !Uncont))


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

#+ Check vs containment
contain_trials = containdat %>% group_by(Trial, MotionDirection, ContainmentType, ContainmentLevel) %>% summarize(LRT = mean(LogRT)) %>% mutate(RT = exp(LRT))

rrt = read.csv('../ContainmentModels/RRTTest_N15.csv')
with(subset(rrt, IsContained == 'True'), mean(TotalSteps==3001))
comp_rrt = merge(contain_trials, rrt) %>% subset(IsContained=='True' & TotalSteps < 3001) %>% 
  select(Trial, MotionDirection, ContainmentType, ContainmentLevel, RT, TotalSteps)
ggplot(comp_rrt, aes(x=TotalSteps, y=RT, color=MotionDirection)) + geom_point()
with(comp_rrt, cor(RT, TotalSteps))
with(subset(comp_rrt, MotionDirection=='None'), cor(RT, TotalSteps))
ggplot(subset(comp_rrt, MotionDirection=='None'), aes(x=TotalSteps,y=RT,color=ContainmentType,shape=ContainmentLevel)) + geom_point()


flood = read.csv('../ContainmentModels/ContainmentTest.csv') %>% subset(Type=='Flood')
flood$Contained = with(flood,(GReach == 'True' & RReach == 'False') | (GReach == 'False' & RReach== 'True'))
comp_flood = merge(contain_trials, flood) %>% subset(Contained) %>% 
  select(Trial, MotionDirection, ContainmentType, ContainmentLevel, RT, TotalSteps)
ggplot(comp_flood, aes(x=TotalSteps, y=RT, color=MotionDirection)) + geom_point()
with(comp_flood, cor(RT, TotalSteps))
with(subset(comp_flood, MotionDirection=='None'), cor(RT, TotalSteps))
comp_flood2 = merge(contain_trials, flood) %>% subset(Contained) %>% 
  select(Trial, MotionDirection, ContainmentType, ContainmentLevel, RT, TotalSteps)
ggplot(comp_flood2, aes(x=TotalSteps, y=RT, color=ContainmentType, shape=ContainmentLevel)) + geom_point()
anova(lm(RT ~ ContainmentType*ContainmentLevel + TotalSteps, data=comp_flood2))

