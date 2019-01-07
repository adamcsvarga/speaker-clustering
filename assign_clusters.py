# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 09:41:29 2015

assigns clusters to individual files based on global clustering
usage: python assign_clusters.py cross.cross.seg

@author: vargaada
"""

import re, sys

def assign(source_file):  
   with open(source_file, 'r') as sources:
        lines = sources.readlines()
   
   for line in lines:

        if line.startswith(';;'):
            continue

        print "line:", line

        file_id = line.split(" ")[0]
        cluster_id = file_id.split("_")[-1].upper()
        dir_name = '_'.join(file_id.split("_")[:-1])
        real_cluster = line.split(" ")[-1][:-1]
            
        with open('data/' + dir_name + '/' + dir_name + '.c.3.seg', 'r') as binfile:
            bin_lines = binfile.readlines()
            
            for bline in bin_lines:
                if bline.split(" ")[-1][:-1] == cluster_id:
                    with open('data/' + dir_name + '/' + dir_name + '.final.seg', 'a+') as output:
                      output.write(re.sub(r'S[0-9]+', real_cluster, bline))

if __name__ == "__main__":
    assign(sys.argv[1])
