import glob
import json
import gzip
import numpy as np
import multiprocessing as mp
from indexing_v6 import load_file

cpus = 192
data_dir = '/data_c/raw'
raw_paths = list(sorted(glob.glob(f'{data_dir}/**/*.json*', recursive=True)))
print(len(raw_paths))

def extract_meta(raw_path):
    rel_path = raw_path[len(data_dir)+1:]
    lines = load_file(raw_path)
    mt_path = raw_path + '.metadata'
    om_path = raw_path + '.metaoff'
    mt_fout = open(mt_path, 'wb')
    om_fout = open(om_path, 'wb')
    om = 0
    for linenum, line in enumerate(lines):
        meta = json.loads(line.strip('\n'))
        del meta['text']
        meta = (json.dumps({'path': rel_path, 'linenum': linenum, 'metadata': meta}) + '\n').encode('utf-8')
        mt_fout.write(meta)
        om_fout.write(np.array([om], dtype=np.uint64).view(np.uint8).tobytes())
        om += len(meta)
    mt_fout.close()
    om_fout.close()

with mp.get_context('fork').Pool(cpus) as p:
    p.map(extract_meta, raw_paths)
