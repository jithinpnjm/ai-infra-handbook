#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("candidate_job_life.svg")
root = tree.getroot()

texts = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    t = "".join(el.itertext()).strip()
    texts.append(t)
    print(f"[{el.attrib.get('font-size','?')}] '{t}'")

# Check source messages
source_messages = [
    "sbatch job.sh (RPC with munge credential)",
    "authenticate, run job_submit plugin, check limits and associations",
    "Submitted batch job 4217",
    "job PENDING in queue, scheduler loop and backfill evaluate it",
    "resources found: allocate nodes A and B, state RUNNING",
    "launch batch step (RPC tree fan-out)",
    "prepare node (prolog)",
    "prolog, fork slurmstepd, run the batch script",
    "script runs srun, steps launched on both nodes",
    "epilog, cleanup of processes",
    "job complete RPC",
    "job record: times, resources, exit code, usage",
    "free nodes A and B, run scheduler again"
]

print("\n=== CHECKING EXACT MATCHES ===")
for msg in source_messages:
    found = any(msg in t for t in texts)
    print(f"[{'PASS' if found else 'FAIL'}] '{msg}'")
    assert found
