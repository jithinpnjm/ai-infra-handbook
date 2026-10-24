#!/usr/bin/env python3
"""Self-checking lab for chapter 8.10: container runtimes and registries around BCM, tested in bcm_containers.py."""
import sys
import bcm_containers as c

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except c.CtrError:
        return True

def main():
    check("Slurm jobs with BCM support: Enroot+Pyxis", c.choose_runtime(True, False) == ["enroot+pyxis"])
    check("Slurm jobs without needing BCM support: Apptainer is the alternative", c.choose_runtime(True, False, want_bcm_support=False) == ["apptainer"])
    check("services: Kubernetes (containerd)", c.choose_runtime(False, True) == ["kubernetes (containerd)"])
    check("both worlds: both answers", c.choose_runtime(True, True) == ["enroot+pyxis", "kubernetes (containerd)"])
    check("neither: plain Docker (administrators and registry hosts)", c.choose_runtime(False, False) == ["docker"])
    check("only Enroot+Pyxis is integrated with Slurm by BCM", [k for k, v in c.RUNTIMES.items() if v["slurm_integration_in_bcm"]] == ["enroot+pyxis"])
    check("Docker and containerd run a (root) daemon; Enroot and Apptainer do not", c.RUNTIMES["docker"]["root_daemon"] and not c.RUNTIMES["enroot+pyxis"]["root_daemon"] and not c.RUNTIMES["apptainer"]["daemon"])
    check("BCM's manuals do not cover Apptainer", "not covered" in c.RUNTIMES["apptainer"]["set_up_by"])
    check("Docker Swarm is not supported", not c.docker_swarm_supported())
    check("after setup only root can run docker", c.docker_available_to("root") and not c.docker_available_to("alice"))

    d = c.DOCKER_DEFAULTS
    check("Docker role defaults: /var/lib/docker, overlay2, iptables on, TLS off, /etc/docker", d["spool"] == "/var/lib/docker" and d["storage backend"] == "overlay2" and d["iptables"] and not d["enable tls"] and d["certificates path"] == "/etc/docker")
    check("a clean Docker role has no problems", c.docker_role_problems(dict(d)) == [])
    check("a storage backend other than overlay2 is flagged", any("overlay2" in x for x in c.docker_role_problems({"storage backend": "btrfs"})))
    check("TLS on without CA, certificate and key is flagged three times", len(c.docker_role_problems({"enable tls": True})) == 3)
    check("verify TLS needs a CA", any("TLS CA" in x for x in c.docker_role_problems({"enable tls": True, "tls certificate": "c", "tls key": "k", "verify tls": True})))
    check("user namespace remap needs the kernel option and a reboot", any("user_namespace.enable=1" in x for x in c.docker_role_problems({"user namespace remap": "dockremap"})))
    check("an unknown log level is flagged", any("log level" in x for x in c.docker_role_problems({"log level": "loud"})))

    check("Harbor UI on the head node is on 9443 and Keycloak also needs 9443: a conflict", c.port_conflicts({"harbor": [c.HARBOR_UI_PORT], "keycloak": list(c.KEYCLOAK_PORTS)}) == [(9443, "harbor", "keycloak")])
    check("on different nodes there is no conflict", c.port_conflicts({"keycloak": list(c.KEYCLOAK_PORTS)}) == [])
    check("Docker Registry's default port is 5000", c.REGISTRY_DEFAULT_PORT == 5000)
    p = c.registry_problems("harbor", node_is_head=True)
    check("Harbor on the head node: default password and closed port are both flagged", len(p) == 2 and any("Harbor12345" in x for x in p) and any("9443" in x for x in p))
    check("Harbor with a changed password and an open port is clean", c.registry_problems("harbor", node_is_head=True, port_opened_on_head=True, password="s3cret") == [])
    check("a registry without datanode protection is flagged", any("datanode" in x for x in c.registry_problems("docker-registry", datanode=False)))
    check("the Docker Hub proxy mode is Docker Registry only", any("proxy" in x or "pull-through" in x for x in c.registry_problems("harbor", password="x", as_hub_proxy=True)))
    check("a proxy mirror URL without a port is flagged", any("port" in x for x in c.registry_problems("docker-registry", as_hub_proxy=True, mirror_url="https://node001")) and not c.registry_problems("docker-registry", as_hub_proxy=True, mirror_url="https://node001:5000"))
    check("an unknown registry kind is refused", raises(lambda: c.registry_problems("quay")))
    check("four remedies for Docker Hub rate limits are listed", len(c.DOCKERHUB_RATE_LIMIT_REMEDIES) == 4)
    check("the Harbor pull secret command names the server and user", "--docker-server=node001:9443" in c.harbor_pull_secret("node001:9443", "admin"))

    good = "machine nvcr.io login $oauthtoken password T\nmachine authn.nvidia.com login $oauthtoken password T\n"
    check("NGC credentials with both machines are clean", c.enroot_credentials_problems(good) == [])
    check("NGC credentials missing authn.nvidia.com are flagged (the common failure)", any("authn.nvidia.com" in x for x in c.enroot_credentials_problems("machine nvcr.io login $oauthtoken password T\n")))
    check("Docker Hub needs registry-1.docker.io", any("registry-1.docker.io" in x for x in c.enroot_credentials_problems(good, uses_ngc=False, uses_dockerhub=True)))
    check("in sbatch the # of an NGC image must be escaped", c.sbatch_container_image("nvcr.io#nvidia/pytorch:21.12-py3") == "nvcr.io\\#nvidia/pytorch:21.12-py3")
    check("small jobs can use a registry URI; larger ones import once to shared storage", "registry" in c.image_distribution(2) and "shared storage" in c.image_distribution(64))
    check("apptainer exec --nv exposes GPUs", c.apptainer_gpu_command("app.sif", "python train.py") == "apptainer exec --nv app.sif python train.py" and "--nv" not in c.apptainer_gpu_command("app.sif", "ls", gpus=False))
    check("Apptainer on BCM is a do-it-yourself list that ends with owning the support", c.apptainer_on_bcm_steps()[-1].startswith("own the support"))

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
