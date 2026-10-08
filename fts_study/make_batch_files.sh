#!/bin/bash


#---- list of files


RECOVERY=0
NFILES_PER_JOB=5
FILENAME=""

#--- dntest2001 files
#FILENAME="fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.dntest2001.txt"
#FILENAME="fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.dntest2001.txt"
#FILENAME="fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt"
#FILENAME="fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt"
#FILENAME="ndlar_2x2_charge_raw_run1_prod_f_official.dntest2001.txt"


#---- dntest2002 files
FILENAME="fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.dntest2002.txt"


#####################################################

if (( RECOVERY == 1 )); then
   FILENAME=${FILENAME/dntest/recovery.dntest}
fi


TOP_DIR="/exp/dune/app/users/twalton/DiskStorageRDAnalysis/"
BASE=$(echo ${FILENAME} | cut -d "." -f 1)

OUTDIR=${TOP_DIR}/jobsub_workspace/replay_workspace/files_on_test_system/${BASE}
if [ ! -d "$OUTDIR" ]; then
   mkdir -p ${OUTDIR}
else 
  rm -f ${OUTDIR}/*.txt
fi


INFILE="${TOP_DIR}/jobsub_workspace/replay_workspace/test_system_text_files/${FILENAME}"

total_len_file_count=${NFILES_PER_JOB}
file_num=1
line_count=0

while IFS= read -r line; do

    printf -v DID "%06d" "$file_num"

    OUTFILE="${OUTDIR}/${BASE}_${DID}.txt"

    echo "$line" >> "$OUTFILE"
    ((line_count++))
    
    if [ $line_count -eq $total_len_file_count ]; then
        chmod 755 $OUTFILE
        line_count=0
        ((file_num++))
    fi

done < "$INFILE"

echo -e "\nCompleted created the batch file lists."
echo -e "Check the directory for your files."
echo -e "\t[$OUTDIR]\n\n"
