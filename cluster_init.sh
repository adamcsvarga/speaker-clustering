#!/bin/bash

PATH=$PATH:..:.

features=$1
#the MFCC corresponds to sphinx 12 MFCC + Energy
# sphinx=the mfcc was computed by the sphinx tools
# 1: static coefficients are present in the file
# 1: energy coefficient is present in the file
# 0: delta coefficients are not present in the file
# 0: delta energy coefficient is not present in the file
# 0: delta delta coefficients are not present in the file
# 0: delta delta energy coefficient is not present in the file
# 13: total size of a feature vector in the mfcc file
# 0:0:0: no feature normalization
fDesc="audio2sphinx,1:1:0:0:0:0,13,0:0:0"

#this variable is use in CLR/NCLR clustering and gender detection
#the MFCC corresponds to sphinx 12 MFCC + E
# sphinx=the mfcc is computed by sphinx tools
# 1: static coefficients are present in the file
# 3: energy coefficient is present in the file but will not be used
# 2: delta coefficients are not present in the file and will be computed on the fly
# 0: delta energy coefficient is not present in the file
# 0: delta delta coefficients are not present in the file
# 0: delta delta energy coefficient is not present in the file
# 13: size of a feature vector in the mfcc file
# 1:1:300:4: the MFCC are wrapped (feature warping using a sliding windows of 300 features),
#                   next the features are centered and reduced: mean and variance are computed by segment
fDescCLR="audio2sphinx,1:3:2:0:0:0,13,1:1:300:4"

show=`basename $1 .sph`
show=`basename $show .wav`

echo $show

#need JVM 1.6
java=java

datadir=sample/${show}

LOCALCLASSPATH=src/LIUM_SpkDiarization-8.4.1.jar

echo "#####################################################"
echo "#   $show"
echo "#####################################################"

mkdir ./$datadir >& /dev/null
echo $(date)

$java -Xmx1G -classpath "$LOCALCLASSPATH" fr.lium.spkDiarization.programs.MSegInit --fInputMask=$features --fInputDesc=$fDesc --sInputMask=$uem --sOutputMask=./$datadir/%s.i.seg  $show
