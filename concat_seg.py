# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 09:41:29 2015

concatenates segmentation files with necessary offset

usage: python concat_seg.py seg_file

@author: vargaada
"""

import sys

def append_seg(segfile):
    try:
        with open('data/speaker.seg', 'r') as source:
            seglines = source.readlines()
    except IOError:
        seglines = []
        with open('data/speaker.seg', 'w+'):
            pass

    #with open(segfile + '.i.seg') as source:
    #    ilines = source.readlines()
    #dur = int(ilines[0].split(' ')[3])
    if len(seglines) > 0:
        end = int(seglines[-1].split(' ')[2]) +\
        int(seglines[-1].split(' ')[3])
    else:
        end = 0
    
    with open(segfile + '.final.seg') as source:
        flines = source.readlines()
    
    # split lines to arrays for sorting
    fs = []
    for fline in flines:
       fs.append(fline.split(' '))
    fsorteds = sorted(fs, key=lambda f: int(f[2]))
    
    for fsorted in fsorteds:
        start = int(fsorted[2]) + end
        with open('data/speaker.seg', 'a+') as target:
            target.write('speaker ' + ' '.join(fsorted[1:2]) + ' '  + \
            str(start) + ' ' + ' '.join(fsorted[3:]))
    

if __name__ == '__main__':
    append_seg(sys.argv[1])
    
