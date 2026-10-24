#!/usr/bin/env python3
"""Self-checking lab for chapter 8.9: Kubernetes-under-BCM rules from the Containerization Manual, tested in bcm_k8s.py."""
import sys
import bcm_k8s as k

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except k.K8sError:
        return True

def main():
    # etcd and plan
    check("etcd fault tolerance: 1->0, 3->1, 4->1, 5->2", [k.etcd_fault_tolerance(n) for n in (1, 3, 4, 5)] == [0, 1, 1, 2])
    check("3 and 4 etcd nodes both survive one failure, so the 4th adds cost only", k.etcd_fault_tolerance(3) == k.etcd_fault_tolerance(4))
    res = {n: (64, 16) for n in ("head", "n1", "n2", "w1", "w2")}
    ok = k.plan_problems(["head", "n1", "n2"], ["head", "n1"], ["w1", "w2"], res)
    check("3 etcd + 2 control plane + enough resources: no problems", ok == [])
    p = k.plan_problems(["head", "n1"], ["head"], ["w1"], res)
    check("2 etcd nodes (even, fewer than 3) and 1 control plane node are flagged", len(p) >= 3 and any("even" in x for x in p) and any("control plane" in x for x in p), p)
    res2 = dict(res, w1=(8, 4))
    check("a worker with 8 GB RAM is below the 16 GB minimum", any("w1" in x and "16 GB" in x for x in k.plan_problems(["head", "n1", "n2"], ["head", "n1"], ["w1"], res2)))
    check("nodes of another Kubernetes cluster cannot be shared", any("another Kubernetes cluster" in x for x in k.plan_problems(["head", "n1", "n2"], ["head", "n1"], ["w1"], res, other_clusters=["w1"])))

    # networks and Typha
    check("a /16 pod network gives 256 per-node /24 ranges: at most 256 nodes", k.pod_network_capacity("172.29.0.0/16") == 256)
    check("a /20 pod network allows only 16 nodes", k.pod_network_capacity("172.29.0.0/20") == 16)
    check("a pod network smaller than one /24 is refused", raises(lambda: k.pod_network_capacity("172.29.0.0/26")))
    check("overlapping service and pod networks are reported", k.networks_overlap("10.150.0.0/16", "10.150.4.0/22") and not k.networks_overlap("10.150.0.0/16", "172.29.0.0/16", ["10.141.0.0/16"]))
    check("Typha: none up to 50 nodes", k.typha_replicas(50) == 0)
    check("Typha: at least 3 replicas above 50 nodes", k.typha_replicas(51) == 3 and k.typha_replicas(300) == 3)
    check("Typha: one per 150 nodes, max 20", k.typha_replicas(1000) == 7 and k.typha_replicas(100000) == 20)
    check("the wizard offers Calico and Flannel", k.CNI_CHOICES == {"calico", "flannel"})

    # operators
    check("four operators are selected by default; the GPU operator is not one", k.DEFAULT_OPERATORS == {"Kgateway", "Kubernetes Metrics Server", "Kubernetes State Metrics", "MetalLB"} and "NVIDIA GPU Operator" not in k.DEFAULT_OPERATORS)
    check("a GPU cluster without the GPU operator is flagged", any("GPU Operator" in x for x in k.operator_problems(k.DEFAULT_OPERATORS, True)))
    check("no Kyverno is flagged as node-level exposure", any("privileged" in x for x in k.operator_problems({"NVIDIA GPU Operator"}, True, kyverno_installed=False)))
    v = k.gpu_operator_values()
    check("GPU operator defaults: toolkit on, driver off, NFD on", v["toolkit.enabled"] and not v["driver.enabled"] and v["nfd.enabled"])
    check("the three options are independent", len({tuple(sorted(k.gpu_operator_values(a, False, c).items(), key=str)) for a in (True, False) for c in (True, False)}) == 4)
    check("on DGX OS the driver container is refused", raises(lambda: k.gpu_operator_values(driver=True, dgx_os=True)))
    check("toolkit off means containerd runtime-class drop-ins", "drop-ins" in k.gpu_operator_values(toolkit=False)["gpu access via"])
    g = k.kubelet_gpu_settings(True)
    check("GPU workers get static CPU manager and best-effort topology manager (BCM 11.34+)", g["cpuManagerPolicy"] == "static" and g["topologyManagerPolicy"] == "best-effort" and g["topologyManagerScope"] == "pod" and g["kubeReserved"] == {"cpu": "250m"})
    check("non-GPU workers and clusters deployed before 11.34 keep the defaults", k.kubelet_gpu_settings(False) == {} and k.kubelet_gpu_settings(True, (11, 33, 0)) == {})

    # overlays
    check("overlay priorities: etcd 500, master 510, worker 500, netq 501", [k.OVERLAYS[x][0] for x in ("kube-default-etcd", "kube-default-master", "kube-default-worker", "kube-default-netq")] == [500, 510, 500, 501])
    check("a node in both master and worker overlays takes the master (510) parameters", k.kubelet_mode(True, True) == ("control-plane", 510) and k.kubelet_mode(False, True) == ("worker", 500) and k.kubelet_mode(False, False) == (None, None))

    # users
    u = k.k8s_user("john")
    check("a new Kubernetes user gets namespace john-restricted, service account john, role edit, home hostPath", u["namespace"] == "john-restricted" and u["service_account"] == "john" and u["role"] == "edit" and u["paths"] == ["/home/john"])
    check("only view, edit, admin and cluster-admin are valid roles", raises(lambda: k.k8s_user("x", role="root")))
    check("a pod mounting the user's own home is admitted", k.pod_allowed(u, ["/home/john/data"])[0])
    ok_, why = k.pod_allowed(u, ["/etc"])
    check("a pod mounting /etc is denied by the hostPath policy", not ok_ and "hostPath" in why)
    check("privileged pods are denied", not k.pod_allowed(u, privileged=True)[0])
    check("running as another UID is denied by default", not k.pod_allowed(u, uid_is_user=False)[0])
    ua = k.k8s_user("jane", allow_all_uids=True, user_paths=["/home/jane", "/scratch"])
    check("--allow-all-uids lets a pod run as any UID when no hostPath is used", k.pod_allowed(ua, uid_is_user=False)[0])
    check("...but not together with a hostPath volume", not k.pod_allowed(ua, ["/scratch"], uid_is_user=False)[0])
    check("--user-paths adds /scratch for the same user", k.pod_allowed(ua, ["/scratch/x"])[0])
    check("without Kyverno nothing restricts the pod (the manual's warning)", k.pod_allowed(u, ["/etc"], privileged=True, kyverno=False)[0])
    check("Kyverno HA means 3 replicas", k.kyverno_replicas(True) == 3 and k.kyverno_replicas(False) == 1)

    # gateway
    check("the default Gateway IP is the highest free address on the node network (the manual's example: just below the head node)", k.gateway_default_ip("10.141.0.0/16", {"10.141.255.254"}) == "10.141.255.253")
    check("addresses in MetalLB pools or the dynamic range are skipped", k.gateway_default_ip("10.141.0.0/16", {"10.141.255.254", "10.141.255.200-10.141.255.253"}) == "10.141.255.199")
    check("installing only the Kgateway operator exposes nothing", not k.gateway_exposes_traffic(True, False) and k.gateway_exposes_traffic(True, True))
    check("the gateway path starts at the head node proxy on 443 and ends at the service", "443" in k.gateway_traffic_path()[1] and k.gateway_traffic_path()[-1] == "service")
    check("API server proxy port is 10443 on every node; etcd spool is /var/lib/etcd", k.PORTS["api_server_proxy"] == 10443 and k.PORTS["etcd_spool"] == "/var/lib/etcd")

    # NetQ, preflight, air gap
    check("NetQ prerequisites met: no problems", k.netq_prereq_problems(3, 300, 128, True, False, False) == [])
    bad = k.netq_prereq_problems(2, 100, 32, False, True, True)
    check("NetQ: 2 nodes, small disk and memory, old OS, Kyverno and default ports are all flagged", len(bad) == 6, bad)
    check("the five preflight checks each have a skip flag", set(k.PREFLIGHT) == {"dns", "ping", "mtu", "package manager", "kube version"} and all(v.startswith("--skip-") for v in k.PREFLIGHT.values()))
    req = {"kubeadm": "1.36.3", "kubectl": "1.36.3"}
    check("air-gap validation names each mismatching package (the manual's example)", k.airgap_version_problems(req, {"kubeadm": "1.34.10-1.1", "kubectl": "1.34.10-1.1"}) == ["kubeadm==1.36.3 (found: 1.34.10-1.1)", "kubectl==1.36.3 (found: 1.34.10-1.1)"])
    check("a matching bundle has no problems", k.airgap_version_problems(req, req) == [])

    # upgrade
    st = k.upgrade_steps(["node001", "node002"], ["node003", "node004"])
    check("upgrade order: first control plane node, other control plane nodes, workers, then BCM's recorded version", st[0].startswith("upgrade the first") and "node002" in st[1] and "worker node003" in st[2] and "update the Kubernetes version in BCM" in st[4])
    check("upgrade: etcd, CNI, CSI and runtimes are not covered by kubeadm and need separate action", "separately" in st[-1])

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
