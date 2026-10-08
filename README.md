# DUNE Workflow Instructions 

> This README provides step-by-step instructions for testing DUNE data read and write operations across various disk technologies.
> Read and write operations are performed using XRootD.
> These instructions do not cover generating an XRootD file for each DUNE dataset.
> This workflow includes pre-generated DUNE datasets, but additional datasets can be added. For each new dataset, the user must generate an XRootD file containing the read results produced by executing the dataset's file in the appropriate workflow.

## Dataset Names
| Name | Abbreviation |
| :--- | :--- |
| <small>fardet-hd:fardet-hd__fd_mc_2023a_reco2__full-reconstructed__v09_81_00d02__standard_reco2_dune10kt_anu_1x2x6__prodgenie_anutau_dune10kt_1x2x6__out1__v1_official</small> | fd_hd_anu |
| <small>fardet-hd:fardet-hd__trg_mc_2025a__detector-simulated__v10_06_00d01__detsim_dune10kt_1x2x2_notpcsigproc__prodmarley_nue_flat_es_dune10kt_1x2x2__out1__v1_official</small> | fd_hd_marley |
| <small>fardet-vd:fardet-vd__fd_mc_2023a_reco2__full-reconstructed__v09_81_00d02__reco2_dunevd10kt_anu_1x8x6_3view_30deg_geov3__prodgenie_anu_numu2nue_nue2nutau_dunevd10kt_1x8x6_3view_30deg__out1__v1_official</small> | fd_vd_anu |
| <small>fardet-vdz:fardet-vd__fd_mc_2023a_reco2__full-reconstructed__v09_81_00d02__reco2_dunevd10kt_nu_1x8x6_3view_30deg_geov3__prodgenie_nu_dunevd10kt_1x8x6_3view_30deg__out1__v1_official</small> | fd_vd_nu |
| neardet-2x2-lar-charge:ndlar_2x2_charge_raw_run1_prod_f_official | ndlar_2x2 |

## Writing Data to dntest Nodes
> We use the FTS script provided by the disk storage group.

1. Checkout repository
   1. mkdir <fts_workspace>
   2. cd <fts_workspace>
   3. git clone https://github.com/twalton-fnal/disk-storage-project.git
2. Generate tokens
   1. htgettoken -i dune-test -a htvaultprod.fnal.gov -r admin
   2. cp /run/user/43472/bt_u43472 <fts_workspace>/disk-storage-project/fts_study/admin-test.token
   3. htdestroytoken
   4. htgettoken -i dune -a htvaultprod.fnal.gov -r interactive
   5. cp /run/user/43472/bt_u43472 <fts_workspace>/disk-storage-project/fts_study/user-src.dst.token
3. Setup the workspace
   1. Setup the replay container
      - source <fts_workspace>/disk-storage-project/setup_replay.sh
   2. Create the Python virtual environment
      1. cd <fts_workspace>
      2. python -m venv transfer_files.venv
      3. source transfer_files.venv/bin/activate
      4. pip install httpx
4. Write data to dntest nodes
   1. cd <fts_workspace>/disk-storage-project
   2. python test_submit_fts.py --filename=<input_filename>
      * Available filenames
        * fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.txt
        * fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.txt
        * fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.txt
        * fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.txt  
        * ndlar_2x2_charge_raw_run1_prod_f_official.txt
   3. deactivate 
   4. exit
5. Check data transfer to dntest node
   1. cd <fts_workspace>/disk-storage-project
   2. python check_files_transfer.py --filename=<input_filename>
      * Available filenames
        * fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6.dntest2001.txt
        * fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.dntest2001.txt
        * fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt
        * fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt
        * ndlar_2x2_charge_raw_run1_prod_f_official.dntest2001.txt
      > Files that failed the write process are stored as text files in the directory
      > <fts_workspace>/disk-storage-project/jobsub_workspace/missing_test_text_files.
6. (Optional) Recovery, write missed files to dntest nodes
   1. python test_submit_fts.py --filename=<input_filename> --recovery
      > Redo the steps 4, 5 and 6 until all files are on disk. 
