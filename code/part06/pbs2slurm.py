#!/usr/bin/env python3
"""Translate common #PBS directives (OpenPBS/PBS Pro style) to #SBATCH lines.

Covers: -N name, -q queue, -l select=...:ncpus=:ngpus=:mem=, -l walltime=, -l place=excl, -J range[%max],
-o/-e paths, -j oe, -m/-M mail, -W depend=, -A account. Anything else is kept as a comment for a human.
This is a migration aid, not a faithful converter: resource semantics differ (chunks vs nodes, vnodes).
"""
import re
import sys


def mem_to_slurm(v):
    m = re.match(r"^(\d+)(kb|mb|gb|tb|k|m|g|t)?$", v.lower())
    if not m:
        return None
    n, u = m.groups()
    return f"{n}{ {'kb': 'K', 'mb': 'M', 'gb': 'G', 'tb': 'T', 'k': 'K', 'm': 'M', 'g': 'G', 't': 'T', None: 'M'}[u] }"


def convert_line(line):
    m = re.match(r"^#PBS\s+(-\w)\s*(.*)$", line.strip())
    if not m:
        return [line]
    flag, val = m.group(1), m.group(2).strip()
    out = []
    if flag == "-N":
        out.append(f"#SBATCH --job-name={val}")
    elif flag == "-q":
        out.append(f"#SBATCH --partition={val}")
    elif flag == "-A":
        out.append(f"#SBATCH --account={val}")
    elif flag == "-o":
        out.append(f"#SBATCH --output={val}")
    elif flag == "-e":
        out.append(f"#SBATCH --error={val}")
    elif flag == "-j":
        out.append("# -j oe: Slurm merges stdout and stderr into --output by default" if val in ("oe", "eo") else f"# TODO {line.strip()}")
    elif flag == "-J":
        rng, _, mx = val.partition("%")
        out.append(f"#SBATCH --array={rng}" + (f"%{mx}" if mx else ""))
    elif flag == "-M":
        out.append(f"#SBATCH --mail-user={val}")
    elif flag == "-m":
        types = {"a": "FAIL", "b": "BEGIN", "e": "END"}
        out.append("#SBATCH --mail-type=" + ",".join(types[c] for c in val if c in types) if any(c in types for c in val) else "# -m n: no mail")
    elif flag == "-W" and val.startswith("depend="):
        out.append(f"#SBATCH --dependency={val[len('depend='):].replace(',', ',')}")
    elif flag == "-l":
        for part in re.split(r",(?![^=]*\+)", val):
            if part.startswith("select="):
                chunks = part[len("select="):].split("+")
                if len(chunks) > 1:
                    out.append(f"# TODO heterogeneous select ({part}); needs a Slurm heterogeneous job")
                    continue
                n, _, rest = chunks[0].partition(":")
                if n.isdigit():
                    nodes, res = int(n), rest
                else:
                    nodes, res = 1, chunks[0]
                kv = dict(x.split("=", 1) for x in res.split(":") if "=" in x)
                out.append(f"#SBATCH --nodes={nodes}")
                if "mpiprocs" in kv:
                    out.append(f"#SBATCH --ntasks-per-node={kv['mpiprocs']}")
                if "ncpus" in kv:
                    out.append(f"#SBATCH --cpus-per-task={kv['ncpus']}" if "mpiprocs" not in kv else f"#SBATCH --cpus-per-task={max(1, int(kv['ncpus']) // int(kv['mpiprocs']))}")
                if "ngpus" in kv:
                    out.append(f"#SBATCH --gpus-per-node={kv['ngpus']}")
                if "mem" in kv and mem_to_slurm(kv["mem"]):
                    out.append(f"#SBATCH --mem={mem_to_slurm(kv['mem'])}")
            elif part.startswith("walltime="):
                out.append(f"#SBATCH --time={part[len('walltime='):]}")
            elif part.startswith("place="):
                if "excl" in part:
                    out.append("#SBATCH --exclusive")
                else:
                    out.append(f"# TODO {part}: no direct equivalent (see --distribution, --exclusive)")
            else:
                out.append(f"# TODO unmapped resource: {part}")
    else:
        out.append(f"# TODO unmapped: {line.strip()}")
    return out


if __name__ == "__main__":
    for raw in open(sys.argv[1]).read().split("\n"):
        for l in convert_line(raw):
            print(l.replace("$PBS_JOBID", "$SLURM_JOB_ID").replace("$PBS_O_WORKDIR", "$SLURM_SUBMIT_DIR").replace("$PBS_NODEFILE", "<use: scontrol show hostnames $SLURM_JOB_NODELIST>").replace("$PBS_ARRAY_INDEX", "$SLURM_ARRAY_TASK_ID"))
