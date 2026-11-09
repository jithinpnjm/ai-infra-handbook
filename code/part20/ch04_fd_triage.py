"""Triage the file descriptors of one process from /proc.

Reads /proc/PID/limits, /proc/PID/fd and /proc/sys/fs/file-nr, then says how
close the process is to EMFILE and what kinds of things it holds open.
Standard library only. The root of the proc tree can be changed so the tests
run on any OS.
"""
import os
import sys

WARN_RATIO = 0.8


def parse_limits(text):
    """Return {name: (soft, hard, units)}. 'unlimited' becomes None.

    /proc/PID/limits shows the soft limit, hard limit and units of each
    resource limit (proc_pid_limits(5)). Columns are separated by runs of
    two or more spaces, and names contain single spaces.
    """
    out = {}
    for line in text.splitlines():
        parts = [p for p in line.replace("\t", "  ").split("  ") if p.strip()]
        parts = [p.strip() for p in parts]
        if len(parts) < 3 or parts[0] == "Limit":
            continue
        name, soft, hard = parts[0], parts[1], parts[2]
        units = parts[3] if len(parts) > 3 else ""
        out[name] = (_num(soft), _num(hard), units)
    return out


def _num(word):
    return None if word == "unlimited" else int(word)


def parse_file_nr(text):
    """Return (allocated, free, maximum) from /proc/sys/fs/file-nr.

    proc_sys_fs(5): allocated file handles, free file handles, maximum.
    """
    a, f, m = text.split()[:3]
    return int(a), int(f), int(m)


def classify_target(target):
    """Name the kind of thing a /proc/PID/fd symlink points at.

    proc_pid_fd(5): pipes and sockets read as type:[inode], descriptors
    without an inode read as anon_inode:file-type. proc_pid_exe(5): an
    unlinked path gets ' (deleted)' appended.
    """
    if target.endswith(" (deleted)"):
        return "deleted"
    if target.startswith("socket:["):
        return "socket"
    if target.startswith("pipe:["):
        return "pipe"
    if target.startswith("anon_inode:"):
        return "anon_inode"
    if target.startswith("/dev/"):
        return "device"
    if target.startswith("/"):
        return "file"
    return "other"


def verdict(open_fds, soft_limit):
    if soft_limit is None:
        return "no per-process limit"
    ratio = open_fds / soft_limit
    if open_fds >= soft_limit:
        return "exhausted: the next open() fails with EMFILE"
    if ratio >= WARN_RATIO:
        return "close to the limit"
    return "ok"


def read_proc(pid, proc_root="/proc"):
    base = os.path.join(proc_root, str(pid))
    with open(os.path.join(base, "limits")) as fh:
        limits = parse_limits(fh.read())
    fd_dir = os.path.join(base, "fd")
    targets = {}
    for name in sorted(os.listdir(fd_dir), key=int):
        targets[int(name)] = os.readlink(os.path.join(fd_dir, name))
    return limits, targets


def summarize(limits, targets):
    soft = limits.get("Max open files", (None, None, ""))[0]
    kinds = {}
    for t in targets.values():
        kinds[classify_target(t)] = kinds.get(classify_target(t), 0) + 1
    deleted = sorted(t for t in targets.values() if classify_target(t) == "deleted")
    return {
        "open": len(targets),
        "soft_limit": soft,
        "kinds": kinds,
        "deleted": deleted,
        "verdict": verdict(len(targets), soft),
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    pid = argv[0] if argv else "self"
    limits, targets = read_proc(pid)
    s = summarize(limits, targets)
    print("open fds:", s["open"], "soft limit:", s["soft_limit"])
    print("kinds:", s["kinds"])
    for d in s["deleted"]:
        print("deleted but open:", d)
    print("verdict:", s["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
