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
> 
