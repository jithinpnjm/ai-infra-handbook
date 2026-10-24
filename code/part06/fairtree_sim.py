#!/usr/bin/env python3
"""Fair Tree fairshare and multifactor priority, re-implemented from the Slurm documentation.

Level Fairshare  LF = S / U   (S = shares / sum of sibling shares, U = usage / sum of sibling usage)
Users are ranked by a depth-first walk of the tree with children sorted by LF (descending);
FairShare = rank / number_of_user_associations, the top user getting 1.0.
Priority = sum(weight * factor); factors normalised to 0..1.
This is a teaching model: it ignores ties, TRES billing and several edge cases.
"""
import math

class Node:
    def __init__(self, name, shares, usage=0.0, children=None):
        self.name, self.shares, self.usage = name, shares, usage
        self.children = children or []

    def total_usage(self):
        return self.usage if not self.children else sum(c.total_usage() for c in self.children)

def level_fs(node, siblings):
    s = node.shares / sum(x.shares for x in siblings)
    tot = sum(x.total_usage() for x in siblings)
    u = node.total_usage() / tot if tot > 0 else 0.0
    return math.inf if u == 0 else s / u

def users(node):
    return [node] if not node.children else [u for c in node.children for u in users(c)]

def fair_tree(root):
    n_users = len(users(root))
    ranks, rank = {}, [n_users]
    def walk(node):
        if not node.children:
            ranks[node.name] = rank[0] / n_users
            rank[0] -= 1
            return
        for c in sorted(node.children, key=lambda c: level_fs(c, node.children), reverse=True):
            walk(c)
    walk(root)
    return ranks

def decay(usage, elapsed_days, half_life_days=7.0):
    return usage * 2 ** (-elapsed_days / half_life_days)

def priority(age_min, max_age_min, fairshare, qos_prio, max_qos_prio, part_factor, max_part_factor,
             w_age=1000, w_fs=100000, w_qos=10000, w_part=1000, nice=0):
    age = min(age_min / max_age_min, 1.0)
    return int(w_age * age + w_fs * fairshare + w_qos * qos_prio / max_qos_prio
               + w_part * part_factor / max_part_factor - nice)

if __name__ == "__main__":
    tree = Node("root", 1, children=[
        Node("physics", 60, children=[Node("alice", 1, 5000), Node("bob", 1, 500)]),
        Node("biology", 40, children=[Node("carol", 1, 100), Node("dave", 1, 100)]),
    ])
    print("Level fairshare among accounts:")
    for a in tree.children:
        print(f"  {a.name:8s} S={a.shares/100:.2f} U={a.total_usage()/tree.total_usage():.3f} LF={level_fs(a, tree.children):.3f}")
    print("FairShare (Fair Tree):")
    for u, f in sorted(fair_tree(tree).items(), key=lambda kv: -kv[1]):
        print(f"  {u:6s} {f:.2f}")
    print("\nUsage decay with a 7-day half-life (usage 8000 core-hours):")
    for d in (0, 7, 14, 28):
        print(f"  after {d:2d} days: {decay(8000, d):7.0f}")
    print("\nPriority of two pending jobs (weights: age 1000, fairshare 100000, qos 10000, partition 1000):")
    a = priority(age_min=60, max_age_min=7*1440, fairshare=0.25, qos_prio=10, max_qos_prio=10, part_factor=1, max_part_factor=1)
    b = priority(age_min=60*24*3, max_age_min=7*1440, fairshare=1.0, qos_prio=1, max_qos_prio=10, part_factor=1, max_part_factor=1)
    print(f"  alice's 1-hour-old job, urgent QOS:        {a}")
    print(f"  carol's 3-day-old job, normal QOS:         {b}")
