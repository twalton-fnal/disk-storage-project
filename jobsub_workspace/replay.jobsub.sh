#!/bin/sh

# get the site information
echo -e "The node working directory $PWD" | tee ${LOGFILE_NAME} 
echo -e "\t\thost is `/bin/hostname`" | tee ${LOGFILE_NAME} 
echo -e "\t\tthe current directory is $PWD" | tee ${LOGFILE_NAME}

# setup workspace
export WORKSPACE=${PWD}
echo -e "The workspace directory is ${WORKSPACE}" | tee ${LOGFILE_NAME}  

# Ask jobsub to retrieve the process id
echo -e "\n\nThe process is [${PROCESS}]." | tee ${LOGFILE_NAME}

NUM=$((PROCESS+START+1))
pfn=$(printf "%06d" "$NUM")

echo -e "\tThe job key physical file name (PFN) is [$pfn]" | tee ${LOGFILE_NAME}

# Check if the replay directory on CVMFS exists
echo -e "\tThe tar directory is [${INPUT_TAR_DIR_LOCAL}]" | tee ${LOGFILE_NAME}
export REPLAY_CONFIG_DIR=${INPUT_TAR_DIR_LOCAL}/jobsub_workspace
if [ ! -d ${REPLAY_CONFIG_DIR} ]; then
   echo -e "The directory [${REPLAY_CONFIG_DIR}] does not exist." | tee ${LOGFILE_NAME}
fi

export REPLAY_SCRIPT=${REPLAY_CONFIG_DIR}/replay.py
export REPLAY_ROOT_LOG=${REPLAY_CONFIG_DIR}/replay_workspace/xroot_log_files/${BASE_FILENAME}.xrd.txt 
export REPLAY_FILE_LIST=${REPLAY_CONFIG_DIR}/replay_workspace/files_on_test_system/${BASE_FILENAME}/${BASE_FILENAME}_${pfn}.txt

echo -e "\tThe replay script is [$REPLAY_SCRIPT]"| tee ${LOGFILE_NAME}
echo -e "\tThe replay xroot file is [$REPLAY_ROOT_LOG]" | tee ${LOGFILE_NAME}
echo -e "\tThe replay file list is [$REPLAY_FILE_LIST]" | tee ${LOGFILE_NAME}

# Setup replay workflow
export REPLAY_CONTAINER=/cvmfs/unpacked.cern.ch/registry.hub.docker.com/coffeateam/coffea-dask-almalinux9:2025.12.0-py3.12
echo -e "The replay container is [$REPLAY_CONTAINER]" | tee ${LOGFILE_NAME}


# get the posix library for running hdf5 files
if [ ${BASE_FILENAME} == *"ndlar_2x2_charge"* ]; then
   echo -e "\t\tGetting the posix libraries from spack."
   (
     source /cvmfs/dune.opensciencegrid.org/spack/v1.2.2/setup-env.sh
     LD_PRELOAD=$(spack find --format {prefix} xrootd)/lib64/libXrdPosixPreload.so
     printf '%s\n' "$LD_PRELOAD" > hdf5.output.txt
   ) 
fi

# execute the workflow
apptainer exec \
     -B $(pwd) \
     -B /cvmfs \
     -B ${REPLAY_CONFIG_DIR}/dune.token \
     --env BASE=${BASE_FILENAME} \
     --env LOG=${LOGFILE_NAME} \
     --env REPLAY_SCRIPT=${REPLAY_SCRIPT} \
     --env REPLAY_ROOT_LOG=${REPLAY_ROOT_LOG} \
     --env REPLAY_FILE_LIST=${REPLAY_FILE_LIST} \
     "${REPLAY_CONTAINER}" \
     bash -c '
 
           echo "Started apptainer exec at: $(date)" | tee ${LOG}
        
           export BEARER_TOKEN_FILE=${REPLAY_CONFIG_DIR}/dune.token
           export BEARER_TOKEN=$(cat $BEARER_TOKEN_FILE)
        
           echo -e "The BEARER_TOKEN_FILE is [${BEARER_TOKEN_FILE}]" | tee ${LOG}
           echo -e "The BEARER_TOKEN is [$BEARER_TOKEN]" | tee ${LOG}
 
           #export X509_CERT_DIR=/cvmfs/oasis.opensciencegrid.org/mis/certificates  
           #echo -e "The certificates directory is [${X509_CERT_DIR}]"
 
           export XrdSecPROTOCOL=ztn,unix 
         
           if [ -f "${REPLAY_SCRIPT}" ]; then
              echo -e "The file exist [${REPLAY_SCRIPT}]" | tee ${LOG}
           fi
 
           if [ -f "${REPLAY_ROOT_LOG}" ]; then
              echo -e "The file exist [${REPLAY_ROOT_LOG}]" | tee ${LOG}
           fi
 
           if [ -f "${REPLAY_FILE_LIST}" ]; then
              echo -e "The file exist [${REPLAY_FILE_LIST}]" | tee ${LOG}
           fi
 

           if [ ${BASE} == *"ndlar_2x2_charge"* ]; then
              IFS= read -r -d '' LD_PRELOAD < hdf5.output.txt
              echo -e "The posix lib exist [${LD_PRELOAD}]" | tee ${LOG}
           fi
 
           echo -e "Running the command [python ${REPLAY_SCRIPT} -i ${REPLAY_ROOT_LOG} -r ${REPLAY_FILE_LIST} --workers 50]\n\n" | tee ${LOG}
           python ${REPLAY_SCRIPT} -d -i ${REPLAY_ROOT_LOG} -r ${REPLAY_FILE_LIST} --workers 50
 
           echo -e "Finished apptainer exec at: $(date)" | tee ${LOG}
      '


# check the output files
echo "Listing current directory: $( pwd )" | tee ${LOGFILE_NAME}
ls -lha *  
echo -e "\n\n" | tee ${LOG}


# setup dune spack
source /cvmfs/dune.opensciencegrid.org/spack/setup-env.sh
spack env activate dune-prototype

# copy files to directory
echo "Copying files to directory [$OUTPUT_DIR]" | tee ${LOGFILE_NAME}

if ls *.log >/dev/null 2>&1; then
   ifdh cp -D *.log  ${OUTPUT_DIR}/ 
fi

if ls *.json >/dev/null 2>&1; then
   ifdh cp -D *.json  ${OUTPUT_DIR}/ 
fi


echo -e "Completed the submission" | tee ${LOGFILE_NAME}



