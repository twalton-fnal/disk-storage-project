#!/usr/bin/env python3
"""Submit a job to an FTS3 server directly using the REST API using tokens"""

from __future__ import annotations

import argparse
from typing import Any

import httpx

TEMPLATE = {
    "params": {
        "overwrite": True,
        "overwrite_on_retry": False,
        "overwrite_when_only_on_disk": False,
        "overwrite_hop": False,
        "reuse": False,
        "job_metadata": None,
        "gridftp": None,
        "spacetoken": None,
        "source_spacetoken": None,
        "verify_checksum": "y",
        "copy_pin_lifetime": -1,
        "bring_online": -1,
        "dst_file_report": False,
        "archive_timeout": -1,
        "timeout": None,
        "fail_nearline": False,
        "retry": 2,
        "multihop": False,
        "credential": None,
        "nostreams": None,
        "s3alternate": False,
        "target_qos": None,
        "ipv4": False,
        "ipv6": False,
        "buffer_size": None,
        "strict_copy": False,
        "disable_cleanup": False,
        "unmanaged_tokens": True,                # <- ADD THIS
    },
    "files": [],
}


def make_file(
    src_url: str,
    dst_url: str,
    src_token: str,
    dst_token: str,
    adler32: str | None,
):
    return {
        "sources": [src_url],
        "destinations": [dst_url],
        "source_tokens": [src_token],
        "destination_tokens": [dst_token],
        "checksum": ("adler32:" + adler32) if adler32 else "adler32",
        "filesize": None,
        "activity": None,
        "scitag": None,
        "metadata": None,
        "staging_metadata": None,
        "archive_metadata": None,
    }


def submit(ftshost: str, request: dict[str, Any], fts_token: str):
    print( f"{ftshost}:8446/jobs" )

    res = httpx.post(
        url=f"{ftshost}:8446/jobs",
        json=request,
        headers={
            "Authorization": f"Bearer {fts_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        verify=False,
    )
    print(f"Submitted request, response status: {res.status_code}")
    job_id: str = res.json()["job_id"]
    print(f"Job id: {ftshost}:8449/fts3/ftsmon/#/job/{job_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ftshost",
        help="FTS3 server to submit to",
        required=True,
    )
    parser.add_argument(
        "--src-prefix",
        help="Prefix for source URLs",
        required=True,
    )
    parser.add_argument(
        "--dst-prefix",
        help="Prefix for destination URLs",
        required=True,
    )
    parser.add_argument(
        "--lfnlist",
        help="File containing list of LFNs to transfer",
        required=True,
    )
    parser.add_argument(
        "--src-token-file",
        help="File containing token to access source storage",
        required=True,
    )
    parser.add_argument(
        "--dst-token-file",
        help="File containing token to access destination storage",
        required=True,
    )
    parser.add_argument(
        "--fts-token-file",
        help="File containing token to submit to FTS",
        required=True,
    )
    args = parser.parse_args()

    with open(args.src_token_file) as f:
        src_token = f.read().strip()
    with open(args.dst_token_file) as f:
        dst_token = f.read().strip()
    with open(args.fts_token_file) as f:
        fts_token = f.read().strip()

    with open(args.lfnlist) as f:
        lfns = [line.strip() for line in f]


    request = TEMPLATE.copy()
    chunk_size = 500
    max_files = len(lfns)
    for i in range(0, max_files, chunk_size):
        print(i)
        for lfn in lfns[i : i + chunk_size]:
            request["files"].append(
                make_file(
                    src_url=f"{args.src_prefix}{lfn}",
                    dst_url=f"{args.dst_prefix}{lfn}",
                    src_token=src_token,
                    dst_token=dst_token,
                    adler32=None,
                )
            )
        print (len(request["files"])) 
        submit(args.ftshost, request, fts_token)
        request["files"] = []
    
