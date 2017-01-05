#!/usr/bin/env bash

fdir=$1
if [ -z $fdir ]; then
    fdir="./"
fi

com="python check_trial.py"
for f in $fdir*.ptr; do
    com="$com $f"
done
eval $com