#!/usr/bin/env python3


import argparse
import os
from pathlib import Path
import sys

#environment variables
PWD = str(os.environ.get('PWD'))
USER = str(os.environ.get('USER'))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Identify files that have NOT been processed and write them to a recovery list."
    )
    p.add_argument(
        "--filename",
        default="ndlar_2x2_charge_raw_run1_prod_f_official.dtntest2001.txt",
        help="Name of the input list file (default: %(default)s).",
    )
    p.add_argument(
        "--json-dir-base",
        default="/pnfs/dune/scratch/users/%s/ReplayFiles" % USER,
        help="The top directory of the output JSON files from the replay submission (default: %(default)s).",
    )
    return p.parse_args()



def find_in_directory(search_str: str, directory: Path) -> bool:
    if not directory.is_dir():
        return False

    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        try:
            with entry.open("r", errors="ignore") as fh:
                for line in fh:
                    if search_str in line:
                        return True
        except Exception:
            continue
    return False



def main() -> None:
    args = parse_args()

    input_file = "%s/replay_workspace/test_system_text_files/%s" % (PWD.replace("fts_study","jobsub_workspace"),args.filename)
    input_file_path  = Path(input_dir).resolve()

    if not input_file_path.is_file():
        sys.exit(f"nput list not found: {input_path}")

    subdir = ""
    if args.filename.find("fardet_hd_antineutrino_mc_reco_dune10kt_apa1x2x6") != -1: 
       subdir = "fd_hd_anu"
    elif args.filename.find("fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2") != -1: 
       subdir = "fd_hd_marley"
    elif args.filename.find("fardet_vd_antineutrino_mc_reco_dune10kt_apa1x8x6") != -1:
       subdir = "fd_vd_anu"
    elif args.filename.find("fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6") != -1:
       subdir = "fd_vd_nu"
    elif args.filename.find("ndlar_2x2_charge_raw_run1_prod_f_official") != -1:
       subdir = "ndlar_2x2"
    else:
       sys.exit( "Unable to determine if the input filename is part of the workflow." )
    
    json_dirs = Path(args.json_dir_base) / subdir

    recovery_name = args.filename.replace("dtntest2001", "recovery.dtntest2001", 1)
    recovery_file_path = input_file.replace(args.filename,recovery_name)

    counter = 0
    missing = []          # type: list[str]

    with input_path.open("r") as src:
        for raw_line in src:
            txt_file = raw_line.strip()
            if not txt_file:          # skip blank lines
                continue

            counter += 1
            processed = False

            for json_dir in json_dirs.iterdir():
                if not json_dir.is_dir():
                    continue
                if find_in_directory(txt_file, json_dir):
                    processed = True
                    print(f"[{counter}] File has been processed [{txt_file}]")
                    break

            if not processed:
                missing.append(txt_file)


    recovery_path.write_text("\n".join(missing) + ("\n" if missing else ""))

    print(f"The dataset [{args.filename}] has [{len(missing)}] recovery files")
    print(f"Recovery list written to: {recovery_path}")


if __name__ == "__main__":
    main()
