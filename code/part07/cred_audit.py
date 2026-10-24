#!/usr/bin/env python3
"""Find BMC accounts that differ from the rest (idea from BCM's `credentialsoverview --inverse`).

Input CSV columns: node,bmc_user,bmc_password. Passwords are never printed. Each distinct
(user, password) pair is shown as a short salted SHA-256 fingerprint with a count, smallest groups
first, so outliers sit at the top. Also flags default or empty credentials.
The salt changes on every run, so a fingerprint copied from one run is useless in another, which is
the same reason the BCM book gives for salting with the session.
"""
import csv, hashlib, os, sys, collections

KNOWN_DEFAULTS = {("admin", "admin"), ("root", "root"), ("root", "calvin"), ("admin", "password"),
                  ("ADMIN", "ADMIN"), ("root", "0penBmc"), ("admin", "")}


def fingerprint(salt, user, pw):
    return hashlib.sha256(salt + f"{user}\0{pw}".encode()).hexdigest()[:12]


def main(path):
    salt = os.urandom(8)
    groups = collections.defaultdict(list)
    problems = []
    for row in csv.DictReader(open(path)):
        user, pw, node = row["bmc_user"], row["bmc_password"], row["node"]
        groups[(user, pw)].append(node)
        if not pw:
            problems.append(f"{node}: empty BMC password")
        if (user, pw) in KNOWN_DEFAULTS:
            problems.append(f"{node}: factory-default credentials ({user})")
    print(f"{'count':>5}  {'user':10} {'fingerprint':14} nodes")
    for (user, pw), nodes in sorted(groups.items(), key=lambda kv: len(kv[1])):
        shown = ",".join(nodes[:4]) + ("..." if len(nodes) > 4 else "")
        print(f"{len(nodes):>5}  {user:10} {fingerprint(salt, user, pw):14} {shown}")
    if len(groups) > 1:
        print(f"\n{len(groups)} different credential sets: the smallest group is probably the odd one out")
    for p in problems:
        print("PROBLEM", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
