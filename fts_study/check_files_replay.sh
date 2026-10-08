
# list of files
############################



#FILENAME="fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.dntest2001.txt"  
#SUBDIR="fd_hd_anu"

#FILENAME="fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.dntest2001.txt"  
#SUBDIR="fd_hd_marley"

#FILENAME="fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt"  
#SUBDIR="fd_vd_anu"

#FILENAME="fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt"  
#SUBDIR="fd_vd_nu"

FILENAME="ndlar_2x2_charge_raw_run1_prod_f_official.dntest2001.txt"
SUBDIR="ndlar_2x2"


REPLAY_DIR="/exp/dune/app/users/twalton/DiskStorageRDAnalysis"
DIR=${REPLAY_DIR}/jobsub_workspace/replay_workspace/test_system_text_files/${FILENAME}

echo -e "Directory [$DIR]"

PNFS_DIRS="/pnfs/dune/scratch/users/twalton/ReplayFiles/${SUBDIR}"
RECOVER_FILENAME=${FILENAME/dntest2001/recovery.dntest2001}

counter=0

while IFS= read -r txt_file; do
    ((counter++)) 

    processed=0

    for json_dir in ${PNFS_DIRS}/*; do
        if grep -rq ${txt_file} ${json_dir}; then
           echo -e "[$counter] File has been processed [${txt_file}]"
           processed=1
           break
        fi
    done

    if (( processed == 0 )); then
       echo -e "${txt_file}" >> ${RECOVER_FILENAME}
       echo -e "[$counter] File has not been processed [${txt_file}]"
    fi

done < ${DIR}


words=$(wc -l ${RECOVER_FILENAME} | cut -d" " -f1)
echo -e "The dataset [$FILENAME] has [$words] recovery files\n\n"


