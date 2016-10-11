library(weights)
library(RColorBrewer)
library(ggplot2)
library(dplyr)
library(tidyr)

cache_pcor = T # Saves recomputing bootstrapped partial correlations
pcor = ppcor::pcor

#+ Load info ---------------------

empdat_full = read.csv('../data/OnlineRGGoodData.csv')
empdat = empdat_full %>% subset(Prediction != 'U') %>% group_by(Trial,Time) %>% 
  summarize(PRed = mean(NormPrediction == 'R'), Acc = mean(as.character(NormPrediction) == as.character(NormGoal)), 
            N = length(Worker), NRed = sum(NormPrediction == 'R'), NGreen = sum(NormPrediction == 'G'))

goal_info = empdat_full %>% group_by(Trial) %>% select(Trial, NormGoal) %>% ungroup %>% unique
time_info = empdat_full %>% group_by(Trial) %>% summarize(MaxTime = max(Time)) %>% ungroup

nndat = read.csv('../data/model_googlenet-4800_complete_trials.csv')
nndat = merge(nndat, goal_info)
nndat$Acc = with(nndat, ifelse(NormGoal == 'G', PGreen, PRed))

physdat = read.csv('../data/ModelFits.csv')
physdat = merge(physdat, goal_info) %>% mutate(Acc = ifelse(NormGoal=='G', 1-PRGA, PRGA))

trial_agg = read.csv('../data/TrialAggInfo.csv')
trial_bystep = read.csv('../data/TrialByStepInfo.csv')
trial_bystep$WallBetweenRed = trial_bystep$WallBetweenRed == 'True'
trial_bystep$WallBetweenGreen = trial_bystep$WallBetweenGreen == 'True'

#+ Empirical accuracy vs. model accuracy ----------------------------------

full_acc_info = empdat %>% mutate(EmpAcc = Acc) %>% select(-PRed, -Acc) %>%
  merge(nndat %>% mutate(NNAcc = Acc) %>% select(Trial,Time,NNAcc)) %>%
  merge(physdat %>% mutate(PhysAcc = Acc) %>% select(Trial,Time,PhysAcc))

wtd_trial_acc = full_acc_info %>% group_by(Trial) %>%
  summarize(EmpAcc = sum(EmpAcc*N)/sum(N), NNAcc = sum(NNAcc*N)/sum(N), PhysAcc=sum(PhysAcc*N)/sum(N))

# Weighted accuracy (by number of observed button presses):
sapply(wtd_trial_acc[2:4], mean)
# Empirical: 81.7%
# Neural Network: 65.5%
# Physics Model: 82.2%

######## Full P(Red)s
full_dat = empdat %>% mutate(EmpRed = PRed) %>% select(Trial, Time, N, NRed, NGreen, EmpRed) %>%
  merge(nndat %>% mutate(NNRed = PRed) %>% select(Trial, Time, NNRed)) %>%
  merge(physdat %>% mutate(PhysRed = PRGA, Goal = NormGoal) %>% select(Trial, Time, PhysRed, Goal)) %>%
  merge(time_info) %>% mutate(RemTime = round(MaxTime - Time,1))

######## Plot red over time
plot_reds = function(trnm, minobs = 3) {
  
  trinfo = full_dat %>% subset(Trial == trnm) %>% subset(N >= minobs) %>% select(Time, EmpRed, NNRed, PhysRed) %>%
    gather(key = Model, value = PRed, -Time)
  
  return(ggplot(trinfo, aes(x = Time, y = PRed, group=Model, color=Model)) + geom_line() + 
           xlim(c(0,max(trinfo$Time))) + ylim(c(0,1)) + theme_bw())
}

# For example...
plot_reds('RTr_Bl1_1')

#+ Plot 2-d histograms ---------------------------------------------
defcpal = colorRampPalette(brewer.pal(9,'YlOrRd'))(100)

plot_red_cor = function(comp = 'NNRed', nbreaks = 40, weight = T, log_this = T, cpal = defcpal) {
  # Set up the buckets
  xlims = c(0,1)
  ylims = c(0,1)
  
  xbr = seq(xlims[1],xlims[2],length.out=nbreaks+1)
  ybr = seq(ylims[1],ylims[2],length.out=nbreaks+1)
  
  xbr[1] = xlims[1]-.001
  ybr[1] = ylims[1]-.001
  xbr[length(xbr)] = xlims[2]+.001
  ybr[length(ybr)] = ylims[2]+.001
  
  xdif = xbr[2]-xbr[1]
  ydif = ybr[2]-ybr[1]
  
  xcnt = xbr[-1] - xdif/2
  ycnt = ybr[-1] - ydif/2
  
  m.counts = matrix(integer(nbreaks*nbreaks),nrow=nbreaks)
  dimnames(m.counts) = list(xcnt,ycnt)
  
  N = nrow(full_dat)
  xs = full_dat[[comp]]
  ys = full_dat[['EmpRed']]
  ws = full_dat[['N']]
  
  for(i in 1:N) {
    x = xs[i]
    y = ys[i]
    w = ws[i]
    # Find the right bucket
    xbk = max(which(x > xbr))
    ybk = max(which(y > ybr))
    # If you weight things, bucket increment is dependent on number of observations, else 1
    inc = ifelse(weight, w / mean(ws), 1)
    m.counts[xbk, ybk] = m.counts[xbk, ybk] + inc
  }
  
  if(log_this) {
    m.counts = log(m.counts + 1,base = 10)
  }
  
  # Expand the grid for plotting
  df = expand.grid(x = xcnt, y = ycnt)
  df$Obs = mapply(function(x,y){m.counts[x,y]},as.character(df$x),as.character(df$y))
  
  plt = ggplot(df, aes(x,y,fill=Obs)) + geom_raster(interpolate=F) + xlab('Model') + ylab('Empirical') +
    scale_fill_gradientn(name='Log-Frequency', colours = cpal, limits = c(0,3.1)) + 
    theme_bw() + theme(legend.position='bottom') + guides(fill = guide_colorbar(title.position='top',title.hjust=.5))
  
  return(plt)
}

# Call to plot the 2-d histograms
nn.cor.plot = plot_red_cor('NNRed') + xlab('CNN')
phys.cor.plot = plot_red_cor('PhysRed') + xlab('Physics')

ggsave('Figures/nnplot.pdf', nn.cor.plot+theme(legend.position='none'), height=3, width=3, units='in')
ggsave('Figures/physplot.pdf', phys.cor.plot+theme(legend.position='none'), height=3, width=3, units='in')
ggsave('Figures/corplot_legend.pdf', nn.cor.plot, height=3, width=3, units='in')

#+ Calculate weighted correlations between models and people ---------------
# Note: the weights package has found a bug in the weighted partial correlations -- cannot use that

overall_nn_cor = with(full_dat, wtd.cors(EmpRed, NNRed, weight=N))[1,1] # r_w = 0.835
overall_phys_cor = with(full_dat, wtd.cors(EmpRed, PhysRed, weight=N))[1,1] # r_w = 0.956

# Without weighting, correlations look worse...
no_weight_nn_cor = with(full_dat, cor(EmpRed, NNRed)) # r = 0.779
no_weight_phys_cor = with(full_dat, cor(EmpRed, PhysRed)) # r = 0.891

# Need to make my own weighted partial correlations...
# (I think this works... it does for the degenerate case of equal weights)
wtd_pcor = function(x,y,z,weight) {
  # Residualize
  r_x = resid(lm(x ~ z, weights = weight))
  r_y = resid(lm(y ~ z, weights = weight))
  N = length(x)
  
  w_mx = sum(weight*r_x)/sum(weight)
  w_my = sum(weight*r_y)/sum(weight)
  w_cov_xy = sum(weight * (r_x-w_mx)*(r_y-w_my)) / sum(weight)
  w_cov_xx = sum(weight * (r_x-w_mx)*(r_x-w_mx)) / sum(weight)
  w_cov_yy = sum(weight * (r_y-w_my)*(r_y-w_my)) / sum(weight)
  w_cor = w_cov_xy / sqrt(w_cov_xx * w_cov_yy)
  return(w_cor)
}

boot_wtd_pcor = function(x,y,z,weight,range = c(.025, .975), ntimes = 500) {
  nsamp = length(x)
  reps = replicate(ntimes, (function() {
    this.idx = base::sample(1:nsamp, nsamp, replace=T)
    return(wtd_pcor(x[this.idx], y[this.idx], z[this.idx], weight[this.idx]))
  })())
  return(quantile(reps, range))
}

tlims = c(.4, 4.)
rem_tlims = c(0., 4.)

if(cache_pcor) {
  load('CachedPCor.RData')
} else {
  nn_pcors = full_dat %>% subset(Time >= tlims[1] & Time <= tlims[2]) %>% group_by(Time) %>% 
    summarize(pcor = wtd_pcor(EmpRed, NNRed, PhysRed, N), ci = list(boot_wtd_pcor(EmpRed, NNRed, PhysRed, N)))
  nn_pcors$ci.025 = sapply(nn_pcors$ci, function(x) {x[1]})
  nn_pcors$ci.975 = sapply(nn_pcors$ci, function(x) {x[2]})
  nn_pcors = nn_pcors %>% select(-ci)
  nn_pcors$Model = "CNN"
  
  phys_pcors = full_dat %>% subset(Time >= tlims[1] & Time <= tlims[2]) %>% group_by(Time) %>% 
    summarize(pcor = wtd_pcor(EmpRed, PhysRed, NNRed, N), ci = list(boot_wtd_pcor(EmpRed, PhysRed, NNRed, N)))
  phys_pcors$ci.025 = sapply(phys_pcors$ci, function(x){x[1]})
  phys_pcors$ci.975 = sapply(phys_pcors$ci, function(x){x[2]})
  phys_pcors = phys_pcors %>% select(-ci)
  phys_pcors$Model = "Physics"
  
  pcors = rbind(nn_pcors, phys_pcors)
  
  (pcor_beg = ggplot(pcors, aes(x=Time, y=pcor, ymin=ci.025, ymax=ci.975, group=Model, color=Model, fill=Model)) +
    geom_ribbon(alpha = .4) + geom_hline(yintercept = 0) + geom_line() +
    ylim(c(-.3,1)) + xlim(c(0,4)) + ylab('Partial correlation') + xlab('Time from beginning') + theme_bw() +
    theme(legend.position='bottom', legend.title=element_blank()))
  
  
  nn_pcors_rem = full_dat %>% subset(RemTime >= rem_tlims[1] & RemTime <= rem_tlims[2]) %>% group_by(RemTime) %>% 
    summarize(pcor = wtd_pcor(EmpRed, NNRed, PhysRed, N), ci = list(boot_wtd_pcor(EmpRed, NNRed, PhysRed, N)))
  nn_pcors_rem$ci.025 = sapply(nn_pcors_rem$ci, function(x) {x[1]})
  nn_pcors_rem$ci.975 = sapply(nn_pcors_rem$ci, function(x) {x[2]})
  nn_pcors_rem = nn_pcors_rem %>% select(-ci)
  nn_pcors_rem$Model = "CNN"
  
  phys_pcors_rem = full_dat %>% subset(RemTime >= rem_tlims[1] & RemTime <= rem_tlims[2]) %>% group_by(RemTime) %>% 
    summarize(pcor = wtd_pcor(EmpRed, PhysRed, NNRed, N), ci = list(boot_wtd_pcor(EmpRed, PhysRed, NNRed, N)))
  phys_pcors_rem$ci.025 = sapply(phys_pcors_rem$ci, function(x){x[1]})
  phys_pcors_rem$ci.975 = sapply(phys_pcors_rem$ci, function(x){x[2]})
  phys_pcors_rem = phys_pcors_rem %>% select(-ci)
  phys_pcors_rem$Model = "Physics"
  
  pcors_rem = rbind(phys_pcors_rem, nn_pcors_rem)
  
  save(pcors, pcors_rem, file = 'CachedPCor.RData')
}

(pcor_beg = ggplot(pcors, aes(x=Time, y=pcor, ymin=ci.025, ymax=ci.975, group=Model, color=Model, fill=Model)) +
  geom_ribbon(alpha = .4) + geom_hline(yintercept = 0) + geom_line() +
  ylim(c(-.3,1)) + xlim(c(0,4)) + ylab('Partial correlation') + xlab('Time from beginning') + theme_bw() +
  theme(legend.position='bottom', legend.title=element_blank(), axis.title = element_text(size = 9), 
        legend.text = element_text(size=9)))

(pcor_end = ggplot(pcors_rem, aes(x = RemTime, y = pcor, ymin = ci.025, ymax = ci.975, group=Model, color=Model, fill=Model)) +
  scale_x_reverse(name = "Time until end") + geom_ribbon(alpha = .4) + geom_hline(yintercept = 0) + geom_line() +
  ylim(c(-.3,1)) + ylab('Partial correlation') + theme_bw() + 
  theme(legend.position='bottom', legend.title=element_blank(), axis.title = element_text(size = 9), 
        legend.text = element_text(size=9)))


ggsave('Figures/pcor_beg.pdf', pcor_beg, width = 3, height = 2.2, units = 'in')
ggsave('Figures/pcor_end.pdf', pcor_end, width = 3, height = 2.2, units = 'in')

#+ Investigate what the NN model is doing wrt heuristics ----------------------

bystep_data = merge(trial_bystep, trial_bystep %>% group_by(Trial) %>% summarize(MaxBounce=max(BounceSoFar))) %>%
  mutate(RemainingBounce = MaxBounce - BounceSoFar) %>%
  merge(full_dat %>% select(Trial, Time, Goal, MaxTime, RemTime,PhysRed, NNRed)) %>%
  mutate(NNPred = ifelse(Goal=='R', NNRed, 1-NNRed), PhysPred = ifelse(Goal=='R', PhysRed, 1-PhysRed),
         DistGoal = ifelse(Goal=='R', DistRed, DistGreen), DistOther = ifelse(Goal=='R', DistGreen, DistRed),
         VelAngGoal = ifelse(Goal=='R', VelAngFromRed, VelAngFromGreen), VelAngOther = ifelse(Goal=='R', VelAngFromGreen, VelAngFromRed),
         WallBetweenGoal = ifelse(Goal=='R', WallBetweenRed, WallBetweenGreen), WallBetweenOther = ifelse(Goal=='R',WallBetweenGreen, WallBetweenRed)) %>%
  select(Trial, Time, NNPred, PhysPred, RemTime, BounceSoFar, RemainingBounce, DistGoal, DistOther, VelAngGoal, VelAngOther,
         WallBetweenGoal, WallBetweenOther) %>%
  mutate(DistDiff = DistGoal - DistOther, DistRatio = DistGoal / DistOther, VelAngDiff = VelAngGoal - VelAngOther,
         WallDiff = WallBetweenGoal - WallBetweenOther)

agg_data = trial_agg %>% 
  merge(full_dat %>% group_by(Trial, Goal) %>% summarize(NNRed = mean(NNRed), PhysRed = mean(PhysRed))) %>%
  mutate(AreaGoal = ifelse(Goal=='R', AreaRed,AreaGreen), AreaOther = ifelse(Goal=='R', AreaGreen, AreaRed),
         NNPred = ifelse(Goal=='R',NNRed,1-NNRed)) %>%
  mutate(AreaRatio = AreaGoal / AreaOther)

# Correlate with things it could know about
bystep_data_use = bystep_data %>% select(-Trial, -Time, -PhysPred, -RemTime, -RemainingBounce, -BounceSoFar)

bystep_cor = cor(bystep_data_use)['NNPred',-1]
agg_cor = cor(agg_data %>% select(NNPred, NWalls, AreaWalls, AreaGoal, AreaOther, AreaRatio, PropClear))['NNPred',-1]

all_cor = c(bystep_cor[c('DistGoal','DistOther','WallBetweenGoal','WallBetweenOther','VelAngGoal','VelAngOther')],
            agg_cor[c(-5,-6)])
xtable::xtable(data.frame(t(all_cor)),digits=3) # Output

#+ See if a "mixed" model using time-varying contributions from NN vs Physics

get_power = function(p, x) {
  a = p[1]
  k = p[2]
  b = p[3]
  return(min(a*x^(-k) + b),1)
}

mix_models = function(p, nn, phys, time) {
  pw = get_power(p, time)
  return(pw*nn + (1-pw)*phys)
}

calc_llh = function(p) {
  if (p[3] < 0) {return(99999999999999)} 
  
  preds = with(full_dat,mapply(function(n,ph,t){mix_models(p,n,ph,t)}, NNRed,PhysRed,Time))
  llhs = log(preds)*full_dat$NRed + log(1-preds)*full_dat$NGreen
  return(-sum(llhs))
}

mix_opt = optim(c(.01,1,.1), calc_llh)

full_dat$MixRed = with(full_dat,mapply(function(n,ph,t){mix_models(mix_opt$par,n,ph,t)}, NNRed,PhysRed,Time))
plot_red_cor('MixRed')
overall_mix_cor = with(full_dat, wtd.cors(EmpRed, MixRed, weight=N))[1,1]

mix_show_df = data.frame(Time = seq(.1,7,by=.1)) %>% mutate(NN_Contrib = get_power(mix_opt$par, Time))
qplot(Time,NN_Contrib,data=mix_show_df, geom='line')

