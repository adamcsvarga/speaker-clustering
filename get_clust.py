# -*- coding: utf-8 -*-
"""
get_clust.py -- gets unique clusters from cluster files
usage: python get_clust.py input_file

Created on Wed Feb 11 16:04:00 2015

@author: vargaada
"""

import sys, re

def to_clust(fname):
    with open(fname + '.clusters', 'w'):
        pass
    with open(fname, 'r') as sources:
        lines = sources.readlines()
    clusters = []
    for line in lines:
        #clusters.append(line[-2:])
        clusters.append(int(re.sub(r'[^0-9]', r'', line[-4:])))
    
    cluster_ids = set(clusters)
    for cluster_id in cluster_ids:
        with open(fname + '.clusters', 'a+') as target:
            target.write(str(cluster_id) + ' \n')
     
if __name__ == "__main__":
    to_clust(sys.argv[1])
   
