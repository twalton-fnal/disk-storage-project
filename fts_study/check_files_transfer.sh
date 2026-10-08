
# list of files
############################


#FILENAME="fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.dntest2001.txt"  
#FILENAME="fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.dntest2001.txt"  
#FILENAME="fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt"  
FILENAME="fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt"  
#FILENAME="ndlar_2x2_charge_raw_run1_prod_f_official.dntest2001.txt"


REPLAY_DIR="/exp/dune/app/users/twalton/DiskStorageRDAnalysis"


DIR=${REPLAY_DIR}/jobsub_workspace/replay_workspace/test_system_text_files/
OUTDIR=${REPLAY_DIR}/jobsub_workspace/replay_workspace/missing_test_text_files/
if [ ! -d ${OUTDIR} ]; then
   mkdir -p ${OUTDIR}
fi

NAME="${OUTDIR}/${FILENAME/txt/miss.txt}"
if [ -f ${NAME} ]; then
   rm ${NAME}
fi

count=0
failed=()

echo -e "Started the validation check for dataset [$FILENAME]"

while IFS= read -r line; do 

      BEARER_TOKEN=$(< /run/user/43472/bt_u43472) gfal-ls -l $line  > /dev/null
      if [ $? -eq 0 ]; then
         if (( count % 100 == 0 )); then
            echo -e "\t[$count] gfal-ls success for file [$line]"
         fi
      else
         failed+=("$line")
      fi

      ((count++))
      done < ${DIR}/${FILENAME} 

echo -e "\nThe file list validation is completed."

printf "%s\n" "${failed[@]}" > $NAME
words=$(wc -l $NAME | cut -d" " -f1)

echo -e "The dataset [$FILENAME] has [$words] missing files\n\n"
