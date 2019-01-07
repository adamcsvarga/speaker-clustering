#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# This script does the following:
# 1 -- Based on the files in the "wav_input" folder, it performs diarization where speakers are
# classified globally amongst files, so that it can be used for speaker-adaptive training. This includes
# speech/music/silence segmentation. It is mainly based on the LIUM Speaker Diarization Toolkit,
# but there are several tricks applied to save memory and computation time (see README for details)
#
# 2 -- It trains a speaker-GMM with MAP
#
# 3 -- Based on the speaker-GMM, it performs speaker-recognition, and it outputs a speaker decision
# for each input test file  
#
# Adam Varga, 2016
#
# python port by Guenter Bartsch, 2018
#

import sys
import os

from nltools import misc

stage = 0
nj=12

# experiment with these until you reach a good #clusters vs performance ratio
# stride = 10
# stride = 100
stride = 200

total = 0;
for fn in os.listdir('wav'):
    total += 1

if stage <= 0:

    os.system('rm -rf data sample test_data')
    os.system('mkdir -p data')
    os.system('rm -f run_parallel.sh')
    os.system('rm -f wav/speaker.wav')

# #########################################################
# # Diarize input files separately with parallelization   #
# #########################################################

if stage <= 1:

    # echo "#!/bin/bash" >> run_parallel.sh # control parallelization
    # # speeding up by running processes parallelly
    # c=0
    # for f in wav/*.wav; do
    # 
    #   show=`basename $f .sph`
    #   show=`basename $show .wav`
    # 
    #   datadir=data/${show}
    # 
    #   if [ ! -f ${datadir}/$show.c.gmm ] ; then
    #     echo "Missing: $datadir"
    #     ((c++))
    #     if [ $c -gt $nj ]; then
    #       c=0
    #       echo "wait" >> run_parallel.sh
    #       echo "./cluster_individual.sh ./$f &" >> run_parallel.sh
    #     else
    #       echo "./cluster_individual.sh ./$f &" >> run_parallel.sh
    #     fi
    #   else
    #     echo "Exists: $datadir"
    #   fi
    # done
    # echo "wait" >> run_parallel.sh
    # echo "exit 0" >> run_parallel.sh
    # 
    # # parallel diarization
    # chmod +x run_parallel.sh
    # exit 0
    # ./run_parallel.sh
    # rm run_parallel.sh

    with open ('run_parallel.sh', 'w') as scriptf:

        cnt = 0
        for fn in os.listdir('wav'):

            if not fn.endswith('.wav'):
                continue

            show = os.path.splitext(fn)[0]

            datadir = 'data/%s' % show

            if not os.path.exists('%s/%s.c/gmm' % (datadir, fn)):

                cnt += 1
                if cnt % stride != 0:
                    continue
                if (cnt % nj) == 0:
                    scriptf.write('wait\n')

                cmd = './cluster_individual.sh wav/%s' % fn
                print "%6d/%6d %s" % (cnt, total, cmd)
                scriptf.write('echo %s\n' %fn)
                scriptf.write('%s &\n' % cmd)

        scriptf.write('wait\n')

    os.system('bash run_parallel.sh')

########################################################
# Get a sample from each file for each cluster         #
########################################################

if stage <= 2:

    misc.mkdirs('sample')

    # # save all clusters appearing in each file
    # for f in data/*; do
    #   fname=`echo "$f" | rev | cut -f1 -d'/' | rev`
    #   echo python get_clust.py ${f}/${fname}.c.3.seg
    #   python get_clust.py ${f}/${fname}.c.3.seg
    # done

    with open ('run_parallel.sh', 'w') as scriptf:

        cnt = 0
        for fn in os.listdir('data'):
            cnt += 1

            if (cnt % nj) == 0:
                scriptf.write('wait\n')

            cmd = 'python get_clust.py data/%s/%s.c.3.seg &' % (fn, fn)
            print "%6d/%6d %s" % (cnt, total, cmd)
            # os.system(cmd)
            scriptf.write('echo %s\n' %fn)
            scriptf.write('%s\n' % cmd)
        scriptf.write('wait\n')

    os.system('bash run_parallel.sh')

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

    return None, None

if stage <= 3:
    # # get samples
    # for f in data/*; do
    #   fname=`echo "$f" | rev | cut -f1 -d'/' | rev`
    #   while read line; do
    #     clust_id=`echo "$line" | cut -f1 -d' '`
    #     startdur=`python segment_egs.py ${clust_id} ${f}/${fname}.c.3.seg`
    #     start=`echo $startdur | cut -f2 -d"'"`
    #     dur=`echo $startdur | cut -f4 -d"'"`
    #     if [ "$start" != "None" ]; then
    #       sox wav/${fname}.wav sample/${fname}_s${clust_id}.wav trim ${start} ${dur}
    #     fi
    #   done < ${f}/${fname}.c.3.seg.clusters  
    # done

    cnt = 0
    with open ('run_parallel.sh', 'w') as scriptf:
        for fname in os.listdir('data'):
            cfname = 'data/%s/%s.c.3.seg.clusters' % (fname, fname) 
            # print cfname

            with open(cfname, 'r') as inf:
                while True:
                    line = inf.readline()
                    if not line:
                        break

                    parts = line.split(' ')
                    clust_id = parts[0]

                    wavfn = 'sample/%s_s%s.wav' % (fname, clust_id)
                    if os.path.exists(wavfn):
                        continue

                    # print line

                    start, dur = get_times(clust_id, 'data/%s/%s.c.3.seg' % (fname, fname))
                    if start:
                        cnt += 1
                        if (cnt % nj) == 0:
                            scriptf.write('wait\n')
                        cmd = 'sox wav/%s.wav %s trim %s %s' % (fname, wavfn, start, dur)
                        print "%d / %d JOB: %s" % (cnt, total, cmd)
                        scriptf.write('echo %s\n' %fname)
                        scriptf.write('%s &\n' % cmd)

        scriptf.write('wait\n')
    os.system('bash run_parallel.sh')



# ######################################################
# # Global re-clustering                               #
# ######################################################

if stage <= 4:
    # # initialize samples
    # echo "#!/bin/bash" >> run_parallel.sh # control parallelization
    # # speeding up by running processes parallelly
    # c=0
    # for f in sample/*.wav; do
    #   ((c++))
    #   if [ $c -gt $nj ]; then
    #     c=0
    #     echo "wait" >> run_parallel.sh
    #     echo "./cluster_init.sh ./$f &" >> run_parallel.sh
    #   else
    #     echo "./cluster_init.sh ./$f &" >> run_parallel.sh
    #   fi
    # done
    # echo "wait" >> run_parallel.sh
    # echo "exit 0" >> run_parallel.sh
    # # parallel initialization
    # chmod +x run_parallel.sh
    # ./run_parallel.sh
    # rm run_parallel.sh

    cnt = 0
    with open ('run_parallel.sh', 'w') as scriptf:
        for fname in os.listdir('sample'):

            if not fname.endswith('.wav'):
                continue

            cnt += 1
            if (cnt % nj) == 0:
                scriptf.write('wait\n')
            cmd = './cluster_init.sh sample/%s' % fname
            print "%d / %d JOB: %s" % (cnt, total, cmd)
            scriptf.write('echo %s\n' % fname)
            scriptf.write('%s &\n' % cmd)

        scriptf.write('wait\n')
    os.system('bash run_parallel.sh')



if stage <= 5:
    # # concatenate initialized output
    # cat sample/*/*.i.seg | perl -e '
    # 	$i=0;
    # 
    # 	while(<>){
    # 		chomp; 
    # 		@t=split(/ +/); 
    # 		$n=$t[0]." ".$t[7]; 
    #  
    # 		if(! exists($d{$n})) { 
    # 			$d{$n}="S".$i;
    # 			$i++;
    # 		}
    # 		print "$t[0] $t[1] $t[2] $t[3] $t[4] $t[5] $t[6] ".$d{$n}."\n";
    # 	}'> sample/samples.seg

    with open ('sample/samples.seg', 'w') as samplesf:

        i = 0
        d = {}
        cnt = 0

        for dn in os.listdir('sample'):
            dirn = 'sample/' + dn
            if not os.path.isdir(dirn):
                continue
            # print dirn
            for fn in os.listdir(dirn):
                if not fn.endswith('.i.seg'):
                    continue
                fname = '%s/%s' % (dirn, fn)

                cnt += 1
                print fname

                with open(fname, 'r') as inf:
                    while True:
                        line = inf.readline()
                        if not line:
                            break
                        if line.startswith(';'):
                            continue
                        
                        t = line.strip().split(' ')
                        if len(t) != 8:
                            print "%s Failed to parse line: %s" % (fname, line.strip())

                        n = t[0] + ' ' + t[7]
                        if not n in d:
                            d[n] = "S%d" % i
                            i += 1

                        samplesf.write('%s %s %s %s %s %s %s %s\n' % (t[0], t[1], t[2], t[3], t[4], t[5], t[6], d[n]))


if stage <= 6:
                        
    # # re-clustering based on the samples
    # java -Xmx12G -classpath \
    # src/LIUM_SpkDiarization-8.4.1.jar fr.lium.spkDiarization.programs.MClust \
    #  --help --fInputMask=sample/%s.wav --fInputDesc=$fDescCLR \
    # --sInputMask=sample/samples.seg --sOutputMask=sample/%s.seg \
    # --cMethod=ce --cThr=1.7 --tInputMask="src/ubm.gmm" \
    # --emCtrl=1,5,0.01 --sTop=5,"src/ubm.gmm" cross

    cmd = ('java -Xmx48G -classpath '
           'src/LIUM_SpkDiarization-8.4.1.jar fr.lium.spkDiarization.programs.MClust '
           '--fInputMask=sample/%s.wav --fInputDesc="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4" '
           '--sInputMask=sample/samples.seg --sOutputMask=sample/%s.seg '
           '--cMethod=ce --cThr=1.7 --tInputMask="src/ubm.gmm" '
           '--emCtrl=1,5,0.01 --sTop=5,"src/ubm.gmm" cross' ) 

    print cmd
    os.system(cmd)

#################################################################
# Re-write global cluster labels to original segmentation       #
#################################################################

if stage <= 7:
    # rm -f data/*/*.final.seg
    # python assign_clusters.py sample/cross.seg
    os.system('rm -f data/*/*.final.seg')
    os.system('python assign_clusters.py sample/cross.seg')

################################################################
# Train speaker model with MAP                                 #
################################################################

if stage <= 8:
    # rm -f wav/speaker.wav
    # rm -f data/speaker.seg
    # for f in wav/*.wav; do
    #  fname=`echo $f | rev | cut -f2- -d'.' | cut -f1 -d'/' | rev`
    #  python concat_seg.py data/${fname}/${fname}
    #  if [ -f wav/speaker.wav ]; then
    #   sox wav/speaker.wav $f wav/tmp.wav
    #   mv wav/tmp.wav wav/speaker.wav
    #  else
    #   sox $f wav/speaker.wav
    #  fi
    # done

    os.system('rm -f wav/speaker.wav')
    os.system('rm -f data/speaker.seg')

    cnt = 0
    for f in os.listdir('wav'):

        if not f.endswith('.wav'):
            continue

        cnt += 1
        if cnt % stride != 0:
            continue

        fname = os.path.splitext(f)[0]

        cmd = 'python concat_seg.py data/%s/%s' % (fname, fname)
        print cmd
        os.system(cmd)

        if os.path.exists('wav/speaker.wav'):
            cmd = 'sox wav/speaker.wav wav/%s.wav wav/tmp.wav' % fname
            print cmd
            os.system(cmd)
            cmd = 'mv wav/tmp.wav wav/speaker.wav'
            print cmd
            os.system(cmd)
        else:
            cmd = 'sox wav/%s.wav wav/speaker.wav' % fname
            print cmd
            os.system(cmd)

if stage <= 9:
 
    # # copy the UBM for each speaker
    # java -Xmx2024m -cp src/LIUM_SpkDiarization-8.4.1.jar fr.lium.spkDiarization.programs.MTrainInit --help --sInputMask=data/%s.seg --fInputMask=wav/%s.wav --fInputDesc="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --emInitMethod=copy --tInputMask=src/ubm.gmm --tOutputMask=data/%s.init.gmm speaker
    # 
    # # train (MAP adaptation, mean only) of each speaker, the diarization file describes the training data of each speaker.
    # java -Xmx2024m -cp src/LIUM_SpkDiarization-8.4.1.jar fr.lium.spkDiarization.programs.MTrainMAP --help --sInputMask=data/%s.seg --fInputMask=wav/%s.wav --fInputDesc="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --tInputMask=data/%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=data/%s.gmm speaker

    cmd='java -Xmx2024m -cp src/LIUM_SpkDiarization-8.4.1.jar fr.lium.spkDiarization.programs.MTrainInit --help --sInputMask=data/%s.seg --fInputMask=wav/%s.wav --fInputDesc="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --emInitMethod=copy --tInputMask=src/ubm.gmm --tOutputMask=data/%s.init.gmm speaker'
    os.system(cmd)
    cmd='java -Xmx2024m -cp src/LIUM_SpkDiarization-8.4.1.jar fr.lium.spkDiarization.programs.MTrainMAP --help --sInputMask=data/%s.seg --fInputMask=wav/%s.wav --fInputDesc="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --tInputMask=data/%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=data/%s.gmm speaker'
    os.system(cmd)
 
#############################################################
# Speaker recognition                                       #
#############################################################

if stage <= 10:

    cmd='mkdir -p test_data'
    print cmd
    os.system(cmd)

    # # init
    # echo "#!/bin/bash" >> run_parallel.sh # control parallelization
    # # speeding up by running processes parallelly
    # c=0
    # for f in test/*.wav; do
    #   ((c++))
    #   if [ $c -gt $nj ]; then
    #     c=0
    #     echo "wait" >> run_parallel.sh
    #     echo "./cluster_init_test.sh ./$f &" >> run_parallel.sh
    #   else
    #     echo "./cluster_init_test.sh ./$f &" >> run_parallel.sh
    #   fi
    # done
    # echo "wait" >> run_parallel.sh
    # echo "exit 0" >> run_parallel.sh
    # 
    # # parallel initialization
    # chmod +x run_parallel.sh
    # ./run_parallel.sh
    # rm run_parallel.sh

    cnt = 0
    with open ('run_parallel.sh', 'w') as scriptf:
        for fname in os.listdir('test'):

            if not fname.endswith('.wav'):
                continue

            cnt += 1
            if (cnt % nj) == 0:
                scriptf.write('wait\n')
            cmd = './cluster_init_test.sh test/%s' % fname
            print "%d / %d JOB: %s" % (cnt, total, cmd)
            scriptf.write('echo %s\n' % fname)
            scriptf.write('%s &\n' % cmd)

        scriptf.write('wait\n')
    os.system('bash run_parallel.sh')

if stage <= 11:
    # for f in test/*.wav; do
    #  testShow=`echo $f | rev | cut -f2- -d'.' | cut -f1 -d'/' | rev`
    #  java -Xmx2G -Xms2G -cp src/LIUM_SpkDiarization-8.4.1.jar  fr.lium.spkDiarization.programs.Identification --sInputMask=test_data/${testShow}/%s.i.seg --help --fInputMask=test/%s.wav  --sOutputMask=test_data/${testShow}/%s.ident.seg --fInputDesc="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4" --tInputMask=data/speaker.gmm --sTop=5,src/ubm.gmm  --sSetLabel=add $testShow
    # done

    cnt = 0
    with open ('run_parallel.sh', 'w') as scriptf:
        for fname in os.listdir('test'):

            if not fname.endswith('.wav'):
                continue


            testshow = os.path.splitext(fname)[0]
            outfn = 'test_data/%s/%s.ident.seg' % (testshow, testshow)
            if os.path.exists(outfn):
                continue

            cnt += 1
            if (cnt % nj) == 0:
                scriptf.write('wait\n')

            cmd = 'java -Xmx2G -Xms2G -cp src/LIUM_SpkDiarization-8.4.1.jar  fr.lium.spkDiarization.programs.Identification --sInputMask=test_data/' + testshow + '/%s.i.seg --help --fInputMask=test/%s.wav  --sOutputMask=test_data/'+testshow+'/%s.ident.seg --fInputDesc="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4" --tInputMask=data/speaker.gmm --sTop=5,src/ubm.gmm  --sSetLabel=add ' + testshow
            print "%d / %d JOB: %s" % (cnt, total, cmd)
            scriptf.write('echo %s\n' % fname)
            scriptf.write('%s &\n' % cmd)

        scriptf.write('wait\n')

    os.system('bash run_parallel.sh')

