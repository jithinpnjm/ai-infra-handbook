#!/usr/bin/env python3
"""A small model of the BCM 11 object model, built ONLY from rules the Administrator Manual states.

It is a teaching model, not BCM and not a cmsh clone. Each rule below names the manual section it comes from.
The point is to be able to ask 'where does this node's value come from?' and 'which role wins?' and to test
that your understanding matches the manual.

Rules implemented (BCM 11 Administrator Manual):
  2.1.3  A regular node is in exactly one category at all times ('default' unless changed).
  2.1.3  Non-Boolean values: the node inherits the category value; a value set on the node overrules it.
  2.1.3  Boolean values: NOT inherited. The category value and the node value are combined with a Boolean OR.
  2.1.3  Several categories may use the same software image (no one-to-one rule).
  2.1.4  A node may be in 0 or more node groups; groups carry no configuration, only operations.
  2.1.5  Roles are assigned, never created (no custom roles). Category-assigned roles have priority 250,
         node-assigned roles 750. A node-assigned role overrides a category-assigned one.
  2.1.6  Configuration overlays assign roles with a priority 0..1000 (default 500); 250 and 750 are forbidden;
         -1 means the overlay is ignored. The highest priority decides the role that applies.
  2.1.1  Device states: UP, DOWN, CLOSED(UP), CLOSED(DOWN). DOWN means a failure (should be up); CLOSED(DOWN)
         means the administrator deliberately took it down. CLOSED devices are mostly ignored by monitoring.
"""
from dataclasses import dataclass, field

CATEGORY_PRIORITY, OVERLAY_DEFAULT_PRIORITY, NODE_PRIORITY = 250, 500, 750
KNOWN_ROLES = {"boot", "provisioning", "storage", "slurmclient", "slurmserver", "slurmsubmit", "slurmaccounting",
               "kubernetesnode", "kubernetescontrolplane", "login", "monitoring", "dockerhost", "pbsproclient"}


class BcmError(ValueError):
    pass


@dataclass
class RoleAssignment:
    role: str
    params: dict = field(default_factory=dict)
    priority: int = 0
    source: str = ""


@dataclass
class SoftwareImage:
    name: str
    kernelversion: str = ""
    locked: bool = False


@dataclass
class Category:
    name: str
    softwareimage: str = "default-image"
    values: dict = field(default_factory=dict)        # non-Boolean settings
    flags: dict = field(default_factory=dict)         # Boolean settings
    roles: dict = field(default_factory=dict)         # role name -> params


@dataclass
class Node:
    hostname: str
    category: str = "default"
    values: dict = field(default_factory=dict)
    flags: dict = field(default_factory=dict)
    roles: dict = field(default_factory=dict)
    state: str = "UP"                                 # UP, DOWN, CLOSED(UP), CLOSED(DOWN)


@dataclass
class Overlay:
    name: str
    priority: int = OVERLAY_DEFAULT_PRIORITY
    roles: dict = field(default_factory=dict)
    nodes: set = field(default_factory=set)
    categories: set = field(default_factory=set)


class Cluster:
    DEFAULTS = {"newnodeinstallmode": "FULL", "bootloaderprotocol": "HTTP", "kernelparameters": ""}

    def __init__(self):
        self.partition = {"defaultcategory": "default"}
        self.images = {"default-image": SoftwareImage("default-image")}
        self.categories = {"default": Category("default")}
        self.nodes = {}
        self.groups = {}
        self.overlays = {}

    # ---- building the cluster ---------------------------------------------------------------
    def add_category(self, name, softwareimage="default-image", **kw):
        if softwareimage not in self.images:
            raise BcmError(f"no software image '{softwareimage}'")
        self.categories[name] = Category(name, softwareimage, **kw)
        return self.categories[name]

    def add_node(self, hostname, category=None, **kw):
        category = category or self.partition["defaultcategory"]
        if category not in self.categories:
            raise BcmError(f"no category '{category}'")
        self.nodes[hostname] = Node(hostname, category, **kw)
        return self.nodes[hostname]

    def move_node(self, hostname, category):
        """A node is in exactly one category: moving replaces the old one (2.1.3)."""
        if category not in self.categories:
            raise BcmError(f"no category '{category}'")
        self.nodes[hostname].category = category

    def add_to_group(self, group, *hostnames):
        """Groups hold names only. A node may be in many groups (2.1.4)."""
        self.groups.setdefault(group, set()).update(hostnames)

    def assign_role(self, target, name, role, **params):
        """cmsh 'assign': only EXISTING roles can be assigned. There is no 'add' for roles (2.1.5)."""
        if role not in KNOWN_ROLES:
            raise BcmError(f"'{role}' is not a role BCM provides: custom roles cannot be created, use a configuration overlay (2.1.5)")
        obj = self.nodes[name] if target == "node" else self.categories[name]
        obj.roles[role] = params

    def add_overlay(self, name, priority=OVERLAY_DEFAULT_PRIORITY, roles=None, nodes=(), categories=()):
        if priority != -1 and not (0 <= priority <= 1000):
            raise BcmError("overlay priority must be 0..1000 (or -1 to ignore the overlay)")
        if priority in (CATEGORY_PRIORITY, NODE_PRIORITY):
            raise BcmError(f"overlay priority {priority} is forbidden: 250 and 750 belong to category and node assignments (2.1.6)")
        for r in (roles or {}):
            if r not in KNOWN_ROLES:
                raise BcmError(f"'{r}' is not a role BCM provides")
        self.overlays[name] = Overlay(name, priority, dict(roles or {}), set(nodes), set(categories))
        return self.overlays[name]

    # ---- resolving what a node actually gets -------------------------------------------------
    def value(self, hostname, name):
        """Return (value, where it came from) for a non-Boolean setting: node, then category, then default (2.1.3)."""
        n = self.nodes[hostname]
        if name in n.values:
            return n.values[name], f"node {hostname}"
        c = self.categories[n.category]
        if name in c.values:
            return c.values[name], f"category {c.name}"
        if name in self.DEFAULTS:
            return self.DEFAULTS[name], "built-in default"
        return None, "unset"

    def flag(self, hostname, name):
        """Boolean setting = category OR node (2.1.3). Returns (result, node value, category value)."""
        n = self.nodes[hostname]
        c = self.categories[n.category]
        nv, cv = bool(n.flags.get(name, False)), bool(c.flags.get(name, False))
        return (nv or cv), nv, cv

    def image_of(self, hostname):
        """The software image comes from the category unless the node overrules it (2.1.2, 2.1.3)."""
        n = self.nodes[hostname]
        return n.values.get("softwareimage") or self.categories[n.category].softwareimage

    def roles_of(self, hostname):
        """For every role, the winning assignment: highest priority wins (2.1.5, 2.1.6)."""
        n = self.nodes[hostname]
        cand = {}
        def offer(role, params, prio, source):
            cur = cand.get(role)
            if cur is None or prio > cur.priority:
                cand[role] = RoleAssignment(role, params, prio, source)
        for role, params in self.categories[n.category].roles.items():
            offer(role, params, CATEGORY_PRIORITY, f"category {n.category}")
        for ov in self.overlays.values():
            if ov.priority == -1:
                continue
            if hostname in ov.nodes or n.category in ov.categories:
                for role, params in ov.roles.items():
                    offer(role, params, ov.priority, f"overlay {ov.name}")
        for role, params in n.roles.items():
            offer(role, params, NODE_PRIORITY, f"node {hostname}")
        return cand

    # ---- device state ------------------------------------------------------------------------
    @staticmethod
    def state_meaning(state):
        return {"UP": ("up", "monitored", "tracked"), "DOWN": ("down", "monitored", "tracked"),
                "CLOSED(UP)": ("up", "mostly ignored", "tracked"), "CLOSED(DOWN)": ("down", "mostly ignored", "tracked")}[state]

    def failures(self):
        """DOWN means 'should be up but is not' (a failure). CLOSED(DOWN) is a deliberate shutdown, not a failure."""
        return sorted(h for h, n in self.nodes.items() if n.state == "DOWN")
