#!/usr/bin/env python3
"""
Python script to extract chunk sizes from xrootd log

Run in apptainer using: apptainer exec -B ${PWD}:/srv --pwd /srv /cvmfs/unpacked.cern.ch/registry.hub.docker.com/coffeateam/coffea-dask-almalinux9:2025.12.0-py3.12 /bin/bash

Command to run: python replay.py -i [name of xrootd logfile] -r [name of file with list of rootfiles] -n [enable random reads option] -s [size of random reads in bytes] -d [enable debug logging level for verbose outputs] -w [number of worker threads to use] -t [wait time between each read request] -u [duration of random reads script in seconds] -m [multiply read sizes by factor of 0.1]
"""

import argparse
import json
import logging
import os
import random
import re
import subprocess
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List
import psutil
from XRootD import client
from XRootD.client.flags import OpenFlags

# Arg parser
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-i", "--input", type=str, help="Input xrootd logfile with .txt")
parser.add_argument(
    "-r", "--rootfiles", type=str, help=".txt file with list of xrootd urls"
)
parser.add_argument(
    "-t", "--time", type=float, default=0, help="wait time between each read request"
)
parser.add_argument(
    "-n", "--random_read", action="store_true", help="enable random reads option"
)
parser.add_argument("-s", "--size", type=int, default=256000, help="size of random reads in bytes")

parser.add_argument(
    "-u",
    "--duration",
    type=int,
    default=60,
    help="duration of random reads script, default 60 seconds",
)
parser.add_argument(
    "-d",
    "--debug",
    action="store_true",
    help="Enable debug logging level for verbose outputs",
)

parser.add_argument("-m", "--reduce-size", action="store_true", help="Multiply read sizes by factor of 0.1")

parser.add_argument("-w", "--workers", type=int, default=50, help="Number of worker threads to use (default: 80)")

parser.add_argument("-j", "--jobs", type=int, default=1, help="Number of condor jobs in batch (default: 1)")

parser.add_argument("-o", "--job-id", type=int, default=0, help="Job ID for this condor job (default: 0)")

# Tokens
client_id = os.environ.get("TEST_CLIENT", "")
client_secret = os.environ.get("TEST_SECRET", "")

# set xrootd to prefer tokens, then unix
os.environ["XrdSecPROTOCOL"] = "ztn,unix"
os.environ["BEARER_TOKEN_FILE"] = "rtest.tkn"


# ---------------------------------------------------------------------------------------------------------------#
@dataclass
class Stats:
    read_mismatches: int = 0
    read_fails: int = 0
    read_errors: int = 0
    file_open_errors: int = 0
    open_error_reason: list = field(default_factory=list)
    total_bytes: int = 0
    read_requests: int = 0
    read_skips: int = 0
    bytes_skipped: int = 0
    total_read_time: float = 0.0
    start_time: str = ""
    end_time: str = ""
    duration: float = 0.0
    total_open_time: float = 0.0

    def __add__(self, other):
        return Stats(
            self.read_mismatches + other.read_mismatches,
            self.read_fails + other.read_fails,
            self.read_errors + other.read_errors,
            self.file_open_errors + other.file_open_errors,
            self.open_error_reason + other.open_error_reason,
            self.total_bytes + other.total_bytes,
            self.read_requests + other.read_requests,
            self.read_skips + other.read_skips,
            self.bytes_skipped + other.bytes_skipped,
            self.total_read_time + other.total_read_time,
            self.total_open_time + other.total_open_time,
        
        )
    def to_dict(self):
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration,
            "total_bytes_read": self.total_bytes,
            "total_read_time_seconds": self.total_read_time,
            "read_mismatches": self.read_mismatches,
            "read_fails": self.read_fails,
            "read_errors": self.read_errors,
            "file_open_errors": self.file_open_errors,
            "open_error_reason": self.open_error_reason,
            "read_requests": self.read_requests,
            "read_skips": self.read_skips,
            "read_bytes_skipped": self.bytes_skipped,
            "total_open_time_seconds": self.total_open_time,
        }


def check_sizes(chunks, offsets):
    stats = Stats()
    if len(chunks) != len(offsets):
        logging.debug("Chunk and offset length mismatch detected.")
        stats.read_mismatches += 1
    return stats


def check_status(status, reads):
    """Checks to make sure reads are successful and accurate"""
    stats = Stats()
    if not status.ok:
        stats.read_fails += 1
        return stats
    for size, buffer in reads:
        if size != len(buffer):
            stats.read_errors += 1
    return stats

class _DoNothingContext:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class BigReadLock:
    """A tool to serialize very large reads"""

    def __init__(self, threshold_bytes: int):
        self.threshold_bytes = threshold_bytes
        self.lock = threading.Lock()

    def maybe_acquire(self, num_bytes: int):
        """Return a locking context if we are over the limit, otherwise return a no-op context"""
        if num_bytes >= self.threshold_bytes:
            return self.lock
        else:
            return _DoNothingContext()


BIG_READ_LOCK = BigReadLock(threshold_bytes=20 * 1024 * 1024)  # 20 MiB


def replay_read(f, offsets, sizes, rootfile_size):
    """Performs a read on a rootfile at a specific chunk"""
    stats = Stats()
    # doing single read
    if isinstance(offsets, int):  # if offsets is not a vector (single read)
        if offsets + sizes > rootfile_size:
            logging.debug(
                f"Skipping chunksize {sizes} at offset {offsets} since it is greater than size of rootfile"
            )
            stats.read_skips += 1
            stats.bytes_skipped += sizes
            return stats
        # Doing single read
        status, response = f.read(int(offsets), int(sizes))
        reads = [(sizes, response)]
        #stats.total_bytes += len(response) if response else 0
        stats.total_bytes += sizes
        stats.read_requests += 1
        stats += check_status(status, reads)
        logging.debug(f"Successfully read chunksize {sizes} at offset {offsets}")
        return stats
    else:
        stats += check_sizes(sizes, offsets)

        # doing vector read
        vector_orig = list(
            zip(offsets, sizes)
        )  # Put offsets and chunksizes into correct format for vector read
        vector = [
            (o, s) for o, s in zip(offsets, sizes) if o + s <= rootfile_size
        ]  # filtering which ones are too big
        if vector_orig != vector:
            skipped_offsets = []
            skipped_chunks = []
            for o, s in zip(offsets, sizes):
                if o + s > rootfile_size:
                    skipped_offsets.append(o)
                    skipped_chunks.append(s)
                    stats.bytes_skipped += s
                    stats.read_skips += 1
            logging.debug(f"In vector {vector_orig}, skipped chunk(s) {skipped_chunks} at offset(s) {skipped_offsets}")
        if not vector:  # if vector is empty after filtering, skip the read
            logging.debug(
                f"Skipping chunksize {sizes} at offset {offsets} since it is greater than size of rootfile"
            )
            return stats

        total_bytes = sum(s for _, s in vector)
        with BIG_READ_LOCK.maybe_acquire(total_bytes):
            read_starttime = time.perf_counter() # start timer right before read
            status, response = f.vector_read(chunks=vector)
            stats.total_read_time += time.perf_counter() - read_starttime # end timer right after read
            reads = [
                (sizes, chunk.buffer)
                for (_, sizes), chunk in zip(vector, response.chunks)
            ]
            stats += check_status(status, reads)
            #stats.total_bytes += sum(len(buffer) for _, buffer in reads)
            stats.total_bytes += sum(sizes for sizes, _ in reads)
            del reads, response  # free memory
        stats.read_requests += 1
        logging.debug(
            f"Successfully read chunksizes {[s for _, s in vector]} at offsets {[o for o, _ in vector]}"
        )
        return stats


def replaylog(logfile, rootfile, sleep_times, reduce_size):
    """Perform a replay over one root file, gets offsets and chunksizes from log and runs replay_read"""
    stats = Stats()
    logging.debug(f"Performing replay over {rootfile}")
    logging.debug(f"Thread ID: {threading.get_ident()}")
    logging.debug(f"Active threads: {threading.active_count()}")

    time.sleep(random.expovariate(5.0))
    process = psutil.Process(os.getpid())
    logging.debug(f"Running on CPU: {process.cpu_num()}")
    raw_start_time = time.time()
    sleep_idx = 0
    # Open root file and do reads
    with open(logfile, "r") as infile:
        with client.File() as f:
            logging.debug(f"Opening {rootfile}...")
            open_starttime = time.perf_counter()
            status, _ = f.open(rootfile, OpenFlags.READ)  # open file for read only
            if not status.ok:
                stats.file_open_errors += 1
                error_msg = f"Code {status.code}: {status.message.strip()}"
                logging.error(f"Failed to open root file {rootfile}. Reason: {error_msg}")
                stats.open_error_reason.append(error_msg)
                return stats
            open_time = time.perf_counter() - open_starttime
            status, info = f.stat()
            rootfile_size = info.size
            for line in infile:
                if re.search(
                    r"kXR_readv\b.*with status:\s*\[SUCCESS\]\s*\.$", line
                ):  # if it's a vector read
                    matches = re.findall(
                        r"offset:\s*(\d+),\s*size:\s*(\d+)", line
                    )  # find offsets, chunksizes
                    offsets = [int(o) for o, s in matches]
                    chunksizes = [int(s) for o, s in matches]
                    if reduce_size:
                        chunksizes = [int(round(s * 0.1)) for s in chunksizes]
                    stats += replay_read(f, offsets, chunksizes, rootfile_size)
                    time.sleep(sleep_times[sleep_idx % len(sleep_times)])
                    sleep_idx += 1
                elif re.search(
                    r"kXR_read\b.*with status:\s*\[SUCCESS\]\s*\.$", line
                ):  # else is a single read
                    match = re.search(r"offset:\s*(\d+),\s*size:\s*(\d+)", line)
                    offset, size = map(int, match.groups())
                    if reduce_size:
                        size = int(round(size * 0.1))
                    stats += replay_read(f, offset, size, rootfile_size)
                    time.sleep(sleep_times[sleep_idx % len(sleep_times)])
                    sleep_idx += 1
    raw_end_time = time.time()
    local_tz=ZoneInfo("America/Chicago") ## set timezone to central time
    local_start_time = datetime.fromtimestamp(raw_start_time, tz=local_tz)
    local_end_time = datetime.fromtimestamp(raw_end_time, tz=local_tz)
    stats.start_time = local_start_time.strftime("%Y-%m-%d %H:%M:%S")
    stats.end_time = local_end_time.strftime("%Y-%m-%d %H:%M:%S")
    stats.duration = raw_end_time - raw_start_time
    stats.total_open_time = open_time
    logging.debug(f"Finished replay over {rootfile}")
    return stats


def randomreplaylog(logfile, rootfile, random_read_size, end_time):
    """Perform a replay over one root file, gets offsets from log and runs replay_read at a specified read size"""
    stats = Stats()
    raw_start_time = time.time()
    logging.info(f"Performing random replay over {rootfile}")
    logging.debug(f"Thread ID: {threading.get_ident()}")
    logging.debug(f"Active threads: {threading.active_count()}")
    process = psutil.Process(os.getpid())
    logging.debug(f"Running on CPU: {process.cpu_num()}")
    with client.File() as f:
        open_starttime = time.perf_counter()
        status, _ = f.open(rootfile, OpenFlags.READ)  # open file for read only
        if not status.ok:
            error_msg = f"Code {status.code}: {status.message.strip()}"
            logging.error(f"Failed to open root file {rootfile}. Reason: {error_msg}")
            stats.file_open_errors += 1
            stats.open_error_reason.append(error_msg)
            return stats
        open_time = time.perf_counter() - open_starttime
        status, info = f.stat()
        rootfile_size = info.size
        while time.time() < end_time:
            with open(logfile, "r") as infile:
                for line in infile:
                    if time.time() >= end_time:
                        logging.info(f"Reached end time for random replay over {rootfile}")
                        break
                    if re.search(r"kXR_readv\b.*with status:\s*\[SUCCESS\]\s*\.$", line):  # if it's a vector read
                        matches = re.findall(r"offset:\s*(\d+),\s*size:\s*(\d+)", line)  # find offsets, chunksizes
                        offsets = [int(o) for o, s in matches]
                        # use random read size if random read option is set
                        chunksizes = [random_read_size] * len(offsets)
                        stats += replay_read(f, offsets, chunksizes, rootfile_size)
                    elif re.search(
                        r"kXR_read\b.*with status:\s*\[SUCCESS\]\s*\.$", line
                    ):  # else is a single read
                        match = re.search(r"offset:\s*(\d+),\s*size:\s*(\d+)", line)
                        offset, size = map(int, match.groups())
                        size = random_read_size
                        stats += replay_read(f, offset, size, rootfile_size)
            return stats
    raw_end_time = time.time()
    local_tz = ZoneInfo("America/Chicago")
    local_start_time = datetime.fromtimestamp(raw_start_time, tz=local_tz)
    local_end_time = datetime.fromtimestamp(raw_end_time, tz=local_tz)
    stats.start_time = local_start_time.strftime("%Y-%m-%d %H:%M:%S")
    stats.end_time = local_end_time.strftime("%Y-%m-%d %H:%M:%S")
    stats.duration = raw_end_time - raw_start_time
    stats.total_open_time = open_time
    logging.debug(f"Finished random replay over {rootfile}")
    return stats


def monitor_system(stats_log):
    process = psutil.Process(os.getpid())

    psutil.cpu_percent(interval=None)  # prime CPU

    while True:
        cpu = psutil.cpu_percent(interval=0.5)

        mem = process.memory_info().rss  # bytes
        mem_percent = process.memory_percent()
        io = process.io_counters()
        read_bytes = io.read_bytes

        stats_log.append(
            {
                "cpu": cpu,
                "memory_bytes": mem,
                "memory_percent_total": mem_percent,
                "read_bytes": read_bytes,
                "timestamp": time.time(),
            }
        )


def duration_replay(logfile, filepaths, end_time, random_read_size):
    total_stats = Stats()
    raw_start_time = time.time()
    while time.time() < end_time:
        rootfile = random.choice(filepaths)
        stats = randomreplaylog(logfile, rootfile, random_read_size, end_time)
        total_stats += stats
    raw_end_time = time.time()
    local_tz = ZoneInfo("America/Chicago")
    local_start_time = datetime.fromtimestamp(raw_start_time, tz=local_tz)
    local_end_time = datetime.fromtimestamp(raw_end_time, tz=local_tz)
    total_stats.start_time = local_start_time.strftime("%Y-%m-%d %H:%M:%S")
    total_stats.end_time = local_end_time.strftime("%Y-%m-%d %H:%M:%S")
    total_stats.duration = raw_end_time - raw_start_time

    return total_stats

def extract_times(logfile):
    """Function to get time in between reads from the xrootd log file"""
    LINE_PATTERN = re.compile(r"kXR_read.*with status:\s*\[SUCCESS\]")
    TS_REGEX = r"\d{2}:\d{2}:\d{2}\.\d{6}"
    TS_FORMAT = "%H:%M:%S.%f"

    ts_re = re.compile(TS_REGEX)
    timestamps = []
    with open(logfile) as f:
        for line in f:
            if LINE_PATTERN.search(line):
                m = ts_re.search(line)
                if m:
                    timestamps.append(datetime.strptime(m.group(), TS_FORMAT))

    # compute deltas as timedelta (max precision)
    deltas = []
    for i in range(1, len(timestamps)):
        delta = (timestamps[i] - timestamps[i - 1]).total_seconds()
        if delta < 0:
            continue
        deltas.append(delta)
    return deltas


def check_xrootd_auth(
    xrootd_url="root://dtntest2001.fnal.gov//store/temp/sitetest/testfile_davs.bin",
):
    """
    Run xrdcp and verify authentication used 'unix'.

    Returns:
        bool: True if authenticated with unix, False otherwise.
    """

    cmd = ["xrdcp", "-d", "2", "-f", xrootd_url, "/dev/null"]

    result = subprocess.run(cmd, capture_output=True, text=True)

    output = result.stdout + result.stderr

    logging.debug(output)

    if "Authenticated with unix" in output and "Authenticated with ztn" in output:
        return True
    else:
        return False


def generate_token():
    file = os.environ.get("BEARER_TOKEN_FILE", "rtest.tkn")
    cmd = (
        "curl -s "
        f"-d 'client_id={client_id}' "
        f"-d 'client_secret={client_secret}' "
        f"-d 'grant_type=client_credentials' "
        f"-d 'scope=storage.read:/' "
        f"https://cms-auth.cern.ch/token"
    )
    output = subprocess.getoutput(cmd)
    try:
        access_token = json.loads(output)["access_token"]
        with open(file, "w") as f:
            f.write(access_token)
        os.chmod(file, 0o600)
    except Exception as e:
        logging.error(f"Failed to generate access token: {e}")


def refresh_token(every=1800):
    """Refresh the token every so many seconds"""
    while True:
        generate_token()
        time.sleep(every)

def split_rootfile_list(rootfile_list, num_jobs, job_id):
    """Split the rootfile list into num_jobs parts and return the part for this job"""
    with open(rootfile_list, "r") as f:
        rootfiles = [line.strip() for line in f if line.strip()]
    total_files = len(rootfiles)
    files_per_job = total_files // num_jobs #rounds down to nearest integer
    start_index = job_id * files_per_job
    end_index = start_index + files_per_job if job_id < (num_jobs - 1) else total_files
    return rootfiles[start_index:end_index]

# -----------------------------------------------------------------------------------------#

# ----------Main---------#
if __name__ == "__main__":
    args = parser.parse_args()

    # Configure global logging framework based on debug flag setup
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    #generate_token()
    success = check_xrootd_auth()

    if success:
        logging.info("Unix authentication confirmed.")
    else:
        logging.error("Unix authentication failed.")
        exit(1)

    # keep token up to date
    threading.Thread(target=refresh_token, daemon=True).start()

    filein= args.input
    rootfiles = args.rootfiles
    rootfiles_list = split_rootfile_list(rootfiles, args.jobs, args.job_id) #gets rootfile list for this specific job
    random_reads = args.random_read
    duration = args.duration
    reduce_size = args.reduce_size
    random_read_size = args.size
    max_workers = args.workers
    start = time.time()
    process = psutil.Process(os.getpid())
    total_stats = Stats()
    stats_log = []
    redirector = "" #"root://dtntest2001.fnal.gov//store/temp/sitetest"
    future_to_job_id = {}
    threading.Thread(target=monitor_system, args=(stats_log,), daemon=True).start()

    sleep_times = extract_times(filein)

    with ThreadPoolExecutor(max_workers) as executor:
        urls = [redirector + line.strip() for line in rootfiles_list]       
        if random_reads == False:
            for i in range(max_workers):
                filepath = urls[i % len(urls)]  # Cycle through the list of URLs if there are more workers than URLs
                logging.info(f"Submitting replay over {filepath}")
                f_obj = executor.submit(replaylog, filein, filepath, sleep_times, reduce_size)
                future_to_job_id[f_obj] = f"worker_{i}_{filepath}"

        else:
            logging.info(f"Random reads enabled, using read size of {random_read_size} bytes for {duration} seconds")
            end_time = start + duration
            for i in range(max_workers):
                filepath = urls[i % len(urls)]  # Cycle through the list of URLs if there are more workers than URLs
                logging.info(f"Submitting random replay over {filepath}")
                f_obj = executor.submit(randomreplaylog, filein, filepath, random_read_size, end_time)
                #f_obj = executor.submit(duration_replay, filein, urls, end_time, random_read_size)
                future_to_job_id[f_obj] = f"worker_{i}_{filepath}"
    # Dict for separate job metrics
    per_job_stats = {}
    for f in as_completed(future_to_job_id):
        job_id = future_to_job_id.get(f)
        try:
            stats = f.result()
            total_stats += stats
            per_job_stats[job_id] = stats.to_dict()  # Store stats for this job
        except Exception as e:
            logging.error(f"Exception encountered within thread future: {e}")
            per_job_stats[job_id] = {"error": str(e)}  # Store error for this job
                
    end = time.time()
    local_tz = ZoneInfo("America/Chicago")  # set timezone to central time
    local_start_time = datetime.fromtimestamp(start, tz=local_tz)
    local_end_time = datetime.fromtimestamp(end, tz=local_tz)
    start_timestamp = local_start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_timestamp = local_end_time.strftime("%Y-%m-%d %H:%M:%S")
    final_threads = threading.active_count()
    
    if stats_log:
        avg_cpu = sum(x["cpu"] for x in stats_log) / len(stats_log)
        max_cpu = max(x["cpu"] for x in stats_log)

        max_mem = max(x["memory_bytes"] for x in stats_log)
        max_mem_percent = max(x["memory_percent_total"] for x in stats_log)
        total_read = stats_log[-1]["read_bytes"] - stats_log[0]["read_bytes"]
        readminus1 = stats_log[-1]["read_bytes"]
        read0 = stats_log[0]["read_bytes"]
    else:
        avg_cpu = max_cpu = max_mem = max_mem_percent = total_read = readminus1 = 0

    # Main structural outputs always use logging.info to display summaries cleanly
    logging.info(f"Total runtime: {end - start:.2f} seconds")
    logging.info(f"Errors opening file: {total_stats.file_open_errors}")
    logging.info(f"Read offset/chunk mismatches: {total_stats.read_mismatches}")
    logging.info(f"Read fails: {total_stats.read_fails}")
    logging.info(f"Actual vs expected read mismatches: {total_stats.read_errors}")
    logging.info(f"Total bytes: {total_stats.total_bytes}")
    logging.info(f"Total read requests: {total_stats.read_requests}")

    # json file mapping properties
    uid_object = uuid.uuid4()
    uid_string = str(uid_object)
    format_str = datetime.fromtimestamp(start, tz=local_tz).strftime("%m%d%y_%H%M%S")
    added_num = f"{args.job_id}"
    json_name = f"replaystats_{format_str}_{uid_string}_{added_num}.json"
    output = {
        "starttime": start_timestamp,
        "endtime": end_timestamp,
        "duration seconds": end - start,
        "threads": {"max_workers": max_workers, "final_active_threads": final_threads},
        "cpu": {
            "average_percent": avg_cpu,
            "max_percent": max_cpu,
        },
        "memory": {
            "max_bytes": max_mem,
            "max_mb": max_mem / (1024**2),
            "max_mem_percent": max_mem_percent,
        },
        "io": {
            "bytes_end": readminus1,
            "read_mb": total_read / (1024**2),
        },
        "stats": {
            "total_bytes_read": total_stats.total_bytes,
            "total_read_time_seconds": total_stats.total_read_time,
            "read_mismatches": total_stats.read_mismatches,
            "read_fails": total_stats.read_fails,
            "read_errors": total_stats.read_errors,
            "file_open_errors": total_stats.file_open_errors,
            "read_requests": total_stats.read_requests,
            "read_skips": total_stats.read_skips,
            "read_bytes_skipped": total_stats.bytes_skipped,
            "total_open_time_seconds": total_stats.total_open_time,
        },
        "job info:": {
            #"rootfile_list": rootfiles_list,
            "xrdlog": filein,
            "random_reads": random_reads,
            "duration_random_reads": duration,
            "reduce_size": reduce_size,
            "jobs_submitted": args.jobs,
            "job_id": args.job_id,
        },
        "stats_per_job": per_job_stats,
    }

    with open(json_name, "w") as f:
        json.dump(output, f, indent=4)
