import os

import ch04_fd_triage as T

# The shape of /proc/PID/limits follows proc_pid_limits(5): soft, hard, units.
# The numbers are made up. 524288 is the hard limit that systemd.exec(5)
# names as the usual default for LimitNOFILE.
LIMITS = (
    "Limit                     Soft Limit           Hard Limit           Units     \n"
    "Max cpu time              unlimited            unlimited            seconds   \n"
    "Max open files            1024                 524288               files     \n"
    "Max processes             63000                63000                processes \n"
)


def test_parse_limits_reads_soft_and_hard():
    lim = T.parse_limits(LIMITS)
    assert lim["Max open files"] == (1024, 524288, "files")
    assert lim["Max cpu time"] == (None, None, "seconds")


def test_parse_file_nr_three_numbers():
    # proc_sys_fs(5): allocated, free, maximum
    assert T.parse_file_nr("1344\t0\t9223372036854775807\n") == (1344, 0, 9223372036854775807)


def test_classify_targets_from_man_pages():
    assert T.classify_target("socket:[2248868]") == "socket"  # proc_pid_fd(5)
    assert T.classify_target("pipe:[1234]") == "pipe"
    assert T.classify_target("anon_inode:[eventpoll]") == "anon_inode"  # proc_pid_fd(5)
    assert T.classify_target("/var/log/app.log (deleted)") == "deleted"  # proc_pid_exe(5)
    assert T.classify_target("/dev/null") == "device"
    assert T.classify_target("/tmp/x") == "file"


def test_verdict_thresholds():
    assert T.verdict(10, 1024) == "ok"
    assert T.verdict(900, 1024) == "close to the limit"
    assert T.verdict(1024, 1024).startswith("exhausted")
    assert T.verdict(5000, None) == "no per-process limit"


def make_proc(tmp_path, pid, targets, limits_text):
    base = tmp_path / str(pid)
    (base / "fd").mkdir(parents=True)
    (base / "limits").write_text(limits_text)
    for n, target in targets.items():
        os.symlink(target, base / "fd" / str(n))
    return str(tmp_path)


def test_read_proc_and_summarize(tmp_path):
    targets = {0: "/dev/null", 1: "/dev/null", 2: "/dev/null",
               3: "socket:[2248868]", 4: "anon_inode:[eventpoll]",
               5: "/var/log/app.log (deleted)"}
    root = make_proc(tmp_path, 42, targets, LIMITS)
    limits, found = T.read_proc(42, proc_root=root)
    assert found == targets
    s = T.summarize(limits, found)
    assert s["open"] == 6
    assert s["soft_limit"] == 1024
    assert s["kinds"]["device"] == 3
    assert s["deleted"] == ["/var/log/app.log (deleted)"]
    assert s["verdict"] == "ok"


def test_exhausted_process(tmp_path):
    small = LIMITS.replace("1024 ", "4    ")
    targets = {i: "/tmp/f%d" % i for i in range(4)}
    root = make_proc(tmp_path, 7, targets, small)
    limits, found = T.read_proc(7, proc_root=root)
    assert T.summarize(limits, found)["verdict"].startswith("exhausted")
