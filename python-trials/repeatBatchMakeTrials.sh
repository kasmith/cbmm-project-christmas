while [ $(./countTrials.sh) -lt 50000 ]; do
    python batchMakeTrials.py 10000 > /dev/null
done
