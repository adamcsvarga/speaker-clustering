#!/bin/bash

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

mkdir -p data
rm -f run_parallel.sh
rm -f wav/speaker.wav

nj=4
fDescCLR="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4"

#########################################################
# Diarize input files separately with parallelization   #
#########################################################
echo "#!/bin/bash" >> run_parallel.sh # control parallelization
# speeding up by running processes parallelly
c=0
for f in wav/*.wav; do
  ((c++))
  if [ $c -gt $nj ]; then
    c=0
    echo "wait" >> run_parallel.sh
    echo "./cluster_individual.sh ./$f &" >> run_parallel.sh
  else
    echo "./cluster_individual.sh ./$f &" >> run_parallel.sh
  fi
done
echo "wait" >> run_parallel.sh
echo "exit 0" >> run_parallel.sh

# parallel diarization
chmod +x run_parallel.sh
./run_parallel.sh
rm run_parallel.sh

########################################################
# Get a sample from each file for each cluster         #
########################################################

mkdir -p sample
# save all clusters appearing in each file
for f in data/*; do
  fname=`echo "$f" | rev | cut -f1 -d'/' | rev`
  python get_clust.py ${f}/${fname}.c.3.seg
done

# get samples
for f in data/*; do
  fname=`echo "$f" | rev | cut -f1 -d'/' | rev`
  while read line; do
    clust_id=`echo "$line" | cut -f1 -d' '`
    startdur=`python segment_egs.py ${clust_id} ${f}/${fname}.c.3.seg`
    start=`echo $startdur | cut -f2 -d"'"`
    dur=`echo $startdur | cut -f4 -d"'"`
    if [ "$start" != "None" ]; then
      sox wav/${fname}.wav sample/${fname}_s${clust_id}.wav trim ${start} ${dur}
    fi
  done < ${f}/${fname}.c.3.seg.clusters  
done

######################################################
# Global re-clustering                               #
######################################################
# initialize samples
echo "#!/bin/bash" >> run_parallel.sh # control parallelization
# speeding up by running processes parallelly
c=0
for f in sample/*.wav; do
  ((c++))
  if [ $c -gt $nj ]; then
    c=0
    echo "wait" >> run_parallel.sh
    echo "./cluster_init.sh ./$f &" >> run_parallel.sh
  else
    echo "./cluster_init.sh ./$f &" >> run_parallel.sh
  fi
done
echo "wait" >> run_parallel.sh
echo "exit 0" >> run_parallel.sh

# parallel initialization
chmod +x run_parallel.sh
./run_parallel.sh
rm run_parallel.sh

# concatenate initialized output
cat sample/*/*.i.seg | perl -e '
	$i=0;

	while(<>){
		chomp; 
		@t=split(/ +/); 
		$n=$t[0]." ".$t[7]; 
 
		if(! exists($d{$n})) { 
			$d{$n}="S".$i;
			$i++;
		}
		print "$t[0] $t[1] $t[2] $t[3] $t[4] $t[5] $t[6] ".$d{$n}."\n";
	}'> sample/samples.seg

# re-clustering based on the samples
java -Xmx12G -classpath \
src/LIUM_SpkDiarization-8.4.1.jar fr.lium.spkDiarization.programs.MClust \
 --help --fInputMask=sample/%s.wav --fInputDesc=$fDescCLR \
--sInputMask=sample/samples.seg --sOutputMask=sample/%s.seg \
--cMethod=ce --cThr=1.7 --tInputMask="src/ubm.gmm" \
--emCtrl=1,5,0.01 --sTop=5,"src/ubm.gmm" cross

#################################################################
# Re-write global cluster labels to original segmentation       #
#################################################################
rm -f data/*/*.final.seg
python assign_clusters.py sample/cross.seg


################################################################
# Train speaker model with MAP                                 #
################################################################
# wavok és globális szegmentálások összefűzése
rm -f wav/speaker.wav
rm -f data/speaker.seg
for f in wav/*.wav; do
 fname=`echo $f | rev | cut -f2- -d'.' | cut -f1 -d'/' | rev`
 python concat_seg.py data/${fname}/${fname}
 if [ -f wav/speaker.wav ]; then
  sox wav/speaker.wav $f wav/tmp.wav
  mv wav/tmp.wav wav/speaker.wav
 else
  sox $f wav/speaker.wav
 fi
done

# copy the UBM for each speaker
java -Xmx2024m -cp src/LIUM_SpkDiarization-8.4.1.jar fr.lium.spkDiarization.programs.MTrainInit --help --sInputMask=data/%s.seg --fInputMask=wav/%s.wav --fInputDesc="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --emInitMethod=copy --tInputMask=src/ubm.gmm --tOutputMask=data/%s.init.gmm speaker

# train (MAP adaptation, mean only) of each speaker, the diarization file describes the training data of each speaker.
java -Xmx2024m -cp src/LIUM_SpkDiarization-8.4.1.jar fr.lium.spkDiarization.programs.MTrainMAP --help --sInputMask=data/%s.seg --fInputMask=wav/%s.wav --fInputDesc="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --tInputMask=data/%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=data/%s.gmm speaker

#############################################################
# Speaker recognition                                       #
#############################################################

mkdir -p test_data
# init
echo "#!/bin/bash" >> run_parallel.sh # control parallelization
# speeding up by running processes parallelly
c=0
for f in test/*.wav; do
  ((c++))
  if [ $c -gt $nj ]; then
    c=0
    echo "wait" >> run_parallel.sh
    echo "./cluster_init_test.sh ./$f &" >> run_parallel.sh
  else
    echo "./cluster_init_test.sh ./$f &" >> run_parallel.sh
  fi
done
echo "wait" >> run_parallel.sh
echo "exit 0" >> run_parallel.sh

# parallel initialization
chmod +x run_parallel.sh
./run_parallel.sh
rm run_parallel.sh

for f in test/*.wav; do
 testShow=`echo $f | rev | cut -f2- -d'.' | cut -f1 -d'/' | rev`
 java -Xmx2G -Xms2G -cp src/LIUM_SpkDiarization-8.4.1.jar  fr.lium.spkDiarization.programs.Identification --sInputMask=test_data/${testShow}/%s.i.seg --help --fInputMask=test/%s.wav  --sOutputMask=test_data/${testShow}/%s.ident.seg --fInputDesc="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4" --tInputMask=data/speaker.gmm --sTop=5,src/ubm.gmm  --sSetLabel=add $testShow
done






