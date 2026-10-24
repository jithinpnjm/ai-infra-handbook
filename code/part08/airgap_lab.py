#!/usr/bin/env python3
"""Self-checking lab for chapter 8.14: air-gapped BCM and Kubernetes rules from the manuals, tested in bcm_airgap.py."""
import sys
import bcm_airgap as a

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except a.AirgapError:
        return True

def main():
    check("BCM 11.32.0 and later may use the air-gapped upgrade procedure; 11.31.0 may not", a.bcm_version_ok_for_airgap_upgrade("11.32.0") and a.bcm_version_ok_for_airgap_upgrade("11.34.0") and not a.bcm_version_ok_for_airgap_upgrade("11.31.0"))
    check("BCM 10 needs 10.31.0 or later", a.bcm_version_ok_for_airgap_upgrade("10.31.0") and not a.bcm_version_ok_for_airgap_upgrade("10.30.0"))
    check("BCM 12 is outside the appendix", raises(lambda: a.bcm_version_ok_for_airgap_upgrade("12.0.0")))
    check("all nodes on 1.34: upgrade to 1.35 is fine", a.upgrade_target_problems(["1.34.7", "1.34.7"], "1.35.1") == [])
    check("skipping a minor (1.34 to 1.36) violates the skew policy", a.upgrade_target_problems(["1.34.7"], "1.36.0") != [])
    check("a patch upgrade stays in the minor", a.upgrade_kind("1.35.3", "1.35.4") == "patch" and a.upgrade_kind("1.34.9", "1.35.0") == "minor")
    check("nodes on 1.34 and 1.35: the only valid target is 1.35", a.upgrade_target_problems(["1.34.7", "1.35.1"], "1.35.3") == [] and a.upgrade_target_problems(["1.34.7", "1.35.1"], "1.36.0") != [])
    check("three minors at once (1.33, 1.34, 1.35) are not allowed", a.upgrade_target_problems(["1.33.0", "1.34.0", "1.35.0"], "1.35.0") != [])

    full = {d: ["f"] for d in a.BUNDLE_DIRS}
    check("a complete bundle has files in all seven categories", a.bundle_problems(full) == [] and len(a.BUNDLE_DIRS) == 7)
    check("a category with no FILES (even if its directory exists) is flagged for re-download", a.bundle_problems(dict(full, **{"k8s-images": []})) == ["k8s-images"])
    check("the working directory needs about 9 GB, or upwards of 20 GB with Run:ai", a.workdir_gb() < 10 and a.workdir_gb(True) >= 20)
    check("Docker Hub: 100 pulls per 6 h unauthenticated, 200 authenticated", a.dockerhub_pull_windows(250, False) == 3 and a.dockerhub_pull_windows(250, True) == 2)
    check("mixed architecture clusters need a customised approach; a matching host is fine", not a.arch_ok("amd64", "amd64", mixed_cluster=True)[0] and a.arch_ok("amd64", "amd64")[0] and not a.arch_ok("amd64", "arm64")[0])
    check("helm 3.x is right for the download host; 4.x is not (as of the manual)", a.helm_version_ok("3.20.2") and not a.helm_version_ok("4.2.3"))

    check("the procedure has 13 steps and starts with node assignment", len(a.STEPS) == 13 and a.STEPS[0].startswith("assign"))
    good = list(range(13))
    check("the documented order has no dependency problems", a.order_problems(good) == [], a.order_problems(good))
    bad = [0, 1, 2, 3, 8, 9, 10, 11]
    check("pushing images before the registry exists is flagged", any("step 8" in x for x in a.order_problems(bad)))
    check("deploying before images, charts and CRDs are in place is flagged", any("step 11" in x for x in a.order_problems([0, 1, 2, 3, 4, 5, 6, 11])))
    check("Run:ai setup before Kubernetes is deployed is flagged", any("step 12" in x for x in a.order_problems([12])))
    check("Ubuntu: extracting under /root fails because _apt cannot read it; /tmp is fine; Rocky can use /root", not a.extraction_dir_ok("ubuntu24.04", "/root/airgapped") and a.extraction_dir_ok("ubuntu24.04", "/tmp/airgapped") and a.extraction_dir_ok("rocky9", "/root/airgapped"))
    check("never run the wizard on the passive head or use --force", len(a.passive_head_problems(True, True)) == 2 and a.passive_head_problems(False) == [])
    check("a GPU operator version is installable only if its chart was downloaded", a.gpu_operator_available("v26.3.0", {"v26.3.0"}) and not a.gpu_operator_available("v25.10.1", {"v26.3.0"}))

    check("Run:ai has 14 dependency operators listed and 5 pre-air-gap prerequisites", len(a.RUNAI_DEPENDENCIES) == 14 and len(a.RUNAI_PRE_AIRGAP) == 5)
    ok = a.runai_problems("ubuntu24.04", "2.25.11", a.RUNAI_DEPENDENCIES, True)
    check("Run:ai on Ubuntu 2.25.11 with all operators and prerequisites: no problems", ok == [])
    p = a.runai_problems("rhel9", "2.22.0", ["MetalLB"], False)
    check("Run:ai on RHEL, an old version, missing operators and missing prerequisites are all flagged", len(p) == 4, p)
    check("the .sha256 file needs the file name appended for sha256sum -c", not a.sha256_line_ok("abcdef0123", "pkg.deb") and a.sha256_line_ok("abcdef0123  pkg.deb", "pkg.deb"))
    check("trusted=yes on a file: repository is acceptable, on an http repository it is not", a.apt_local_repo_line_problems("deb [trusted=yes] file:/mnt1/ubuntu noble main") == [] and a.apt_local_repo_line_problems("deb [trusted=yes] http://mirror/ubuntu noble main"))
    check("four offline options are listed (DOCA, mysql, create-image, RHEL installer)", len(a.offline_options()) == 4 and "--cmdvd" in a.offline_options()["DOCA OFED"])

    # Gap pass: Appendix C.4 step-by-step kubeadm upgrade checks
    check("C.4.1: the first control-plane node runs 'kubeadm upgrade apply v1.33.6 --kubeconfig=...' (p. 216)",
          a.c4_control_plane_upgrade_cmd(True, "v1.33.6") == "kubeadm upgrade apply v1.33.6 --kubeconfig=/root/.kube/config-default")
    check("C.4: subsequent control-plane nodes run 'kubeadm upgrade node --kubeconfig ...' without a version argument (p. 217)",
          a.c4_control_plane_upgrade_cmd(False, "v1.33.6") == "kubeadm upgrade node --kubeconfig /root/.kube/config-default")
    check("C.4.1: imageupdate without -w is a dry-run and is rejected for node binary upgrade (p. 215)",
          raises(lambda: a.c4_worker_upgrade_steps("worker001", write_flag=False)))
    w_steps = a.c4_worker_upgrade_steps("worker001", "default", write_flag=True)
    check("C.4 worker upgrade: drain -> imageupdate -w --wait -> kubeadm upgrade node -> daemon-reload -> restart kubelet -> uncordon (pp. 217-218)",
          len(w_steps) == 6 and w_steps[0].startswith("head: kubectl drain") and "kubeadm upgrade node" in w_steps[2] and w_steps[-1].startswith("head: kubectl uncordon"))
    check("C.4.1 validation: kube-apiserver pod Image: points to master.cm.cluster:5000/kube-apiserver:v1.33.6 (p. 217)",
          a.c4_apiserver_image_matches("Image: master.cm.cluster:5000/kube-apiserver:v1.33.6") and
          not a.c4_apiserver_image_matches("Image: registry.k8s.io/kube-apiserver:v1.32.10"))
    check("C.4.1 skew rule allows jumping from 1.32.10 directly to 1.33.6 without applying 1.32.11 first (p. 216)",
          a.upgrade_target_problems(["1.32.10", "1.32.10"], "1.33.6") == [])

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
