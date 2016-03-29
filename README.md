# Unsupervised Speaker Clustering & Speaker Recognition 
## Scripts created by Adam Varga, 2015-2016

This toolkit is based on the [LIUM Speaker Diarization Toolkit](http://www-lium.univ-lemans.fr/diarization/doku.php/download). It can be used for
performing unsupervised speaker clustering in sound files based on the diarization output, where speakers with similar voice characteristics will to the same cluster.
This can be useful to perform speaker adaptive training of acoustic models for speech recognition when the identity of the speakers is unknown.

The script additionally trains a Gaussian Mixture Model for speaker recognition, and classifies speakers in the test files with regard to 
the speaker clusters.

1. Requirements for running the scripts
  * Java JDK (1.6+)
  * bash
  * sox
  * Python 2.7
  * LIUM SpeakerDiarization Toolkit

2. Using the toolkit
   WAV files for training and testing should be placed in the folders `wav/` and `test/`, respectively. Executing `run.sh` performs the whole process described
   above.
   
3. List of files
   * `src/` - LIUM Toolkit and pretrained models
   * `wav/` - put training files here
   * `test/` - put test files here
   * `assign_clusters.py` (1.0 kB) - assign global clusters to individual files
   * `cluster_individual.sh` (5.8 kB) - cluster individual files (based on the [LIUM Wiki](http://www-lium.univ-lemans.fr/diarization/doku.php/welcome))
   * `cluster_init.sh` (2.0 kB) - initialize clusters (based on the [LIUM Wiki](http://www-lium.univ-lemans.fr/diarization/doku.php/welcome))
   * `concat_seg.py` (2.0 kB) - concatenates segmentation files with necessary offset
   * `get_clust.py` (726 B) - get individual cluster IDs based on cluster files
   * `run.sh` (4.1 kB) - run the full clustering, training and testing
   * `segment_egs.py` (1.7 kB) - get samples for each cluster
   * `train_speaker.sh` (1.0 kB) - train speaker GMM with MAP
   
4. List of output folders and files
   * `data/` - clustering data files produced by LIUM
   * `sample/` - samples of the original sound files corresponding to clusters 
     * `$ID/` - data folders corresponding to samples, their content is similar to that of the `data/` folder
	 * `samples.seg` - concatenated and modified sample cluster IDs (modified to avoid overlap)
	 * `cross.seg` - result of global re-clustering