#!/bin/env python
# -*- coding: utf-8 -*-

import os

PREFIX='mozcv'

outfn=PREFIX+'_spk2utt'

with open (outfn, 'w') as outf:

    for dirfn in os.listdir('test_data'):

        for infn in os.listdir('test_data/%s' % dirfn):

            if not infn.endswith('ident.seg'):
                continue

            cluster = None
            with open('test_data/%s/%s' % (dirfn, infn), 'r') as seg_f:

                while not cluster:
                    line = seg_f.readline()
                    if not line:
                        break

                    # print line
                    for key in line.split():
                        # print repr(key)
                        if 'init#_#' in key:
                            cluster = key[7:]
                            break

            print infn, cluster

            outf.write('%s%s %s\n' % (PREFIX, cluster, dirfn))

print "%s written." % outfn

