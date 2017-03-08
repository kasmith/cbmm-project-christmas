#!/bin/bash
#SBATCH --job-name=SPRTModel
#SBATCH --output=SlurmOut/SPRT-%j.out
#SBATCH --error=SlurmOut/SPRT-%j.err
#SBATCH --mem=32000
#SBATCH --nodes=1
#SBATCH -c 1
#SBATCH -t 12:00:00

python full_sprt_model.py $1
