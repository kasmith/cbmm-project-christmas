library(weights)
library(ggplot2)
library(RColorBrewer)
library(dplyr)
library(tidyr)

######### Load info

nndat = read.csv('../data/model_googlenet-4800_complete_trials.csv')
empdat_full = read.csv('../data/OnlineRGGoodData.csv')
empdat = empdat_full %>% subset(Prediction != 'U') %>% group_by(Trial,Time) %>% 
  summarize(PRed = mean(NormPrediction == 'R'), Acc = mean(as.character(NormPrediction) == as.character(NormGoal)), N = length(Worker))

goal_info = empdat_full %>% group_by(Trial) %>% select(Trial, NormGoal) %>% ungroup %>% unique
nndat = merge(nndat, goal_info)
nndat$Acc = with(nndat, ifelse(NormGoal == 'G', PGreen, PRed))

physdat = read.csv('../data/ModelFits.csv')
physdat = merge(physdat, goal_info) %>% mutate(Acc = ifelse(NormGoal=='G', 1-PRGA, PRGA))

######## Empirical accuracy vs. model accuracy

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
full_dat = empdat %>% mutate(EmpRed = PRed) %>% select(Trial, Time, N, EmpRed) %>%
  merge(nndat %>% mutate(NNRed = PRed) %>% select(Trial, Time, NNRed)) %>%
  merge(physdat %>% mutate(PhysRed = PRGA, Goal = NormGoal) %>% select(Trial, Time, PhysRed, Goal))

######## Plot red over time
plot_reds = function(trnm, minobs = 3) {
  
  trinfo = full_dat %>% subset(Trial == trnm) %>% subset(N >= minobs) %>% select(Time, EmpRed, NNRed, PhysRed) %>%
    gather(key = Model, value = PRed, -Time)
  
  return(ggplot(trinfo, aes(x = Time, y = PRed, group=Model, color=Model)) + geom_line() + 
           xlim(c(0,max(trinfo$Time))) + ylim(c(0,1)) + theme_bw())
}

# For example...
plot_reds('RTr_Bl1_1')

######## Plot 2-d histograms
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
    scale_fill_gradientn(name='Log-Frequency', colours = cpal) + 
    theme_bw() + theme(legend.position='bottom')
  
  return(plt)
}

# Call to plot the 2-d histograms
plot_red_cor('NNRed')
plot_red_cor('PhysRed')


######## Calculate weighted correlations between models and people
# Note: the weights package has found a bug in the weighted partial correlations -- cannot use that

overall_nn_cor = with(full_dat, wtd.cors(EmpRed, NNRed, weight=N))[1,1] # r_w = 0.835
overall_phys_cor = with(full_dat, wtd.cors(EmpRed, PhysRed, weight=N))[1,1] # r_w = 0.956

# Without weighting, correlations look worse...
no_weight_nn_cor = with(full_dat, cor(EmpRed, NNRed)) # r = 0.779
no_weight_phys_cor = with(full_dat, cor(EmpRed, PhysRed)) # r = 0.891
