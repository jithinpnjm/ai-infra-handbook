#!/usr/bin/env python3
import sys

def est_width(text, is_mono=False, font_size=24):
    factor = 0.62 if is_mono else 0.6
    return len(text) * factor * font_size

steps = [
    # 1: U -> C
    {"src": "U", "dst": "C", "type": "msg", "lines": [
        ("sbatch job.sh", True),
        ("(RPC with munge credential)", False)
    ]},
    # 2: C -> C
    {"src": "C", "dst": "C", "type": "self", "lines": [
        ("authenticate, run job_submit plugin,", False),
        ("check limits and associations", False)
    ]},
    # 3: C -> U
    {"src": "C", "dst": "U", "type": "reply", "lines": [
        ("Submitted batch job 4217", False)
    ]},
    # 4: C -> C
    {"src": "C", "dst": "C", "type": "self", "lines": [
        ("job PENDING in queue,", False),
        ("scheduler loop and backfill evaluate it", False)
    ]},
    # 5: C -> C
    {"src": "C", "dst": "C", "type": "self", "lines": [
        ("resources found: allocate nodes A and B,", False),
        ("state RUNNING", False)
    ]},
    # 6: C -> D1
    {"src": "C", "dst": "D1", "type": "msg", "lines": [
        ("launch batch step (RPC tree fan-out)", False)
    ]},
    # 7: C -> D2
    {"src": "C", "dst": "D2", "type": "msg", "lines": [
        ("prepare node (prolog)", False)
    ]},
    # 8: D1 -> D1
    {"src": "D1", "dst": "D1", "type": "self", "lines": [
        ("prolog, fork slurmstepd,", False),
        ("run the batch script", False)
    ]},
    # 9: D1 -> D2
    {"src": "D1", "dst": "D2", "type": "msg", "lines": [
        ("script runs srun,", False),
        ("steps launched on both nodes", False)
    ]},
    # 10: D1 -> D1
    {"src": "D1", "dst": "D1", "type": "self", "lines": [
        ("epilog, cleanup of processes", False)
    ]},
    # 11: D2 -> D2
    {"src": "D2", "dst": "D2", "type": "self", "lines": [
        ("epilog, cleanup of processes", False)
    ]},
    # 12: D1 -> C
    {"src": "D1", "dst": "C", "type": "msg", "lines": [
        ("job complete RPC", False)
    ]},
    # 13: C -> DBD
    {"src": "C", "dst": "DBD", "type": "msg", "lines": [
        ("job record: times, resources,", False),
        ("exit code, usage", False)
    ]},
    # 14: C -> C
    {"src": "C", "dst": "C", "type": "self", "lines": [
        ("free nodes A and B, run scheduler again", False)
    ]}
]

for i, s in enumerate(steps, 1):
    print(f"Step {i:2d} ({s['src']} -> {s['dst']}, {s['type']}):")
    for text, is_mono in s['lines']:
        w = est_width(text, is_mono, 24)
        print(f"   [{'MONO' if is_mono else 'SANS'}] w={w:5.1f}px (box min={w+32:5.1f}px) : '{text}'")
