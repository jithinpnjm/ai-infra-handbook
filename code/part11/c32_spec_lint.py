#!/usr/bin/env python3
"""Lint an NVKE cluster spec for the mistakes the NVKE docs and controller reject or warn about.

Rules come from controller/internal/server/{clusters,cluster_network,node_metadata_validation}.go
and docs/workload-clusters/{create,node-pools}.md at nvke commit 487f511.
Each finding is (severity, rule, message). Severity is ERROR when the API
rejects the request (observed on a local controller), WARN when it accepts a
request that the docs say will bite later.
"""
import ipaddress
import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
RESERVED_LABEL = ("kubernetes.io", "k8s.io", "nvke.nvidia.com", "nke.nvidia.com", "nke.io")
PRIVATE = [ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]
DEFAULT_POD = "192.168.0.0/16"
DEFAULT_SVC = "10.96.0.0/12"


def _under(key, domains):
    prefix = key.rsplit("/", 1)[0] if "/" in key else ""
    return any(prefix == d or prefix.endswith("." + d) for d in domains)


def _private(net):
    return any(net.version == 4 and net.subnet_of(p) for p in PRIVATE)


def lint(spec):
    out = []

    def add(sev, rule, msg):
        out.append((sev, rule, msg))

    name = spec.get("name", "")
    if not NAME_RE.match(name) or len(name) > 55:
        add("ERROR", "name", "name must be a lowercase DNS label of at most 55 characters")
    ver = spec.get("controlPlaneKubernetesVersion", "")
    if not VERSION_RE.match(str(ver)):
        add("ERROR", "version", "controlPlaneKubernetesVersion must be X.Y.Z with no leading v")
    if "etcdEncrypted" not in spec:
        add("ERROR", "etcd", "etcdEncrypted is required and has no default")
    elif spec["etcdEncrypted"] is False:
        add("WARN", "etcd", "etcdEncrypted false: it can be turned on later, never off")
    if spec.get("cniPlugin", "ovn-kubernetes") != "ovn-kubernetes":
        add("WARN", "cni", "only ovn-kubernetes is supported; calico creation is refused unless the controller allows legacy clusters")
    providers = [k for k in ("nico", "launchLayer", "infra") if k in spec]
    if len(providers) != 1:
        add("ERROR", "provider", "exactly one of nico, launchLayer, infra is required")

    cp = spec.get("controlPlaneConfig", {})
    count = cp.get("desiredCount")
    surge = cp.get("maxSurge", 0)
    pools = spec.get("nodePools", [])
    vip = spec.get("controlPlaneVIP")
    if count is None:
        add("ERROR", "control-plane", "controlPlaneConfig.desiredCount is required")
        count = 0
    if surge not in (0, 1):
        add("ERROR", "surge", "controlPlaneConfig.maxSurge must be 0 or 1")
    if count > 1 and not vip:
        add("ERROR", "vip", "controlPlaneVIP is required when desiredCount is above 1")
    if count == 1 and not vip:
        add("WARN", "vip", "no VIP: a single control-plane node cannot be scaled, upgraded or replaced; recreate the cluster to add a VIP")
    if count == 2:
        add("WARN", "quorum", "exactly two control-plane nodes are excluded from automatic certificate renewal; use 1 or 3 or more")
    elif count > 1 and count % 2 == 0:
        add("WARN", "quorum", "use an odd control-plane count so etcd keeps a quorum")
    cpn = cp.get("nico", {})
    if "nico" in spec:
        if not cpn.get("instanceTypePreference"):
            add("ERROR", "control-plane", "controlPlaneConfig.nico.instanceTypePreference is required")
        if not cpn.get("release"):
            add("ERROR", "release", "controlPlaneConfig.nico.release is required")
        if ("vpcPrefixIDs" in cpn) == ("subnetIDs" in cpn):
            add("ERROR", "network-ids", "control plane needs exactly one of vpcPrefixIDs or subnetIDs")

    net = spec.get("network", {})
    pod_text = net.get("podCIDR", DEFAULT_POD)
    svc_text = net.get("serviceCIDR", DEFAULT_SVC)
    try:
        pods = [ipaddress.ip_network(p.strip()) for p in pod_text.split(",")]
        svc = ipaddress.ip_network(svc_text)
    except ValueError as exc:
        add("ERROR", "cidr", f"unparseable CIDR: {exc}")
        pods, svc = [], None
    for p in pods:
        if not (12 <= p.prefixlen <= 23) or not _private(p):
            add("ERROR", "cidr", f"pod CIDR {p} must be private IPv4, /12 to /23")
        if svc and p.overlaps(svc):
            add("ERROR", "cidr", f"pod CIDR {p} overlaps service CIDR {svc}")
    if svc and (not (12 <= svc.prefixlen <= 24) or not _private(svc)):
        add("ERROR", "cidr", f"service CIDR {svc} must be private IPv4, /12 to /24")
    if pods:
        need = count + sum(p.get("desiredNodeCount", 0) for p in pools) + max(1, surge)
        have = sum(2 ** (24 - p.prefixlen) for p in pods if p.prefixlen <= 24)
        if have < need:
            add("ERROR", "cidr-capacity", f"pod CIDR gives {have} /24 node blocks but {need} are required (nodes plus headroom)")
    if vip:
        try:
            a = ipaddress.ip_address(vip)
            if a.version != 4:
                add("ERROR", "vip", "controlPlaneVIP must be IPv4")
            elif any(a in p for p in pods) or (svc and a in svc):
                add("ERROR", "vip", "controlPlaneVIP must be outside the pod and service CIDRs")
        except ValueError:
            add("ERROR", "vip", "controlPlaneVIP is not an IP address")

    for label in cp.get("nodeLabels", {}):
        if _under(label, RESERVED_LABEL):
            add("ERROR", "labels", f"control-plane label {label} is under a reserved domain")
    seen = set()
    for pool in pools:
        pn = pool.get("name", "")
        if pn in seen:
            add("ERROR", "pool-name", f"duplicate node pool name {pn}")
        seen.add(pn)
        prefix = pool.get("nodeNamePrefix", "")
        if len(f"{name}-{prefix}-0000") > 63:
            add("ERROR", "node-name", f"pool {pn}: node names {name}-{prefix}-NNNN exceed 63 characters")
        pnico = pool.get("nico", {})
        if "nico" in spec:
            if not pnico.get("instanceTypeID"):
                add("ERROR", "pool", f"pool {pn}: nico.instanceTypeID is required")
            if not pnico.get("release"):
                add("ERROR", "release", f"pool {pn}: nico.release is required")
            if ("vpcPrefixIDs" in pnico) == ("subnetIDs" in pnico):
                add("ERROR", "network-ids", f"pool {pn}: need exactly one of vpcPrefixIDs or subnetIDs")
        for label in pool.get("nodeLabels", {}):
            if _under(label, RESERVED_LABEL):
                add("ERROR", "labels", f"pool {pn}: label {label} is under a reserved domain")
        for t in pool.get("nodeTaints", []):
            if _under(t.get("key", ""), RESERVED_LABEL):
                add("ERROR", "taints", f"pool {pn}: taint key {t['key']} is under a reserved domain")
            if t.get("effect") == "NoExecute":
                add("WARN", "taints", f"pool {pn}: NoExecute also evicts DaemonSet pods that lack a toleration")
        if pool.get("nodeLabels") or pool.get("nodeTaints"):
            add("INFO", "immutable", f"pool {pn}: labels and taints are fixed at creation and applied once; change later with kubectl")
        if pool.get("recycleBudget", 0) == 0:
            add("INFO", "recycle", f"pool {pn}: recycleBudget 0 means auto mode marks no outdated nodes")
    return out


def main(argv):
    if len(argv) != 2:
        print("usage: c32_spec_lint.py SPEC.yaml", file=sys.stderr)
        return 2
    findings = lint(yaml.safe_load(Path(argv[1]).read_text()))
    for sev, rule, msg in findings:
        print(f"{sev:5} {rule}: {msg}")
    return 1 if any(s == "ERROR" for s, _, _ in findings) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
