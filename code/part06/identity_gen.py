#!/usr/bin/env python3
"""One user list -> LDAP entries (LDIF), Slurm accounting commands, and home/quota setup, with validation.

CSV columns: user,uid,fullname,group,project,shell,quota_gb,sshkey
Usage: identity_gen.py users.csv OUTDIR [--base dc=cluster,dc=example,dc=org] [--min-uid 10000]
Outputs: users.ldif, slurm_accounts.sh, homes.sh
"""
import argparse
import csv
import os
import re
import sys


def validate(rows, min_uid):
    errs, users, uids = [], set(), {}
    for r in rows:
        u = r["user"]
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,31}", u):
            errs.append(f"{u}: invalid user name")
        if u in users:
            errs.append(f"{u}: duplicate user")
        users.add(u)
        try:
            uid = int(r["uid"])
        except ValueError:
            errs.append(f"{u}: uid not a number")
            continue
        if uid < min_uid:
            errs.append(f"{u}: uid {uid} below site minimum {min_uid} (collides with system/local ranges)")
        if uid in uids:
            errs.append(f"{u}: uid {uid} already used by {uids[uid]}")
        uids[uid] = u
        if not r["shell"].startswith("/"):
            errs.append(f"{u}: shell must be an absolute path")
        if not r["quota_gb"].isdigit():
            errs.append(f"{u}: quota_gb must be an integer")
    return errs


def gidnumber(group, gids):
    return gids.setdefault(group, 20000 + len(gids))


def ldif(rows, base):
    out, gids = [], {}
    people, groups = f"ou=People,{base}", f"ou=Groups,{base}"
    out += [f"dn: {people}", "objectClass: organizationalUnit", "ou: People", "", f"dn: {groups}", "objectClass: organizationalUnit", "ou: Groups", ""]
    members = {}
    for r in rows:
        g = r["group"]
        gidnumber(g, gids)
        members.setdefault(g, []).append(r["user"])
    for g, gid in gids.items():
        out += [f"dn: cn={g},{groups}", "objectClass: posixGroup", f"cn: {g}", f"gidNumber: {gid}"]
        out += [f"memberUid: {m}" for m in members[g]]
        out.append("")
    for r in rows:
        cn = r["fullname"]
        sn = cn.split()[-1]
        out += [f"dn: uid={r['user']},{people}", "objectClass: inetOrgPerson", "objectClass: posixAccount", "objectClass: shadowAccount",
                "objectClass: ldapPublicKey", f"uid: {r['user']}", f"cn: {cn}", f"sn: {sn}", f"uidNumber: {r['uid']}",
                f"gidNumber: {gids[r['group']]}", f"homeDirectory: /home/{r['user']}", f"loginShell: {r['shell']}"]
        if r["sshkey"]:
            out.append(f"sshPublicKey: {r['sshkey']}")
        out.append("")
    return "\n".join(out)


def slurm(rows):
    out = ["#!/bin/bash", "set -euo pipefail"]
    for acct in sorted({r["project"] for r in rows}):
        out.append(f"sacctmgr -i add account {acct} Description='{acct}' Organization='{acct}' || true")
    for r in rows:
        out.append(f"sacctmgr -i add user {r['user']} account={r['project']} defaultaccount={r['project']} || true")
    return "\n".join(out) + "\n"


def homes(rows):
    out = ["#!/bin/bash", "set -euo pipefail", "# run on the file server hosting /home; example with Lustre project quotas (6.19)"]
    for r in rows:
        out += [f"install -d -m 0700 -o {r['uid']} -g {r['uid']} /home/{r['user']}",
                f"# lfs setquota -u {r['user']} -B {r['quota_gb']}G -b {int(r['quota_gb']) * 9 // 10}G /home"]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("outdir")
    ap.add_argument("--base", default="dc=cluster,dc=example,dc=org")
    ap.add_argument("--min-uid", type=int, default=10000)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv)))
    errs = validate(rows, a.min_uid)
    if errs:
        print("\n".join("ERROR " + e for e in errs))
        sys.exit(1)
    os.makedirs(a.outdir, exist_ok=True)
    open(os.path.join(a.outdir, "users.ldif"), "w").write(ldif(rows, a.base))
    open(os.path.join(a.outdir, "slurm_accounts.sh"), "w").write(slurm(rows))
    open(os.path.join(a.outdir, "homes.sh"), "w").write(homes(rows))
    print(f"wrote users.ldif, slurm_accounts.sh, homes.sh for {len(rows)} users")
