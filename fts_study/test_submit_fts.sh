#!/usr/bin/env bash
set -e



# FAR DETECTOR DATASETS
#------------------------------------------------------
# EOS - fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.txt, 5549, 16.8 TB 17299
# EOS - fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.txt, 17299, 35.7 TB
# EOS - fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.txt, 15542, 26.0 TB  
# EOS - fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.txt, 21051, 19.9 TB 


# NEAR DETECTOR DATASETS
#-------------------------------------------
# EOS - ndlar_2x2_charge_raw_run1_prod_f_official.txt, 517 files, 241 GB

USER=twalton
BASE_DIR="/exp/dune/app/users/twalton/DiskStorageRDAnalysis/jobsub_workspace/replay_workspace/modified_fnal_disk_text_files/"

#FILENAME="fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.txt"
#FILENAME="fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.txt"
FILENAME="fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.txt"

python3 fts_token_job.py --ftshost https://fts3-dev.fnal.gov \
  --src-prefix davs://fndcadoor.fnal.gov:2880 \
  --dst-prefix davs://dtntest2001.fnal.gov:9000/scratch/users/${USER} \
  --lfnlist ${BASE_DIR}/${FILENAME} \
  --src-token-file user-src.dst.token --dst-token-file user-src.dst.token --fts-token-file admin-test.token 
