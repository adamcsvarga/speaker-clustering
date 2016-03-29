# -*- coding: utf-8 -*-
"""
segment_egs.py -- gets an example segment from file corresponding to cluster 
id
usage: python segment_egs.py cluster_id filename

Created on Wed Feb 11 17:21:04 2015

@author: vargaada
"""

import sys

def get_times(c_id, fname):
    
    """Takes a segment """    
    
    sample_name = '..' + fname.split('.')[2] + '.sample.seg'
    #clear file if starting new segment (i. e. c_id is 0)
    #assumes that the file to get the samples from is already
    #bi-clustered (contains clusters with ids 0 and 1 only)
    if int(c_id) == 0:
        with open(sample_name, 'w'):
            pass
    
    #read all from source
    with open(fname, 'r') as sources:
        lines = sources.readlines()
        
    #gets the first line that belongs to the corresponding cluster (c_id)
    #and after attaching a subfix to the file id, writes it to sample file
    for line in lines:
        c = line[-2]
        if c == c_id:
            with open(sample_name, 'a+') as targets:
                f_id, rest = line.split(' ')[0], " ".join(line.split(' ')[1:])
                f_mod = f_id + "_s" + str(c_id)
                mod_line = " ".join([f_mod, rest])
                targets.write(mod_line)
           
            start, dur = int(line.split(' ')[2]), int(line.split(' ')[3])
            start_sec, start_mil = start // 100, start % 100
            dur_sec, dur_mil = dur // 100, dur % 100
            #returns start times and durations in sox-readable format
            #can be usedd for segmenting files according to samples
            return ".".join([str(start_sec), str(start_mil)]), ".".join([str(dur_sec), str(dur_mil)])

if __name__ == "__main__":
    print(get_times(sys.argv[1], sys.argv[2]))
