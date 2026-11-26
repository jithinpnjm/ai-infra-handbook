#!/usr/bin/env python3
import re, sys, subprocess, pathlib
import xml.etree.ElementTree as ET

# Content check
participants = [
    "User on login node",
    "slurmctld",
    "slurmdbd",
    "slurmd on node A",
    "slurmd on node B"
]

messages = [
    ("U", "C", "sbatch job.sh (RPC with munge credential)"),
    ("C", "C", "authenticate, run job_submit plugin, check limits and associations"),
    ("C", "U", "Submitted batch job 4217"),
    ("C", "C", "job PENDING in queue, scheduler loop and backfill evaluate it"),
    ("C", "C", "resources found: allocate nodes A and B, state RUNNING"),
    ("C", "D1", "launch batch step (RPC tree fan-out)"),
    ("C", "D2", "prepare node (prolog)"),
    ("D1", "D1", "prolog, fork slurmstepd, run the batch script"),
    ("D1", "D2", "script runs srun, steps launched on both nodes"),
    ("D1", "D1", "epilog, cleanup of processes"),
    ("D2", "D2", "epilog, cleanup of processes"),
    ("D1", "C", "job complete RPC"),
    ("C", "DBD", "job record: times, resources, exit code, usage"),
    ("C", "C", "free nodes A and B, run scheduler again")
]

print(f"Total participants: {len(participants)}")
print(f"Total messages: {len(messages)}")
