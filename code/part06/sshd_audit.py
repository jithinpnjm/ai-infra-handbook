#!/usr/bin/env python3
"""Audit an sshd_config for settings that matter on a shared login/bastion node.

Reads the global section (before the first Match block); first occurrence of a keyword wins, as in sshd.
Option names and defaults were checked against sshd_config(5) from openssh-portable (2026-10).
Usage: sshd_audit.py sshd_config [more files]
"""
import sys

RULES = [
    # keyword, predicate on value (None = unset), severity, message
    ("PermitRootLogin", lambda v: v in ("no", "prohibit-password", "forced-commands-only"), "ERROR", "root login must be no/prohibit-password/forced-commands-only (default is prohibit-password)"),
    ("PasswordAuthentication", lambda v: v == "no", "ERROR", "password authentication should be off on login nodes (keys, certificates, or SSO+MFA)"),
    ("KbdInteractiveAuthentication", lambda v: v in ("no", "yes"), "info", "keyboard-interactive is how MFA (PAM) usually works: keep 'yes' only with an AuthenticationMethods policy"),
    ("PermitEmptyPasswords", lambda v: v in (None, "no"), "ERROR", "empty passwords must never be allowed"),
    ("AllowGroups", lambda v: v is not None, "warn", "restrict logins with AllowGroups (or AllowUsers) instead of everyone in the directory"),
    ("MaxAuthTries", lambda v: v is not None and int(v) <= 4, "warn", "set MaxAuthTries <= 4 (default 6)"),
    ("LoginGraceTime", lambda v: v is not None and int(v.rstrip('s')) <= 60, "warn", "shorten LoginGraceTime (default 120 s) to limit unauthenticated connection hogging"),
    ("ClientAliveInterval", lambda v: v is not None and int(v) > 0, "warn", "set ClientAliveInterval so dead sessions on shared nodes are reaped"),
    ("X11Forwarding", lambda v: v in (None, "no", "yes"), "info", "X11 forwarding enlarges the attack surface; enable only where GUI tools are needed"),
    ("PermitUserEnvironment", lambda v: v in (None, "no"), "ERROR", "PermitUserEnvironment must stay 'no' (lets users inject LD_PRELOAD-style variables)"),
    ("AllowTcpForwarding", lambda v: v is not None, "info", "decide port forwarding policy explicitly (needed for Jupyter tunnels, risky on bastions)"),
    ("AuthorizedKeysCommand", lambda v: True, "info", "with SSSD/FreeIPA keys: AuthorizedKeysCommand /usr/bin/sss_ssh_authorizedkeys (+ AuthorizedKeysCommandUser)"),
    ("LogLevel", lambda v: v in ("VERBOSE", "INFO", "DEBUG"), "warn", "use LogLevel VERBOSE to log key fingerprints for audit"),
    ("Banner", lambda v: v is not None, "info", "legal/usage banner recommended for institutional systems"),
    ("MaxStartups", lambda v: True, "info", "default 10:30:100; raise for bastions fronting many users (login bursts at class start)"),
]


def parse(path):
    cfg = {}
    for raw in open(path):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, _, val = line.partition(" ")
        if key.lower() == "match":
            break
        cfg.setdefault(key.lower(), val.strip())
    return cfg


def audit(path):
    cfg = parse(path)
    out = []
    for key, ok, sev, msg in RULES:
        v = cfg.get(key.lower())
        try:
            good = ok(v)
        except (ValueError, AttributeError):
            good = False
        if sev == "info":
            if v is None:
                out.append(("info", f"{key} not set: {msg}"))
        elif not good:
            out.append((sev, f"{key}={v if v is not None else '<default>'}: {msg}"))
    return out


if __name__ == "__main__":
    rc = 0
    for f in sys.argv[1:]:
        print(f"== {f}")
        res = audit(f)
        for sev, m in res:
            print(f"{sev:5s} {m}")
            rc |= sev == "ERROR"
        if not res:
            print("no findings")
    sys.exit(rc)
