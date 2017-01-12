def main():
    NEW_DIMS = '[1000, 620]'

    trial_types = ['complex', 'porous', 'size', 'stopper']
    trial_nums = ['1', '2', '3', '4', '5', '6']
    trial_conds = ['a', 'b', 'c']

    for t in trial_types:
        for n in trial_nums:
            for c in trial_conds:
                with open('_'.join([t, n, c]) + '.json', 'r+') as f:
                    f.write('{\"Dims\": '+ NEW_DIMS)                    
                    print 'changed ' + '_'.join([t,n,c]) + '.json'


if __name__ == '__main__':
    main()
