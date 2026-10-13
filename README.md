# DUNE Workflow Instructions 

> This README provides step-by-step instructions for testing DUNE data read and write operations across various disk technologies.
> Read and write operations are performed using XRootD.
> These instructions do not cover generating an XRootD log file for each DUNE dataset or the list containing the files in each dataset.
> The XRootD log files and list of DUNE data files are included in the jobsub_workspace/replay_workspace directory.
> This workflow includes pre-generated DUNE datasets, but additional datasets can be added. For each new dataset, the user must generate an XRootD file containing the read results by running the dataset file in the appropriate workflow.
>
> This workflow must be carried out on a DUNE gpvm.

## Dataset Names
| Name | Abbreviation |
| :--- | :--- |
| <small>fardet-hd:fardet-hd__fd_mc_2023a_reco2__full-reconstructed__v09_81_00d02__standard_reco2_dune10kt_anu_1x2x6__prodgenie_anutau_dune10kt_1x2x6__out1__v1_official</small> | fd_hd_anu |
| <small>fardet-hd:fardet-hd__trg_mc_2025a__detector-simulated__v10_06_00d01__detsim_dune10kt_1x2x2_notpcsigproc__prodmarley_nue_flat_es_dune10kt_1x2x2__out1__v1_official</small> | fd_hd_marley |
| <small>fardet-vd:fardet-vd__fd_mc_2023a_reco2__full-reconstructed__v09_81_00d02__reco2_dunevd10kt_anu_1x8x6_3view_30deg_geov3__prodgenie_anu_numu2nue_nue2nutau_dunevd10kt_1x8x6_3view_30deg__out1__v1_official</small> | fd_vd_anu |
| <small>fardet-vdz:fardet-vd__fd_mc_2023a_reco2__full-reconstructed__v09_81_00d02__reco2_dunevd10kt_nu_1x8x6_3view_30deg_geov3__prodgenie_nu_dunevd10kt_1x8x6_3view_30deg__out1__v1_official</small> | fd_vd_nu |
| neardet-2x2-lar-charge:ndlar_2x2_charge_raw_run1_prod_f_official | ndlar_2x2 |

## Writing Data to dtntest Nodes
> To transfer data, we use the FTS script, __*fts_token_job.py*__, provided by the disk storage group.
> Below are the step-by-step instructions for transferring DUNE data from disk to the DTN test nodes.

1. Check out the repository
   1. mkdir <disk_project_workspace>
   2. cd <disk_project_workspace>
   3. git clone -b develop https://github.com/twalton-fnal/disk-storage-project.git
2. Generate tokens
   1. htgettoken -i dune-test -a htvaultprod.fnal.gov -r admin
   2. cp /run/user/43472/bt_u43472 <disk_project_workspace>/disk-storage-project/fts_study/admin-test.token
   3. htdestroytoken
   4. htgettoken -i dune -a htvaultprod.fnal.gov -r interactive
   5. cp /run/user/43472/bt_u43472 <disk_project_workspace>/disk-storage-project/fts_study/user-src.dst.token
3. Set up the workspace
   1. Set up the replay container
      - source <disk_project_workspace>/disk-storage-project/setup_replay.sh
   2. Create the Python virtual environment
      1. cd <disk_project_workspace>
      2. python -m venv transfer_files.venv
      3. source transfer_files.venv/bin/activate
      4. pip install httpx (Do this only once)
   3. Do not exit the Python virtual environment
4. Write data to dtntest nodes
   1. Confirm the directory
      * cd <disk_project_workspace>/disk-storage-project
   2. Run the Python wrapper script for **fts_token_job.py**
      * python test_submit_fts.py --filename=<input_filename>
        * Available filenames
          * fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.txt
          * fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.txt
          * fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.txt
          * fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.txt  
          * ndlar_2x2_charge_raw_run1_prod_f_official.txt
   3. Exit the Python virtual environment and container
      1. deactivate 
      2. exit
5. Check the data transfer to the dtntest node
   1. cd <disk_project_workspace>/disk-storage-project
   2. python check_files_transfer.py --filename=<input_filename>
      * Available filenames
        * fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.dntest2001.txt
        * fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.dntest2001.txt
        * fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt
        * fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt
        * ndlar_2x2_charge_raw_run1_prod_f_official.dntest2001.txt
      > Files that failed the write process are stored as text files in the directory
      > <disk_project_workspace>/disk-storage-project/jobsub_workspace/missing_test_text_files.
7. (Optional) Recovery: write missed files to dtntest nodes
   1. python test_submit_fts.py --filename=<input_filename> --recovery
      > Redo steps 4, 5, and 6 until all files are on disk.

## Reading Data from dtntest Nodes
> We use the replay script, ***replay.py*** provided by the storage group.
> Additionally, the Fermilab workflow management batch system, jobsub, is used to submit the replay read jobs to the grid.
> Below are the step-by-step instructions for the batch submission of replay jobs to the grid. 

1. Create a batch list of files for each job.
   1. cd <disk_project_workspace>/disk-storage-project/fts_study
   2. python make_batch_files.py --filename=\<filename\> --nfiles-per-job=\<N\>
      * Available filenames
        * fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.dtntest2001.txt
        * fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.dtntest2001.txt
        * fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.dtntest2001.txt
        * fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.dtntest2001.txt
        * ndlar_2x2_charge_raw_run1_prod_f_official.dtntest2001.txt
        * fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.dtntest2002.txt
2. Submit the jobs to the grid
   1. cd <disk_project_workspace>/disk-storage-project/jobsub_workspace
   2. python replay.submit.jobsub.py --detector=**DETECTOR** --nfiles=**NFILES**
      > See the help menu for the available **DETECTOR**.
      > The output JSON files are located in your DUNE scratch area, /pnfs/dune/scratch/users/\<USER\>/ReplayFiles.
      > The parameter --outdir is used to change the default location.
      > Additionally, this script generates a token and stores it in a file in your local area.
      > The entire workspace is tarred into a file and uploaded to CVMFS. Therefore, the job has token access and the names of
      > the group of files to process for the given detector type.
      >
      > The jobs are monitored using *jobsub_q --user=\<USER\> -G dune*
3. Check the replay job submission.
   1. cd <disk_project_workspace>/disk-storage-project/fts_study
   2. 
