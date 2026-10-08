
# list of files
############################


#FILENAME="fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.txt"  
FILENAME="fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.txt"  
#FILENAME="fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.txt"  
#FILENAME="fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.txt"  
#FILENAME="ndlar_2x2_charge_raw_run1_prod_f_official.txt"


REPLAY_DIR="/exp/dune/app/users/twalton/DiskStorageRDAnalysis"


DIR=${REPLAY_DIR}/jobsub_workspace/replay_workspace/fnal_disk_text_files/ 
OUTDIR=${REPLAY_DIR}/jobsub_workspace/replay_workspace/test_system_text_files/

DTN="dtntest2002" #dtntest2001

while IFS= read -r line; do 
      modified_line="${line/root:\/\/fndcadoor.fnal.gov:1094\/pnfs\/fnal.gov\/usr\//root:\/\/dtntest2001.fnal.gov:\/\/scratch\/users\/${USER}\/}" 
      echo "$modified_line" 
      done < ${DIR}/${FILENAME} > "${OUTDIR}/${FILENAME/txt/dntest2001.txt}"


echo -e "\nThe file list generation is completed."
echo -e "Please check that the URLs for files on the test system are correct."
echo -e "\t[${OUTDIR}/${FILENAME/txt/dntest2001.txt}]\n\n"

