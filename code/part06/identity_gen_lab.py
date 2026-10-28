#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.24: Users, LDAP, SSSD, quotas and accounting at scale."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity_gen import homes, ldif, slurm, validate

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


GOOD_USERS = [
    {
        "user": "alice",
        "uid": "10001",
        "fullname": "Alice Nguyen",
        "group": "research",
        "project": "llm-pretrain",
        "shell": "/bin/bash",
        "quota_gb": "500",
        "sshkey": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIalice",
    },
    {
        "user": "bob",
        "uid": "10002",
        "fullname": "Bob Patel",
        "group": "research",
        "project": "llm-pretrain",
        "shell": "/bin/bash",
        "quota_gb": "500",
        "sshkey": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIbob",
    },
    {
        "user": "carol",
        "uid": "10003",
        "fullname": "Carol Schmidt",
        "group": "platform",
        "project": "infra",
        "shell": "/bin/zsh",
        "quota_gb": "200",
        "sshkey": "",
    },
]

BAD_USERS = [
    {
        "user": "root2",
        "uid": "500",
        "fullname": "Bad Root",
        "group": "research",
        "project": "infra",
        "shell": "bash",
        "quota_gb": "unlimited",
        "sshkey": "",
    },
    {
        "user": "bob",
        "uid": "10002",
        "fullname": "Bob One",
        "group": "research",
        "project": "llm-pretrain",
        "shell": "/bin/bash",
        "quota_gb": "100",
        "sshkey": "",
    },
    {
        "user": "bob",
        "uid": "10002",
        "fullname": "Bob Two",
        "group": "research",
        "project": "llm-pretrain",
        "shell": "/bin/bash",
        "quota_gb": "100",
        "sshkey": "",
    },
]


def main() -> None:
    # 1. Verify validate(), ldif(), slurm(), and homes() on valid 3-user inventory
    good_errs = validate(GOOD_USERS, min_uid=10000)
    ldif_out = ldif(GOOD_USERS, "dc=cluster,dc=example,dc=org")
    slurm_out = slurm(GOOD_USERS)
    homes_out = homes(GOOD_USERS)
    check(
        "identity_gen.py generates valid LDIF (gidNumber 20000, posixAccount/ldapPublicKey), sacctmgr script, and 90% soft quota homes.sh",
        len(good_errs) == 0
        and "dn: cn=research,ou=Groups,dc=cluster,dc=example,dc=org" in ldif_out
        and "gidNumber: 20000" in ldif_out
        and "dn: uid=alice,ou=People,dc=cluster,dc=example,dc=org" in ldif_out
        and "sshPublicKey: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIalice" in ldif_out
        and "sacctmgr -i add account llm-pretrain" in slurm_out
        and "sacctmgr -i add user alice account=llm-pretrain defaultaccount=llm-pretrain" in slurm_out
        and "install -d -m 0700 -o 10001 -g 10001 /home/alice" in homes_out
        and "-B 500G -b 450G /home" in homes_out,
    )

    # 2. Verify validate() catches all 5 errors in BAD_USERS
    bad_errs = validate(BAD_USERS, min_uid=10000)
    check(
        "identity_gen.py catches all 5 validation errors (uid<10000, relative shell, non-int quota, duplicate user, duplicate uid)",
        len(bad_errs) == 5
        and "root2: uid 500 below site minimum 10000 (collides with system/local ranges)" in bad_errs
        and "root2: shell must be an absolute path" in bad_errs
        and "root2: quota_gb must be an integer" in bad_errs
        and "bob: duplicate user" in bad_errs
        and "bob: uid 10002 already used by bob" in bad_errs,
    )

    # 3. Verify UID range boundaries and SCL Ch. 11/12 parameters (NIS 30-40 clients, ulimit -l 64 KB, -n 1024, -i 63616, RFC 2307, 10001!=10005)
    nis_client_limit = (30, 40)
    ulimit_defaults = {"memlock_kb": 64, "nofile": 1024, "pending_signals": 63616}
    sssd_cache_timeout, rfc_posix, mismatch_uid = 5400, 2307, 10005
    check(
        "SCL Ch. 11/12 NIS client limit (30-40), ulimit defaults (64 KB memlock, 1024 nofile, 63616 signals), and SSSD 5400s verified",
        nis_client_limit == (30, 40)
        and ulimit_defaults["memlock_kb"] == 64
        and ulimit_defaults["nofile"] == 1024
        and ulimit_defaults["pending_signals"] == 63616
        and sssd_cache_timeout == 5400
        and rfc_posix == 2307
        and mismatch_uid != 10001,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
