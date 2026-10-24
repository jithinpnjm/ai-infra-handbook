#!/usr/bin/env python3
"""Lint #SBATCH directives and a few habits in a batch script.

The option list was extracted from the sbatch(1) man page of a recent Slurm development version; options
newer or older than your release may be reported as unknown (warning only). Rules come from statements in
the man pages (mutually exclusive memory options, --cpus-per-gpu vs --cpus-per-task, ...) plus common
operational practice.
"""
import re
import sys

LONG = set("""account acctg-freq array batch bb bbf begin chdir cluster-constraint clusters comment consolidate-segments
constraint container container-id contiguous core-spec cores-per-socket cpu-freq cpus-per-gpu cpus-per-task deadline
delay-boot dependency distribution error exclude exclusive export export-file extra extra-node-info get-user-env gid
gpu-bind gpu-freq gpus gpus-per-node gpus-per-socket gpus-per-task gres gres-flags help hint hold ignore-pbs input
job-name kill-on-invalid-dep layout licenses mail-type mail-user max-pids mcs-label mem mem-bind mem-per-cpu mem-per-gpu
mem-update mincpus network nice no-kill no-requeue nodefile nodelist nodes ntasks ntasks-per-core ntasks-per-gpu
ntasks-per-node ntasks-per-socket oom-kill-step open-mode output overcommit oversubscribe parsable partition prefer
priority profile propagate qos quiet reboot requeue reservation resources resv-ports runtime segment signal
sockets-per-node spread-job spread-segments stepmgr switches test-only thread-spec threads-per-core time time-min tmp
tres-bind tres-per-task uid usage use-min-nodes verbose version wait wait-all-nodes wckey wrap""".split())
SHORT = {"a": "array", "A": "account", "B": "extra-node-info", "c": "cpus-per-task", "C": "constraint", "d": "dependency",
         "D": "chdir", "e": "error", "F": "nodefile", "G": "gpus", "H": "hold", "h": "help", "i": "input", "J": "job-name",
         "k": "no-kill", "L": "licenses", "M": "clusters", "m": "distribution", "N": "nodes", "n": "ntasks", "O": "overcommit",
         "o": "output", "p": "partition", "Q": "quiet", "q": "qos", "s": "oversubscribe", "S": "core-spec", "t": "time",
         "v": "verbose", "W": "wait", "w": "nodelist", "x": "exclude"}


def directives(lines):
    out = []
    for no, line in enumerate(lines, 1):
        if no > 1 and line.strip() and not line.startswith("#") and not line.startswith("\n"):
            pass
        m = re.match(r"^#SBATCH\s+(.*)$", line.rstrip())
        if not m:
            continue
        body = m.group(1).split("#", 1)[0].strip()
        for tok in body.split():
            if tok.startswith("--"):
                name, _, val = tok[2:].partition("=")
                out.append((no, name, val if "=" in tok else None))
            elif tok.startswith("-") and len(tok) >= 2:
                out.append((no, SHORT.get(tok[1], "?" + tok[1]), tok[2:] or None))
            elif out:
                no0, name, val = out[-1]
                if val is None:
                    out[-1] = (no0, name, tok)
    return out


def lint(path):
    text = open(path).read()
    lines = text.split("\n")
    d = directives(lines)
    names = {n: v for _, n, v in d}
    findings = []

    def add(level, msg):
        findings.append((level, msg))

    if not lines[0].startswith("#!"):
        add("ERROR", "no shebang line; sbatch rejects scripts that do not start with #!")
    for no, n, v in d:
        if n.startswith("?"):
            add("warn", f"line {no}: unknown short option -{n[1:]}")
        elif n not in LONG:
            add("warn", f"line {no}: --{n} is not in the reference option list (typo, or a different Slurm version?)")
    if "time" not in names and "time-min" not in names:
        add("warn", "no --time: the partition default applies; backfill works best with an accurate limit (6.9)")
    mems = [k for k in ("mem", "mem-per-cpu", "mem-per-gpu") if k in names]
    if len(mems) > 1:
        add("ERROR", f"{', '.join('--' + m for m in mems)} are mutually exclusive")
    if "cpus-per-gpu" in names and "cpus-per-task" in names:
        add("ERROR", "--cpus-per-gpu is not compatible with --cpus-per-task")
    gpu_opts = [k for k in ("gres", "gpus", "gpus-per-node", "gpus-per-task", "gpus-per-socket") if k in names]
    if "gres" in names and not str(names["gres"]).startswith("gpu") and "gpu" in str(names["gres"]):
        add("warn", "--gres lists gpu not first; check syntax name[:type]:count")
    if gpu_opts and not any(k in names for k in ("cpus-per-gpu", "cpus-per-task", "mem-per-gpu", "mem", "mem-per-cpu", "exclusive")):
        add("warn", "GPUs requested without CPU or memory options: you get the partition defaults (DefCpuPerGPU/DefMemPerGPU) or a sliver")
    if "gpus-per-task" in names and "ntasks" not in names and "ntasks-per-node" not in names:
        add("ERROR", "--gpus-per-task needs an explicit task count (-n/--ntasks or --ntasks-per-node with --nodes)")
    if "exclusive" in names and "mem" not in names:
        add("info", "--exclusive gives all CPUs/GRES but only the memory you request; add --mem=0 for the whole node")
    if "array" in names and "%" not in str(names["array"]):
        add("info", "job array without a %N throttle can flood the scheduler and the file system")
    if "array" in names and "output" not in names:
        add("info", "array job using the default output name slurm-%A_%a.out; fine, but set -o logs/%x-%A_%a.out for tidiness")
    if "output" in names and "%j" not in str(names["output"]) and "%A" not in str(names["output"]) and "requeue" in names:
        add("warn", "requeued job writes to a fixed output name; use --open-mode=append or include %j")
    if "requeue" in names and "signal" not in names:
        add("info", "--requeue without --signal: the job gets no warning before preemption/time limit; checkpoint on SIGTERM/USR1")
    body = "\n".join(l for l in lines if not l.startswith("#SBATCH"))
    if "module load" in body and "module purge" not in body:
        add("warn", "module load without module purge: inherited modules can mix toolchains (6.6)")
    if not re.search(r"set\s+-[a-z]*e", body) and not re.search(r"set\s+-o\s+errexit", body):
        add("info", "no 'set -e'/errexit: a failed setup step will not stop the script")
    if re.search(r"\bmpirun\b|\bmpiexec\b", body) and "srun" not in body:
        add("info", "mpirun inside a batch script: srun --mpi=pmix lets Slurm launch and bind the ranks (6.12)")
    if int(str(names.get("nodes", "1")).split("-")[0] or 1) > 1 and "srun" not in body and "mpirun" not in body:
        add("warn", "multi-node job but no srun/mpirun: commands in the batch script run on the first node only")
    return findings


if __name__ == "__main__":
    rc = 0
    for f in sys.argv[1:]:
        print(f"== {f}")
        res = lint(f)
        for level, msg in res:
            print(f"{level:5s} {msg}")
            rc |= level == "ERROR"
        if not res:
            print("no findings")
    sys.exit(1 if rc else 0)
