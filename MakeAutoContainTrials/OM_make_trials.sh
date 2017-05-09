#!/usr/bin/env bash
#SBATCH --job-name=BalanceModel
#SBATCH --output=SlurmOut/MakeTrials-%j.out
#SBATCH --error=SlurmOut/MakeTrials-%j.err
#SBATCH --mem=32000
#SBATCH --nodes=1
#SBATCH -c 1
#SBATCH -t 24:00:00

python make_trials.py "$1" "$2"