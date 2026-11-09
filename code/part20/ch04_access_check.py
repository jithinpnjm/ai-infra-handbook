"""Explain why open() on a path succeeds or fails.

A small model of the checks the kernel makes, in the order a person should
check them. It follows path_resolution(7), acl(5), capabilities(7),
chattr(1), mount(8) and open(2). It is a teaching model, not the kernel:
it has no SELinux, AppArmor, seccomp, or user namespace mapping.
Standard library only.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class Cred:
    uid: int
    gid: int
    groups: Set[int] = field(default_factory=set)
    dac_override: bool = False      # CAP_DAC_OVERRIDE
    linux_immutable: bool = False   # CAP_LINUX_IMMUTABLE (only matters for chattr)


@dataclass
class Node:
    name: str
    uid: int
    gid: int
    mode: int                       # e.g. 0o640
    is_dir: bool = False
    # ACL as {"user": {uid: "rw-"}, "group_obj": "r--", "group": {gid: "r--"}, "mask": "r--"} or None
    acl: Optional[Dict] = None
    immutable: bool = False         # chattr +i
    mount_ro: bool = False          # the mount holding this node is read-only
    mount_noexec: bool = False


WANT = {"r": 4, "w": 2, "x": 1}


def _bits(word):
    return sum(WANT[c] for c in word if c in WANT)


def candidates(node, cred):
    """Return (list of permission bit sets, class name).

    Access is granted when any one of the sets holds everything requested.
    Without an ACL this follows path_resolution(7): the first matching class
    is the only one used, even when a later class would allow more.
    With an ACL it follows the access check algorithm in acl(5).
    """
    acl = node.acl
    if cred.uid == node.uid:
        return [(node.mode >> 6) & 7], "owner"
    if acl is None:
        if node.gid == cred.gid or node.gid in cred.groups:
            return [(node.mode >> 3) & 7], "group"
        return [node.mode & 7], "other"
    mask = _bits(acl["mask"]) if "mask" in acl else 7
    users = acl.get("user", {})
    if cred.uid in users:
        return [_bits(users[cred.uid]) & mask], "named user entry, limited by the mask"
    found = []
    if node.gid == cred.gid or node.gid in cred.groups:
        found.append(_bits(acl["group_obj"]) & mask)
    for g, perms in acl.get("group", {}).items():
        if g == cred.gid or g in cred.groups:
            found.append(_bits(perms) & mask)
    if found:
        return found, "group entries, limited by the mask"
    return [node.mode & 7], "other"


def check_access(path: List[Node], cred: Cred, want: str, executing: bool = False):
    """Walk the path. Return (allowed, errno, reason).

    path holds every directory from the root down, then the final node.
    want is a string made of r, w, x.
    """
    for d in path[:-1]:
        sets, cls = candidates(d, cred)
        if not any(b & 1 for b in sets) and not cred.dac_override:
            return False, "EACCES", "no search (x) permission on directory %s for the %s class" % (d.name, cls)
    target = path[-1]
    wants_write = "w" in want
    if wants_write and target.mount_ro:
        return False, "EROFS", "%s is on a read-only mount" % target.name
    if wants_write and target.immutable:
        return False, "EPERM", "%s has the immutable attribute, even root is refused" % target.name
    if executing and target.mount_noexec:
        return False, "EACCES", "%s is on a noexec mount, mode bits are never consulted" % target.name
    sets, cls = candidates(target, cred)
    need = _bits(want)
    if cred.dac_override:
        if "x" in want and not (target.mode & 0o111) and not target.is_dir:
            return False, "EACCES", "CAP_DAC_OVERRIDE grants execute only if some x bit is set"
        return True, None, "allowed by CAP_DAC_OVERRIDE"
    if any(b & need == need for b in sets):
        return True, None, "allowed by the %s" % cls
    have = ",".join(_fmt(b) for b in sets)
    return False, "EACCES", "the %s give %s but %s was requested" % (cls, have, want)


def _fmt(bits):
    return "".join(c if bits & v else "-" for c, v in (("r", 4), ("w", 2), ("x", 1)))
