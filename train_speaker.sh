#!/bin/bash

# copy the UBM for each speaker
java -Xmx2024m -cp src/LIUM_SpkDiarization.jar fr.lium.spkDiarization.programs.MTrainInit --help --sInputMask=$datadir/%s.final.seg --fInputMask=wav/%s.wav --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --emInitMethod=copy --tInputMask=src/ubm.gmm --tOutputMask=%s.init.gmm speakers

#train (MAP adaptation, mean only) of each speaker, the diarization file describes the training data of each speaker.
java -Xmx2024m -cp LIUM_SpkDiarization.jar fr.lium.spkDiarization.programs.MTrainMAP --help --sInputMask=%s.seg --fInputMask=%s.wav --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --tInputMask=%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=%s.gmm speakers

