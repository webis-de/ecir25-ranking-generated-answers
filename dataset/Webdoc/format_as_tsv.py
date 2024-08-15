from glob import glob
import pandas as pd

postfix = '_min_length_50'
# Read in the data
glob_dir = 'crawl/txt' + postfix + '/*/*.txt'
files = glob(glob_dir)
data = []
for file in files:
    out = {}
    uuid = file.split('/')[-1].split('.')[0]
    out['docid'] = uuid
    out['text'] = open(file, 'r').read()
    data.append(out)

pd.DataFrame(data).to_csv(f'data/txt{postfix}.tsv', sep='\t', index=False)


