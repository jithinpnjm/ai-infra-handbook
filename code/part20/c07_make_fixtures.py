#!/usr/bin/env python3
"""Generate the SYNTHETIC fixtures for chapter 20.7. Nothing here is a real log.

All IP addresses come from the documentation ranges (RFC 5737). Host names and
tenants are invented. The seed is fixed, so every run writes identical files.

Usage: c07_make_fixtures.py [OUTDIR]      write the text fixtures
       c07_make_fixtures.py --tree DIR    write the file tree used by task 9
"""
import os
import random
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20260207


def write(path, lines):
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def access_log(rng):
    # One hour of a gateway log, 10:00 to 10:59. Extra field at the end: request_time.
    ips = ["203.0.113.%d" % i for i in range(10, 40)] + ["198.51.100.%d" % i for i in range(1, 30)]
    paths = ["/v1/chat/completions", "/v1/completions", "/v1/models", "/healthz", "/metrics"]
    heavy = "203.0.113.77"  # the top talker, planted
    t0 = datetime(2026, 3, 12, 10, 0, 0)
    rows = []
    for i in range(3000):
        ts = t0 + timedelta(seconds=rng.randint(0, 3599))
        ip = heavy if rng.random() < 0.12 else rng.choice(ips)
        p = rng.choices(paths, weights=[60, 15, 5, 15, 5])[0]
        status = rng.choices([200, 200, 200, 200, 400, 429, 500], weights=[90, 0, 0, 0, 4, 3, 1])[0]
        rt = round(rng.uniform(0.02, 0.4) if p in ("/healthz", "/metrics", "/v1/models") else rng.uniform(0.3, 3.0), 3)
        rows.append([ts, ip, p, status, rt])
    # Error burst: 10:42, a wave of 502/503 from a handful of clients.
    for _ in range(140):
        ts = t0 + timedelta(minutes=42, seconds=rng.randint(0, 59))
        rows.append([ts, rng.choice(ips[:12]), "/v1/chat/completions", rng.choice([502, 503]), round(rng.uniform(0.01, 0.2), 3)])
    # A smaller bump at 10:17.
    for _ in range(35):
        ts = t0 + timedelta(minutes=17, seconds=rng.randint(0, 59))
        rows.append([ts, rng.choice(ips[12:]), "/v1/completions", 504, round(rng.uniform(29.0, 30.0), 3)])
    # Slow requests, planted with unique values. "9.5" is there to trap a text sort.
    slow = [(21.7, "/v1/chat/completions", 200), (48.213, "/v1/chat/completions", 200),
            (9.5, "/v1/completions", 200), (33.9, "/v1/chat/completions", 200),
            (61.004, "/v1/completions", 200), (15.25, "/v1/chat/completions", 200)]
    for rt, p, st in slow:
        ts = t0 + timedelta(seconds=rng.randint(0, 3599))
        rows.append([ts, rng.choice(ips), p, st, rt])
    rows.sort(key=lambda r: r[0])
    out = []
    for ts, ip, p, st, rt in rows:
        stamp = ts.strftime("%d/%b/%Y:%H:%M:%S +0000")
        out.append('%s - - [%s] "%s %s HTTP/1.1" %d %d "-" "python-requests/2.31 (synthetic)" %.3f'
                   % (ip, stamp, "GET" if p in ("/healthz", "/metrics", "/v1/models") else "POST",
                      p, st, rng.randint(120, 9000), rt))
    return out


def auth_log(rng):
    attackers = ["198.51.100.23", "198.51.100.99", "192.0.2.14", "192.0.2.200"]
    weights = [50, 31, 12, 3]
    t0 = datetime(2026, 3, 12, 3, 0, 0)
    out = []
    for i in range(400):
        ts = (t0 + timedelta(seconds=i * 7)).strftime("%b %d %H:%M:%S")
        pid = rng.randint(1000, 30000)
        ip = rng.choices(attackers, weights)[0]
        port = rng.randint(30000, 60000)
        kind = rng.choice(["inv", "root", "user"])
        if kind == "inv":
            msg = "Failed password for invalid user %s from %s port %d ssh2" % (rng.choice(["admin", "oracle", "test"]), ip, port)
        elif kind == "root":
            msg = "Failed password for root from %s port %d ssh2" % (ip, port)
        else:
            msg = "Failed password for deploy from %s port %d ssh2" % (ip, port)
        out.append("%s gpu-node-07 sshd[%d]: %s" % (ts, pid, msg))
        if i % 25 == 0:
            out.append("%s gpu-node-07 sshd[%d]: Accepted publickey for deploy from 192.0.2.50 port %d ssh2: ED25519 SHA256:synthetic"
                       % (ts, pid + 1, port))
    return out


def journal(rng):
    t0 = datetime(2026, 3, 12, 2, 0, 0)
    plan = {"vllm.service": 9, "node-exporter.service": 2, "dcgm-exporter.service": 5}
    out = []
    sec = 0
    for unit, n in plan.items():
        for k in range(1, n + 1):
            sec += rng.randint(20, 90)
            ts = (t0 + timedelta(seconds=sec)).strftime("%Y-%m-%dT%H:%M:%S+0000")
            out.append("%s gpu-node-07 systemd[1]: %s: Main process exited, code=exited, status=1/FAILURE" % (ts, unit))
            out.append("%s gpu-node-07 systemd[1]: %s: Failed with result 'exit-code'." % (ts, unit))
            out.append("%s gpu-node-07 systemd[1]: %s: Scheduled restart job, restart counter is at %d." % (ts, unit, k))
            out.append("%s gpu-node-07 systemd[1]: Stopped %s (synthetic description)." % (ts, unit))
    out.append("%s gpu-node-07 systemd[1]: vllm.service: Start request repeated too quickly." % ts)
    out.append("%s gpu-node-07 systemd[1]: vllm.service: Failed with result 'start-limit-hit'." % ts)
    # Interleave so lines are not grouped by unit.
    rng.shuffle(out)
    out.sort(key=lambda s: s[:19])
    return out


def ps_listing(rng):
    rows = [(1, 0, "Ss", "systemd"), (412, 1, "Ss", "sshd"), (655, 1, "Ssl", "containerd"),
            (901, 655, "Sl", "containerd-shim"), (902, 901, "Ssl", "python3"),
            (950, 901, "Z", "python3"), (951, 902, "Z", "ffmpeg"), (952, 902, "Z", "ffmpeg"),
            (953, 902, "Z", "ffmpeg"), (960, 1, "Ss", "ZMQ-broker"), (970, 1, "R+", "ps"),
            (980, 412, "Ss", "sshd"), (981, 980, "Ss", "bash"), (990, 981, "Z+", "sleep"),
            (1001, 902, "Dl", "dataloader"), (1002, 1, "Sl", "Zabbix-agent")]
    return ["    PID    PPID STAT COMMAND"] + ["%7d %7d %-4s %s" % r for r in rows]


def df_listing(rng):
    rows = [("/dev/nvme0n1p2", 959863856, 884123300, 26999000, "/"),
            ("tmpfs", 263840000, 0, 263840000, "/dev/shm"),
            ("/dev/nvme1n1", 3750000000, 3562500000, 187500000, "/mnt/model cache"),
            ("/dev/nvme2n1", 1920000000, 192000000, 1728000000, "/var/lib/containerd"),
            ("overlay", 959863856, 884123300, 26999000, "/var/lib/docker/overlay2/x/merged"),
            ("/dev/sda1", 102400000, 9216000, 93184000, "/boot/efi"),
            ("/dev/md0", 7680000000, 6451200000, 1228800000, "/data"),
            ("/dev/nvme3n1", 1000000000, 91000000, 909000000, "/scratch")]
    out = ["Filesystem 1024-blocks Used Available Capacity Mounted on"]
    for fs, blocks, used, avail, mnt in rows:
        pct = -(-used * 100 // (used + avail))
        out.append("%s %d %d %d %d%% %s" % (fs, blocks, used, avail, pct, mnt))
    return out


def app_jsonl(rng):
    models = ["llama-70b", "mixtral-8x7b", "embed-small"]
    codes = ["kv_cache_full", "queue_timeout", "context_too_long", "rate_limited"]
    t0 = datetime(2026, 3, 12, 11, 0, 0)
    out = []
    for i in range(500):
        ts = (t0 + timedelta(seconds=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if rng.random() < 0.16:
            code = rng.choices(codes, [10, 6, 3, 1])[0]
            if i % 29 == 0:  # a few errors with no code field
                out.append('{"ts":"%s","level":"error","model":"%s","tenant":"t-%03d"}' % (ts, rng.choice(models), rng.randint(1, 40)))
            else:
                out.append('{"ts":"%s","level":"error","model":"%s","code":"%s","tenant":"t-%03d"}'
                           % (ts, rng.choice(models), code, rng.randint(1, 40)))
        else:
            out.append('{"ts":"%s","level":"info","model":"%s","tokens_out":%d,"latency_ms":%d,"tenant":"t-%03d"}'
                       % (ts, rng.choice(models), rng.randint(1, 900), rng.randint(40, 4000), rng.randint(1, 40)))
    out.append('{"ts":"2026-03-12T11:08:21Z","level":"error","model":"llama-70b","code":"kv_cac')  # truncated tail
    return out


def crontab(rng):
    return [
        "# synthetic crontab of user deploy",
        "SHELL=/bin/bash",
        "MAILTO=ops@example.invalid",
        "",
        "*/5 * * * * /usr/local/bin/push_metrics.sh",
        "0 2 * * * tar czf /backup/models-$(date +%Y%m%d).tgz /models",
        "30 2 * * * tar czf /backup/models-$(date +\\%Y\\%m\\%d).tgz /models",
        "15 3 * * 1 /usr/local/bin/rotate_keys.sh >> /var/log/rotate.log 2>&1",
        "@daily /usr/local/bin/cleanup.sh --keep 7%",
        "45 4 * * * echo \"done $(date +%H:%M)\" >> /var/log/done.log",
        "# 0 5 * * * echo disabled %",
        "0 6 * * * /usr/bin/printf 'ok\\n' > /dev/null",
    ]


def passwd_group(rng):
    passwd = ["root:x:0:0:root:/root:/bin/bash", "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin",
              "alice:x:1000:1000:Alice:/home/alice:/bin/bash", "bob:x:1001:1001:Bob:/home/bob:/bin/bash",
              "carol:x:1002:1002:Carol:/home/carol:/usr/sbin/nologin", "dave:x:1003:1003:Dave:/home/dave:/bin/zsh",
              "toor:x:0:0:backup root:/root:/bin/bash", "svc-metrics:x:998:998::/var/lib/metrics:/usr/sbin/nologin",
              "erin:x:1004:1004:Erin:/home/erin:/bin/bash"]
    group = ["root:x:0:", "sudo:x:27:alice,carol,erin", "wheel:x:10:dave,svc-metrics", "docker:x:999:bob,alice",
             "alice:x:1000:", "bob:x:1001:"]
    return passwd, group


def make_text(outdir):
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(SEED)
    write(os.path.join(outdir, "access.log"), access_log(rng))
    write(os.path.join(outdir, "auth.log"), auth_log(rng))
    write(os.path.join(outdir, "journal.txt"), journal(rng))
    write(os.path.join(outdir, "ps.txt"), ps_listing(rng))
    write(os.path.join(outdir, "df.txt"), df_listing(rng))
    write(os.path.join(outdir, "app.jsonl"), app_jsonl(rng))
    write(os.path.join(outdir, "crontab.txt"), crontab(rng))
    passwd, group = passwd_group(rng)
    write(os.path.join(outdir, "passwd.txt"), passwd)
    write(os.path.join(outdir, "group.txt"), group)


def make_tree(root):
    """Files with fixed mtimes, so `find ! -newer ref.stamp` is repeatable."""
    old = datetime(2026, 2, 1, 12, 0, 0).timestamp()
    ref = datetime(2026, 3, 1, 12, 0, 0).timestamp()
    new = datetime(2026, 3, 10, 12, 0, 0).timestamp()
    spec = [("svc/api.log", 300, old), ("svc/api.log.1", 300, old), ("svc/old requests.log", 250, old),
            ("svc/worker-a.log", 400, old), ("svc/fresh.log", 500, new), ("svc/tiny.log", 1, old),
            ("tmp/core dump.log", 150, old), ("tmp/notes.txt", 900, old), ("tmp/boundary.log", 120, old),
            ("deep/a/b/engine.log", 700, old), ("deep/a/b/engine.log.gz", 700, old)]
    os.makedirs(root, exist_ok=True)
    for rel, kib, mt in spec:
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(b"x" * (kib * 1024))
        os.utime(p, (mt, mt))
    stamp = os.path.join(root, "ref.stamp")
    open(stamp, "w").close()
    os.utime(stamp, (ref, ref))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--tree"]:
        make_tree(a[1])
    else:
        make_text(a[0] if a else os.path.join(HERE, "c07_fixtures"))
