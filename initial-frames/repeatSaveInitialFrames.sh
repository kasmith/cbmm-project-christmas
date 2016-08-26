while [ $(ls -A ~/frames-new | wc -l) -lt 100000 ]; do
    python saveInitialFrames.py > /dev/null
done
