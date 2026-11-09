import ch04_strace_errors as S

# From How Linux Works, 3rd edition, chapter 8, section 8.3.1 (strace cat not_a_file).
BOOK_ENOENT = 'openat(AT_FDCWD, "not_a_file", O_RDONLY) = -1 ENOENT (No such file or directory)'

# From Systems Performance, 2nd edition, chapter 5, section 5.5.4 (strace -ttt -T -p).
BOOK_T = "1356982510.395542 close(3) = 0 <0.000267>"
BOOK_T2 = "1356982510.396980 rt_sigprocmask(SIG_SETMASK, [], NULL, 8) = 0 <0.000024>"

# From the same section: strace -c dd if=/dev/zero of=/dev/null bs=1k count=5000k
BOOK_C = """\
% time seconds usecs/call calls errors syscall
------ ----------- ----------- --------- --------- ----------------
51.46 0.008030 0 5120005 read
48.54 0.007574 0 5120003 write
0.00 0.000000 0 20 13 open
[...]
------ ----------- ----------- --------- --------- ----------------
100.00 0.015604 10240092 19 total
"""


def test_parse_book_enoent():
    d = S.parse_line(BOOK_ENOENT)
    assert d["name"] == "openat"
    assert d["ret"] == -1
    assert d["errno"] == "ENOENT"
    assert d["msg"] == "No such file or directory"
    assert S.last_path(d) == "not_a_file"


def test_parse_timed_lines():
    d = S.parse_line(BOOK_T)
    assert (d["name"], d["ret"], d["errno"], d["secs"]) == ("close", 0, None, 0.000267)
    assert S.parse_line(BOOK_T2)["name"] == "rt_sigprocmask"


def test_pid_prefix():
    d = S.parse_line('[pid 1975] openat(AT_FDCWD, "/etc/x", O_RDONLY) = -1 EACCES (Permission denied)')
    assert d["pid"] == "1975" and d["errno"] == "EACCES"


def test_non_syscall_lines_are_ignored():
    assert S.parse_line("+++ exited with 0 +++") is None
    assert S.parse_line("") is None


def test_errno_counts_orders_by_frequency():
    lines = [
        'openat(AT_FDCWD, "/a", O_RDONLY) = -1 ENOENT (No such file or directory)',
        'openat(AT_FDCWD, "/b", O_RDONLY) = -1 ENOENT (No such file or directory)',
        'openat(AT_FDCWD, "/c", O_RDWR) = -1 EMFILE (Too many open files)',
        'openat(AT_FDCWD, "/d", O_RDONLY) = 3',
    ]
    assert S.errno_counts(lines) == [(("openat", "ENOENT"), 2), (("openat", "EMFILE"), 1)]


def test_every_hint_is_nonempty_and_covers_open_errors():
    for e in ("ENOENT", "EACCES", "EPERM", "EROFS", "EMFILE", "ENFILE", "ENOSPC", "EDQUOT", "ETXTBSY"):
        assert len(S.HINTS[e]) > 20


def test_parse_summary_table_from_book():
    rows = S.parse_summary(BOOK_C)
    by = {r["name"]: r for r in rows}
    assert by["read"]["calls"] == 5120005
    assert by["open"]["calls"] == 20 and by["open"]["errors"] == 13
    assert by["read"]["errors"] == 0
    assert "total" not in by


def test_slow_calls():
    lines = [BOOK_T, 'wait4(-1, [{WIFEXITED(s) && WEXITSTATUS(s) == 0}], WSTOPPED|WCONTINUED, NULL) = 1975 <0.018187>']
    slow = S.slow_calls(lines, 0.01)
    assert [d["name"] for d in slow] == ["wait4"]
