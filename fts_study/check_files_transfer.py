#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path


#environment variables
PWD = str(os.environ.get('PWD'))
USER = str(os.environ.get('USER'))


def parse_args() -> argparse.Namespace:
    """Command‑line arguments – mirrors the Bash variables."""
    parser = argparse.ArgumentParser(
        description="Validate the file transfer to the dntest nodes."
    )

    parser.add_argument(
        "--filename",
        default="fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.dntest2001.txt",
        help="Name of the file that contains the list of files on the dntest nodes" (default: %(default)s)",
    )

    return parser.parse_args()


def run_gfal_ls(lfn: str, token: str) -> bool:
    env = os.environ.copy()
    env["BEARER_TOKEN"] = token.strip()

    proc = subprocess.run(
        [gfal-ls, "-l", lfn],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def main() -> None:
    args = parse_args()

    top_dir  = "%s/replay_workspace/" % (PWD.replace("fts_study","jobsub_workspace"))
    dir_path = Path(top_dir) / "test_system_text_files"
    out_dir  = Path(top_dir) / "missing_test_text_files"
    out_dir.mkdir(parents=True, exist_ok=True)

    output_name = out_dir / args.filename.replace(".txt", "miss.txt")
    if output_name.exists():
        output_name.unlink()     # remove any stale file

    uid  = os.getuid()
    try:
        token = Path(f"/run/user/{uid}/bt_u{uid}").read_text()
    except Exception as exc:
        sys.exit(f"Could not read token file [/run/user/{uid}/bt_u{uid}]: {exc}")


    input_file = dir_path / args.filename
    if not input_file.is_file():
        sys.exit(f"Input file not found: {input_file}")

    print(f"Started the validation check for dataset [{args.filename}]")

    failed = []          # type: list[str]
    count  = 0

    with input_file.open("r") as fh:
        for line in fh:
            lfn = line.strip()
            if not lfn:
                continue   

            success = run_gfal_ls(lfn, token)
            if success:
                if count % 100 == 0:
                    print(f"\t[{count}] gfal-ls success for file [{lfn}]")
            else:
                failed.append(lfn.lstrip(f"root://dtntest2001.fnal.gov://scratch/users/{USER}") )

            count += 1

    print("\nThe file list validation is completed.\n")

    output_name.write_text("\n".join(failed) + ("\n" if failed else ""))
    missing_cnt = len(failed)
    print(f"The dataset [{args.filename}] has [{missing_cnt}] missing files\n")


if __name__ == "__main__":
    main()
