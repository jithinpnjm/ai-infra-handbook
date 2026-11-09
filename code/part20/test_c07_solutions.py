"""Runs every chapter 20.7 solution against its synthetic fixture.

Expected values are computed here in plain Python from the fixture, not copied
from the shell output, so a wrong one-liner cannot agree with a wrong test.
"""
import collections
import glob
import json
import os
import re
import shutil
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "c07_fixtures")


def sh(name, *args):
    r = subprocess.run(["bash", os.path.join(HERE, name), *args], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout.splitlines()


def lines(name):
    with open(os.path.join(FIX, name)) as f:
        return f.read().splitlines()


def top(counter, n):
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def test_all_shell_files_pass_bash_n():
    files = glob.glob(os.path.join(HERE, "c07_*.sh"))
    assert len(files) >= 15
    for f in files:
        assert subprocess.run(["bash", "-n", f]).returncode == 0, f


def test_fixtures_are_deterministic(tmp_path):
    subprocess.run(["python3", os.path.join(HERE, "c07_make_fixtures.py"), str(tmp_path)], check=True)
    for name in os.listdir(FIX):
        assert open(os.path.join(FIX, name)).read() == open(tmp_path / name).read(), name


def test_t01_top_talkers():
    c = collections.Counter(l.split()[0] for l in lines("access.log"))
    assert sh("c07_t01_top_talkers.sh") == ["%s %d" % kv for kv in top(c, 5)]
    assert sh("c07_t01_top_talkers.sh")[0].startswith("203.0.113.77 ")


def test_t02_slowest():
    rows = [(float(l.split()[-1]), l.split()[8], l.split()[6]) for l in lines("access.log")]
    exp = ["%.3f %s %s" % r for r in sorted(rows, key=lambda r: -r[0])[:5]]
    assert sh("c07_t02_slowest_requests.sh") == exp
    assert exp[0].startswith("61.004")


def test_t03_bursts():
    c = collections.Counter()
    for l in lines("access.log"):
        f = l.split()
        if f[8].startswith("5"):
            c[f[3][1:18]] += 1
    assert sh("c07_t03_error_bursts.sh") == ["%s %d" % kv for kv in top(c, 3)]
    assert sh("c07_t03_error_bursts.sh")[0] == "12/Mar/2026:10:42 140"


def test_t04_percentiles():
    v = sorted(float(l.split()[-1]) for l in lines("access.log"))
    n = len(v)
    rank = lambda p: max(1, -(-p * n // 100))
    exp = "n=%d p50=%.3f p95=%.3f p99=%.3f" % (n, v[rank(50) - 1], v[rank(95) - 1], v[rank(99) - 1])
    assert sh("c07_t04_percentile.sh") == [exp]


def test_t05_ssh():
    c = collections.Counter()
    for l in lines("auth.log"):
        m = re.search(r"Failed password .* from (\S+) port", l)
        if m:
            c[m.group(1)] += 1
    assert sh("c07_t05_ssh_failures.sh") == ["%s %d" % kv for kv in top(c, 3)]


def test_t06_restarts():
    best = {}
    for l in lines("journal.txt"):
        m = re.search(r" (\S+): Scheduled restart job, restart counter is at (\d+)\.", l)
        if m:
            best[m.group(1)] = max(best.get(m.group(1), 0), int(m.group(2)))
    exp = ["%s %d" % kv for kv in sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))]
    assert sh("c07_t06_restart_counters.sh") == exp
    assert exp[0] == "vllm.service 9"


def test_t07_zombies():
    c = collections.Counter()
    for l in lines("ps.txt")[1:]:
        pid, ppid, stat, comm = l.split(None, 3)
        if stat.startswith("Z"):
            c[ppid] += 1
    exp = ["parent %s zombies %d" % (p, n) for p, n in sorted(c.items(), key=lambda kv: (-kv[1], int(kv[0])))]
    assert sh("c07_t07_zombies.sh") == exp
    assert all("ZMQ" not in e and "Zabbix" not in e for e in exp)


def test_t08_filesystems():
    exp = []
    for l in lines("df.txt")[1:]:
        f = l.split(None, 5)
        if f[0] not in ("tmpfs", "overlay") and int(f[4].rstrip("%")) >= 85:
            exp.append((int(f[4].rstrip("%")), f[5]))
    exp = ["%d%% %s" % e for e in sorted(exp, key=lambda e: (-e[0], e[1]))]
    assert sh("c07_t08_full_filesystems.sh") == exp
    assert "95% /mnt/model cache" in exp


def test_t09_find(tmp_path):
    tree = str(tmp_path / "tree")
    subprocess.run(["python3", os.path.join(HERE, "c07_make_fixtures.py"), "--tree", tree], check=True)
    ref = os.path.getmtime(os.path.join(tree, "ref.stamp"))
    exp = []
    for d, _, fs in os.walk(tree):
        for f in fs:
            p = os.path.join(d, f)
            if f.endswith(".log") and os.path.getsize(p) > 100 * 1024 and os.path.getmtime(p) <= ref:
                exp.append((os.path.getsize(p), "./" + os.path.relpath(p, tree)))
    exp = ["%d %s" % e for e in sorted(exp, key=lambda e: (-e[0], e[1]))]
    assert sh("c07_t09_find_old_logs.sh", tree) == exp
    assert "153600 ./tmp/core dump.log" in exp
    assert not any("fresh" in e or ".gz" in e or "tiny" in e for e in exp)


@pytest.mark.skipif(shutil.which("jq") is None, reason="jq not installed")
def test_t10_jq():
    c = collections.Counter()
    for l in lines("app.jsonl"):
        try:
            o = json.loads(l)
        except ValueError:
            continue
        if o.get("level") == "error":
            c[o.get("code", "unknown")] += 1
    assert sh("c07_t10_jq_error_codes.sh") == ["%s %d" % kv for kv in top(c, 99)]
    assert c["unknown"] > 0


def test_t11_cron():
    exp = []
    for i, l in enumerate(lines("crontab.txt"), 1):
        if not l.strip() or l.lstrip().startswith("#") or re.match(r"[A-Za-z_]\w*=", l):
            continue
        f = l.split()
        cmd = " ".join(f[1:] if f[0].startswith("@") else f[5:])
        if re.search(r"(^|[^\\])%", cmd):
            exp.append("line %d" % i)
    assert sh("c07_t11_cron_percent.sh") == exp == ["line 6", "line 9", "line 10"]


def test_t12_sudo():
    pw = [l.split(":") for l in lines("passwd.txt")]
    ok = {p[0] for p in pw if int(p[2]) >= 1000 and not p[6].endswith(("nologin", "false"))}
    s = set()
    for l in lines("group.txt"):
        g = l.split(":")
        if g[0] in ("sudo", "wheel"):
            s |= {m for m in g[3].split(",") if m in ok}
    uid0 = ["uid0: %s" % p[0] for p in pw if p[2] == "0" and p[0] != "root"]
    assert sh("c07_t12_sudo_audit.sh") == ["sudo: " + " ".join(sorted(s))] + uid0


def test_signals_demo():
    out = subprocess.run(["bash", os.path.join(HERE, "c07_signals_demo.sh")], capture_output=True, text=True, timeout=60).stdout
    assert "A_handles_TERM: exit=0" in out
    assert "B_ignores_TERM: still_running=yes" in out
    assert "B_after_KILL: exit=137" in out
    assert "C_default_TERM: exit=143" in out
    assert "D_zombie_count: 1" in out
    assert "D_parent_pid_matches: yes" in out


def test_robust_demo():
    out = subprocess.run(["bash", os.path.join(HERE, "c07_robust_demo.sh")], capture_output=True, text=True, timeout=60).stdout
    assert "if_hides_e: exit=0 out=after-false|ok" in out
    assert "pipefail_off: exit=0 out=status=0" in out
    assert "pipefail_on: exit=0 out=status=1" in out
    assert "unset_var: exit=" in out and "not-reached" not in out.split("unset_var")[1].split("\n")[0]
    assert "local_masks: exit=0 out=reached" in out
    assert "quote_split: exit=0 out=unquoted=2|quoted=1" in out
    assert "trap_cleanup: exit=1 out=cleaned" in out


def test_transfer_demo():
    out = subprocess.run(["bash", os.path.join(HERE, "c07_transfer_demo.sh")], capture_output=True, text=True, timeout=60).stdout
    assert "tar_roundtrip_equal: yes" in out
    assert "curl_404_without_f: 404" in out
    assert "curl_404_with_f_exit: 22" in out
    assert "c.txt" in out
