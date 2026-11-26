import re
import xml.etree.ElementTree as ET
import subprocess
import pathlib

# Let's write the complete SVG generator and test script

title = "Traditional HPC center versus AI factory"
analogy = "public library versus manufacturing plant"
col1_header = "Traditional HPC center"
col2_header = "AI factory"

bottom = "Slurm, fabric and storage skills carry over; what changes is the size of each failure and how quickly you must respond"

rows = [
    {
        "name": "Workloads",
        "hpc": [
            "physical simulation in C, C++ and",
            "Fortran with MPI and OpenMP"
        ],
        "ai": [
            "neural-network pre-training, fine-tuning,",
            "data curation and inference in Python with",
            "PyTorch or JAX and NCCL"
        ],
        "h": 108,
        "is_orange": False
    },
    {
        "name": "Precision",
        "hpc": [
            "heavy FP64"
        ],
        "ai": [
            "BF16, FP16, FP8, FP4; FP64 rarely used"
        ],
        "h": 56,
        "is_orange": False
    },
    {
        "name": "Traffic",
        "hpc": [
            "domain decomposition with halo",
            "exchanges and small global reductions"
        ],
        "ai": [
            "data, tensor, pipeline, expert and context",
            "parallelism; AllReduce, AllGather,",
            "ReduceScatter, AllToAll elephant flows"
        ],
        "h": 108,
        "is_orange": False
    },
    {
        "name": "Jobs",
        "hpc": [
            "wide mix of small and medium jobs plus",
            "occasional hero runs"
        ],
        "ai": [
            "bimodal: a few thousand-GPU jobs for weeks",
            "plus fine-tuning and 24/7 inference"
        ],
        "h": 82,
        "is_orange": False
    },
    {
        "name": "Storage",
        "hpc": [
            "scratch, home and simulation dumps",
            "with heavy POSIX metadata"
        ],
        "ai": [
            "streaming dataloader reads and periodic",
            "multi-terabyte synchronous checkpoint bursts"
        ],
        "h": 82,
        "is_orange": False
    },
    {
        "name": "Packaging",
        "hpc": [
            "environment modules, Spack, EasyBuild"
        ],
        "ai": [
            "OCI containers from NGC base images"
        ],
        "h": 56,
        "is_orange": False
    },
    {
        "name": "Failure",
        "hpc": [
            "periodic checkpoint and restart"
        ],
        "ai": [
            "at thousands of GPUs faults every few hours",
            "or days; automated health checks and",
            "sub-minute checkpointing"
        ],
        "h": 108,
        "is_orange": True # Single orange item highlight
    },
    {
        "name": "North star",
        "hpc": [
            "high node utilization and fair queue",
            "turnaround"
        ],
        "ai": [
            "high MFU, minimum time-to-train, lowest cost",
            "per token or tokens per watt"
        ],
        "h": 82,
        "is_orange": False
    },
    {
        "name": "Rack power",
        "hpc": [
            "15 to 40 kW"
        ],
        "ai": [
            "40 to 130 kW or more with direct-to-chip",
            "liquid cooling"
        ],
        "h": 82,
        "is_orange": False
    }
]

# Coordinates
# Canvas width = 1600, height = 1180
# Margin left = 40, right = 40 (usable 1520)
# Col 0 (Dimension): x = 40, width = 245
# Col 1 (HPC): x = 297, width = 588
# Col 2 (AI): x = 897, width = 663
# Note: 40 + 245 = 285. Gap = 12. 297 + 588 = 885. Gap = 12. 897 + 663 = 1560. Margin right = 40! Perfect symmetry!

w_col0 = 245
x_col0 = 40

w_col1 = 588
x_col1 = 297

w_col2 = 663
x_col2 = 897

# Row icon SVG paths generator
def get_icon(name, x, y, is_orange=False):
    c = "#db8129" if is_orange else "#207448"
    # returns SVG group with icon centered around (x+18, y+18) inside 36x36 box
    if name == "Workloads":
        # window with >_
        return f'''<g transform="translate({x}, {y})" stroke="{c}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="2" width="32" height="28" rx="4"/>
          <line x1="2" y1="10" x2="34" y2="10"/>
          <polyline points="7,17 12,21 7,25"/>
          <line x1="16" y1="25" x2="24" y2="25"/>
        </g>'''
    elif name == "Precision":
        # math / chip
        return f'''<g transform="translate({x}, {y})" stroke="{c}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="6" y="6" width="24" height="24" rx="3"/>
          <path d="M12 2 v4 M24 2 v4 M12 30 v4 M24 30 v4 M2 12 h4 M2 24 h4 M30 12 h4 M30 24 h4"/>
          <circle cx="18" cy="18" r="4"/>
        </g>'''
    elif name == "Traffic":
        # network nodes and paths
        return f'''<g transform="translate({x}, {y})" stroke="{c}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="8" cy="18" r="5"/>
          <circle cx="28" cy="9" r="5"/>
          <circle cx="28" cy="27" r="5"/>
          <line x1="13" y1="16" x2="23" y2="11"/>
          <line x1="13" y1="20" x2="23" y2="25"/>
        </g>'''
    elif name == "Jobs":
        # queue / stack of tasks
        return f'''<g transform="translate({x}, {y})" stroke="{c}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="16" width="28" height="16" rx="3"/>
          <path d="M8 16 V10 A3 3 0 0 1 11 7 H25 A3 3 0 0 1 28 10 V16"/>
          <path d="M12 7 V4 A2 2 0 0 1 14 2 H22 A2 2 0 0 1 24 4 V7"/>
          <line x1="10" y1="24" x2="26" y2="24"/>
        </g>'''
    elif name == "Storage":
        # disk cylinder
        return f'''<g transform="translate({x}, {y})" stroke="{c}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <ellipse cx="18" cy="8" rx="14" ry="5"/>
          <path d="M4 8 v10 c0 3 6 5 14 5 s14 -2 14 -5 v-10"/>
          <path d="M4 18 v8 c0 3 6 5 14 5 s14 -2 14 -5 v-8"/>
        </g>'''
    elif name == "Packaging":
        # box / package
        return f'''<g transform="translate({x}, {y})" stroke="{c}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 3 L32 10 L18 17 L4 10 Z"/>
          <path d="M4 10 V24 L18 31 V17"/>
          <path d="M32 10 V24 L18 31"/>
          <line x1="11" y1="7" x2="25" y2="14"/>
        </g>'''
    elif name == "Failure":
        # alert shield / warning
        return f'''<g transform="translate({x}, {y})" stroke="{c}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 3 L32 9 V18 C32 26 18 32 18 32 C18 32 4 26 4 18 V9 Z"/>
          <line x1="18" y1="11" x2="18" y2="19"/>
          <circle cx="18" cy="24" r="1.5" fill="{c}"/>
        </g>'''
    elif name == "North star":
        # star / compass
        return f'''<g transform="translate({x}, {y})" stroke="{c}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="18" cy="18" r="14"/>
          <polygon points="18,6 21,15 30,18 21,21 18,30 15,21 6,18 15,15" fill="{c}"/>
        </g>'''
    elif name == "Rack power":
        # lightning / power plug
        return f'''<g transform="translate({x}, {y})" stroke="{c}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="19,2 7,18 17,18 14,32 28,15 18,15"/>
        </g>'''
    return ""

print("Testing icon generator...")
for r in rows:
    ic = get_icon(r["name"], 50, 100)
    assert len(ic) > 20
print("Icons generated successfully!")
