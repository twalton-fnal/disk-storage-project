#!/usr/bin/env python3


import argparse
import os
import shutil
from pathlib import Path
import sys

#environment variables
PWD = str(os.environ.get('PWD'))
USER = str(os.environ.get('USER'))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a large list‑of‑files text file into batches."
    )
    parser.add_argument(
        "--filename",
        default="fardet_hd_marley_mc_detsim_dune10kt_apa1x2x2.dtntest2001.txt",
        help="Name of the input text file which contains all the data that should be on the dtntest node.",
    )
    parser.add_argument(
        "--recovery",
        type=int,
        choices=[0, 1],
        default=0,
        help="If 1, replace the first occurrence of 'dtntest' with "
             "'recovery.dtntest' in the filename (default: %(default)s).",
    )
    parser.add_argument(
        "--nfiles-per-job",
        type=int,
        default=5,
        help="How many files to process per job (default: %(default)s).",
    )
    return parser.parse_args()


def safe_mkdir(path: Path) -> None:
    """Create *path* if it does not exist; otherwise leave it untouched."""
    if not path.is_dir():
        path.mkdir(parents=True, exist_ok=True)


def clean_output_dir(outdir: Path) -> None:
    """Remove any ``*.txt`` files that may already be in *outdir*."""
    if outdir.is_dir():
        for txt_file in outdir.glob("*.txt"):
            txt_file.unlink()
    else:
        outdir.mkdir(parents=True, exist_ok=True)


def main() -> None:
    args = parse_args()

    # ------------------------------------------------------------------
    # Apply the “recovery” transformation if requested
    # ------------------------------------------------------------------
    filename = args.filename
    if args.recovery == 1:
        filename = filename.replace("dtntest", "recovery.dtntest", 1)

    # ------------------------------------------------------------------
    # Derive paths / base name
    # ------------------------------------------------------------------
    base_dir = "%s" % (PWD.replace("fts_study","")) 

    top_dir     = Path(base_dir).resolve()
    base_subdir = filename.split(".", 1)[0]                     
    outdir      = top_dir/"jobsub_workspace"/"replay_workspace"/"files_on_test_system"/base_subdir

    safe_mkdir(outdir)
    clean_output_dir(outdir)

    infile = top_dir/"jobsub_workspace"/"replay_workspace"/"test_system_text_files"/filename
    if not infile.is_file():
        sys.exit(f"The input file is not found: {infile}")

    # ------------------------------------------------------------------
    # Split the input file
    # ------------------------------------------------------------------
    batch_size = args.nfiles_per_job
    file_counter = 1
    line_counter = 0
    batch_path = None
    batch_handle = None

    # Helper to close the previous batch (if any) and make it executable
    def close_batch() -> None:
        nonlocal batch_handle, batch_path
        if batch_handle:
            batch_handle.close()
            os.chmod(batch_path, 0o755)
            print(f"\tCreated batch: {batch_path}")
            batch_handle = None
            batch_path = None

    with infile.open("r") as src:
        for line in src:
            line = line.rstrip("\n")
            if line_counter == 0:
                # start a new batch file
                did = f"{file_counter:06d}"
                batch_path = outdir / f"{base_subdir}_{did}.txt"
                batch_handle = batch_path.open("w")
            batch_handle.write(line + "\n")
            line_counter += 1

            # If the batch is full, close it and reset counters
            if line_counter >= batch_size:
                close_batch()
                file_counter += 1
                line_counter = 0

    # Close any partially‑filled final batch
    close_batch()

    # ------------------------------------------------------------------
    # Final user feedback
    # ------------------------------------------------------------------
    print("\nCompleted creating the batch file lists.")
    print("Check the directory for your files:")
    print(f"\t[{outdir}]\n")


if __name__ == "__main__":
    main()
