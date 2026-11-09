"""Read strace output the way you would in an interview.

Pull out failed system calls, count them by errno, and print the next step
for each errno. Also reads the table printed by `strace -c`.
Standard library only.
"""
import re
import sys
from collections import Counter

# One line: optional "[pid N] ", name(args) = result, optional <seconds>.
LINE = re.compile(
    r"^(?:\[pid\s+(?P<pid>\d+)\]\s+|(?P<pid2>\d+)\s+)?"
    r"(?:(?P<ts>\d+\.\d+)\s+)?"
    r"(?P<name>[a-z_0-9]+)\((?P<args>.*)\)\s+=\s+"
    r"(?P<ret>-?\d+|\?)"
    r"(?:\s+(?P<errno>E[A-Z0-9]+)\s+\((?P<msg>[^)]*)\))?"
    r"(?:\s+<(?P<secs>\d+\.\d+)>)?\s*$"
)

# Meaning of each errno for open(2) and friends. Wording follows open(2),
# getrlimit(2), proc_sys_fs(5), inotify_add_watch(2) and path_resolution(7).
HINTS = {
    "ENOENT": "A path part does not exist or is a dangling symlink. Check the path the program really used, the working directory, and the mount namespace.",
    "EACCES": "Mode bits, an ACL, a directory without search permission on the path, noexec on exec, or a MAC policy (SELinux, AppArmor). Walk the whole path.",
    "EPERM": "The operation needs ownership or a capability. Look at the immutable attribute, capabilities, and user namespace ID mapping.",
    "EROFS": "The file is on a read-only filesystem or mount. Check the mount flags with findmnt and the pod's readOnlyRootFilesystem.",
    "EMFILE": "Per-process descriptor limit reached. Compare /proc/PID/fd with /proc/PID/limits, then find the leak.",
    "ENFILE": "System-wide open file limit reached. Compare /proc/sys/fs/file-nr with file-max.",
    "ENOSPC": "No blocks, no inodes, or an inotify watch limit. Run df -h and df -i, then check deleted-but-open files.",
    "EDQUOT": "A disk quota on blocks or inodes is exhausted for this user.",
    "ETXTBSY": "The file is an executable that is running, so it cannot be written.",
    "ELOOP": "Too many symbolic links, 40 on Linux, or O_NOFOLLOW met a symlink.",
    "ENOTDIR": "A path part used as a directory is not one.",
}

SUMMARY_ROW = re.compile(
    r"^\s*(?P<pct>\d+\.\d+)\s+(?P<secs>\d+\.\d+)\s+(?P<usecs>\d+)\s+"
    r"(?P<calls>\d+)\s+(?:(?P<errors>\d+)\s+)?(?P<name>[a-z_0-9]+)\s*$"
)


def parse_line(line):
    """Return a dict for a syscall line, or None for anything else."""
    m = LINE.match(line.strip())
    if not m:
        return None
    d = m.groupdict()
    d["ret"] = None if d["ret"] == "?" else int(d["ret"])
    d["secs"] = float(d["secs"]) if d["secs"] else None
    d["pid"] = d["pid"] or d["pid2"]
    return d


def failures(lines):
    """Yield every parsed call that came back with an errno."""
    for line in lines:
        d = parse_line(line)
        if d and d["errno"]:
            yield d


def errno_counts(lines):
    """Count failures by (syscall, errno), most common first."""
    c = Counter((d["name"], d["errno"]) for d in failures(lines))
    return c.most_common()


def last_path(d):
    """The quoted path in the first string argument, if there is one."""
    m = re.search(r'"((?:[^"\\]|\\.)*)"', d["args"])
    return m.group(1) if m else None


def parse_summary(text):
    """Parse the table printed by `strace -c` into rows."""
    rows = []
    for line in text.splitlines():
        m = SUMMARY_ROW.match(line)
        if m and m["name"] != "total":
            rows.append({
                "name": m["name"], "calls": int(m["calls"]),
                "errors": int(m["errors"] or 0), "pct": float(m["pct"]),
            })
    return rows


def slow_calls(lines, threshold):
    """Calls whose -T time is at least threshold seconds."""
    out = []
    for line in lines:
        d = parse_line(line)
        if d and d["secs"] is not None and d["secs"] >= threshold:
            out.append(d)
    return out


def report(lines):
    for (name, errno), n in errno_counts(lines):
        print("%5d  %s  %s" % (n, name, errno))
        print("       " + HINTS.get(errno, "No hint stored for this errno. Read the man page of the call."))


if __name__ == "__main__":
    report(sys.stdin.read().splitlines())
