library(ppcor)
library(ggplot2)

hum.dat = read.csv('FirstGoal.csv')
phys.dat = read.csv('ModelFirstPRGA.csv')
nn.dat = read.csv('googlenet_data.csv')

hum.dat = hum.dat[c(1,3)]
names(hum.dat) = c('Trial','HumanRed')

names(phys.dat) = c('Trial', 'PhysModelRed')

nn.dat = nn.dat[c(1,3)]
names(nn.dat) = c('Trial', 'NNRed')

dat = merge(hum.dat, phys.dat)
dat = merge(dat, nn.dat)

# Basic correlations
with(dat, cor(HumanRed, PhysModelRed)) # Hum vs Phys: .91
with(dat, cor(HumanRed, NNRed)) # Hum vs NN: .73
with(dat, cor(NNRed, PhysModelRed)) # NN vs Phys: .74

# Partial correlations
pcor(dat[c(2:4)])
# Cor (Human, Phys | NN) = .80
# Cor (Human, NN | Phys) = .18
# Cor (Phys, NN | Human) = .30

# Plots
abl = geom_abline(intercept=0,slope=1,linetype='dashed')
qplot(PhysModelRed, HumanRed, data=dat, geom='point', xlab='Phys Model',
      ylab = 'Empirical', xlim = c(0,1), ylim = c(0,1)) + abl
qplot(NNRed, HumanRed, data=dat, geom='point', xlab='Neural Network',
      ylab = 'Empirical', xlim = c(0,1), ylim = c(0,1)) + abl

