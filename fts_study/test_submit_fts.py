#!/usr/bin/env python3

import argparse
import subprocess
import os, sys
from pathlib import Path

#environment variables
PWD = str(os.environ.get('PWD'))
USER = str(os.environ.get('USER'))


def build_command(
    ftshost: str,
    src_prefix: str,
    dst_prefix: str,
    lfnlist: Path,
    src_token_file: str,
    dst_token_file: str,
    fts_token_file: str,
) -> list:
    """
    Assemble the command line that will be executed.

    Returns
    -------
    list
        The argument list suitable for ``subprocess.run``.
    """
    return [
        sys.executable,               # use the same Python interpreter that runs this script
        "fts_token_job.py",
        "--ftshost", ftshost,
        "--src-prefix", src_prefix,
        "--dst-prefix", dst_prefix,
        "--lfnlist", str(lfnlist),
        "--src-token-file", src_token_file,
        "--dst-token-file", dst_token_file,
        "--fts-token-file", fts_token_file,
    ]


def main() -> None:

    text_file_dir = "%s/replay_workspace/modified_fnal_disk_text_files/" % (PWD.replace("fts_study","jobsub_workspace"))
  

    parser = argparse.ArgumentParser(
        description="Wrap the fts_token_job.py call with easy‑to‑use arguments."
    )

    parser.add_argument(
        "--user",
        default="twalton",
        help="Username that appears in the destination davs URL. (default: %(default)s)",
    )
    parser.add_argument(
        "--file-dir",
        default="%s" % text_file_dir,
        help="The file directory that contains the dataset file lists. (default: %(default)s)",
    )
    parser.add_argument(
        "--filename",
        default="fardet_vd_neutrino_mc_reco_dune10kt_apa1x8x6.txt",
        help="Name of the file that holds the list of logical file names. (default: %(default)s)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the constructed command but do NOT execute it.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the command before running it.",
    )

    args = parser.parse_args()


    # ----------------------------------------------------------------------
    # Build the full path to the LFN list file
    # ----------------------------------------------------------------------
    lfnlist_path = Path(args.file_dir) / args.filename
    if not lfnlist_path.is_file():
        parser.error(f"FNAL list file not found: {lfnlist_path}")

    # ----------------------------------------------------------------------
    # Assemble the final command
    # ----------------------------------------------------------------------
    cmd = build_command(
        ftshost="https://fts3-dev.fnal.gov",
        src_prefix="davs://fndcadoor.fnal.gov:2880",
        dst_prefix=f"davs://dtntest2001.fnal.gov:9000/scratch/users/{USER}", 
        lfnlist=lfnlist_path,
        src_token_file="user-src.dst.token",
        dst_token_file="user-src.dst.token",
        fts_token_file="admin-test.token",
    )

    # ----------------------------------------------------------------------
    # Run (or just display) the command
    # ----------------------------------------------------------------------
    print("Running the command:")
    print(" ".join(cmd))

    if args.dry_run:
        sys.exit(0)

    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(result.stdout)
    except subprocess.CalledProcessError as exc:
        print(f"Error: fts_token_job.py exited with status {exc.returncode}", file=sys.stderr)
        print(exc.output, file=sys.stderr)
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
