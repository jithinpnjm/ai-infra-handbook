"""Part 18 tests. Run: python3 -m pytest -q code/part18/test_part18.py"""
import json, os, shutil, subprocess, sys, stat
from pathlib import Path
import pytest, yaml
HERE = Path(__file__).parent; sys.path.insert(0, str(HERE))
import seclib as S

@pytest.fixture(autouse=True)
def sec(tmp_path, monkeypatch):
    monkeypatch.setenv("SEC_HOME", str(tmp_path / "sec")); monkeypatch.chdir(tmp_path); return tmp_path

COMPS = {"firmware": "fw-1.0", "bootloader": "grub-2.12", "kernel": "linux-6.8", "dpu": "doca-2.9", "cvm": "cvm-img-7"}

def node(name="gpu-node-1", comps=COMPS, fw=None):
    S.save_json(f"nodes/{name}/components.json", comps); S.save_json(f"nodes/{name}/firmware.json", fw or {"gpu_driver_fw": "550.54.14", "bmc": "2.1.0"})

# ---- measurement chain -------------------------------------------------------------
def test_chain_established_and_verified():
    import establish_chain as e, verify_chain as v
    node(); assert e.main(["--node", "gpu-node-1", "--output", "chain.json"]) == 0
    assert v.main(["--chain", "chain.json"]) == 0 and S.verify_audit()

def test_extend_is_order_dependent():
    a = S.extend(S.extend("0" * 64, S.sha(b"a")), S.sha(b"b")); b = S.extend(S.extend("0" * 64, S.sha(b"b")), S.sha(b"a")); assert a != b

def test_tampered_chain_detected(capsys):
    import establish_chain as e, verify_chain as v
    node(); e.main(["--node", "gpu-node-1", "--output", "chain.json"])
    d = json.load(open("chain.json")); d["steps"][2]["measurement"] = S.sha(b"evil-kernel"); json.dump(d, open("chain.json", "w"))
    assert v.main(["--chain", "chain.json"]) == 1 and "kernel" in capsys.readouterr().out

def test_golden_value_names_changed_component(capsys):
    import establish_chain as e, verify_chain as v
    node(); S.save_json("golden/gpu-node-1.json", {"kernel": S.sha(b"linux-6.7")})
    e.main(["--node", "gpu-node-1", "--output", "chain.json"]); assert v.main(["--chain", "chain.json"]) == 1 and "kernel: measurement differs from golden" in capsys.readouterr().out

def test_missing_component_refuses_chain():
    import establish_chain as e
    node(comps={k: v for k, v in COMPS.items() if k != "dpu"}); assert e.main(["--node", "gpu-node-1", "--output", "c.json"]) == 1

def test_forged_signature_rejected():
    import establish_chain as e, verify_chain as v
    node(); e.main(["--node", "gpu-node-1", "--output", "chain.json"]); d = json.load(open("chain.json")); d["signature"] = "0" * 64; json.dump(d, open("chain.json", "w"))
    assert v.main(["--chain", "chain.json"]) == 1

# ---- firmware lifecycle --------------------------------------------------------------
def test_fw_update_verify_rollback():
    import fw_update as u, fw_verify as v, fw_rollback as r, fw_bom_scan as b
    node(); assert u.main(["--node", "gpu-node-1", "--version", "550.54.15"]) == 0 and v.main(["--node", "gpu-node-1", "--expected-version", "550.54.15"]) == 0
    assert v.main(["--node", "gpu-node-1", "--expected-version", "550.54.14"]) == 1
    assert r.main(["--node", "gpu-node-1", "--previous-version", "999.0"]) == 1                 # never installed
    assert r.main(["--node", "gpu-node-1", "--previous-version", "550.54.14"]) == 0 and v.main(["--node", "gpu-node-1", "--expected-version", "550.54.14"]) == 0
    assert b.main(["--node", "gpu-node-1", "--output", "fw_bom/n.yaml"]) == 0 and {"name": "bmc", "version": "2.1.0"} in yaml.safe_load(open("fw_bom/n.yaml"))["components"]

def test_cve_correlation_uses_numeric_versions(tmp_path):
    import fw_cve_monitor as m
    node("a", fw={"gpu_driver_fw": "550.9.0"}); node("b", fw={"gpu_driver_fw": "550.54.15"})
    feed = [{"id": "CVE-X", "component": "gpu_driver_fw", "fixed_in": "550.54.15", "severity": "HIGH"}]; json.dump(feed, open("feed.json", "w"))
    assert m.main(["--vendor", "nvidia", "--feed", "feed.json", "--webhook", "https://hook.example"]) == 1       # 550.9.0 < 550.54.15 numerically (a string compare would get this wrong)
    w = S.load_json("webhook_outbox.json"); assert [h["node"] for h in w["payload"]] == ["a"]

# ---- threat modeling --------------------------------------------------------------------
def test_threat_pipeline(tmp_path):
    import asset_inventory as ai, attack_surface as at, threat_catalogue as tc, threat_catalogue_update as tu, risk_matrix as rm, schedule_workshop as sw, schedule_review as sr
    S.save_json("platform.json", {"assets": [{"name": "churn-model", "kind": "model", "data_class": "restricted", "owner": "ds"}, {"name": "ngc-key", "kind": "credential", "data_class": "confidential", "owner": "plat"}]})
    assert ai.main(["--platform", "p", "--output", "asset_inventory.yaml"]) == 0 and at.main(["--platform", "p", "--output", "attack_surface.md"]) == 0
    assert tc.main(["--scope", "AI", "--asset-inventory", "asset_inventory.yaml", "--output", "threat_catalogue.md"]) == 0
    assert tu.main(["--threat-id", "T-001", "--new-mitigation", "watermark"]) == 0 and "watermark" in open("threat_catalogue.md").read() and tu.main(["--threat-id", "T-999", "--new-mitigation", "x"]) == 1
    assert rm.main(["--threat-catalogue", "threat_catalogue.md", "--output", "risk.md"]) == 0
    top = open("risk.md").read().split("## Top threats")[1].splitlines()[1]; assert "churn-model" in top and "(score 15)" in top       # restricted model: 3 x 5, ranks first
    assert sw.main(["--date", "2024-04-15", "--time", "t", "--scope", "s", "--participants", "platform-team,security-team"]) == 0 and sw.main(["--date", "2024-04-15", "--time", "t", "--scope", "s", "--participants", "platform-team"]) == 1
    assert sr.main(["--threat-model", "threat_catalogue.md", "--date", "2024-07-15"]) == 0

def test_inventory_refuses_ownerless_asset():
    import asset_inventory as ai
    S.save_json("platform.json", {"assets": [{"name": "x", "kind": "model", "owner": ""}]}); assert ai.main(["--platform", "p", "--output", "o.yaml"]) == 1

# ---- lineage and audit ---------------------------------------------------------------------
def test_lineage_graph():
    import lineage_graph as lg
    S.save_json("lineage.json", {"models": {"churn-model-v6": {"dataset": "churn-v3", "run": "r6", "code_commit": "abc"}}, "datasets": {"churn-v3": {"sources": ["crm", "events"]}}})
    assert lg.main(["--model", "churn-model-v6", "--dataset", "churn-v3", "--output", "l.yaml"]) == 0 and yaml.safe_load(open("l.yaml"))["dataset_sources"] == ["crm", "events"]
    assert lg.main(["--model", "churn-model-v6", "--dataset", "other", "--output", "l.yaml"]) == 1 and lg.main(["--model", "nope", "--dataset", "d", "--output", "l.yaml"]) == 1

def test_audit_bucket_is_append_only(tmp_path):
    import audit_log as a
    p = a.write_audit_entry(str(tmp_path / "bucket"), {"who": "alice", "what": "read model"}); assert a.verify_entry(p)
    with pytest.raises(PermissionError): open(p, "w")                                       # read-only file
    e = json.loads(p.read_text()); e["event"]["who"] = "mallory"; q = tmp_path / "forged.json"; q.write_text(json.dumps(e)); assert not a.verify_entry(q)
    with pytest.raises(FileExistsError): a.write_to_bucket(str(tmp_path / "bucket"), json.loads(p.read_text()))

def test_audit_chain_tamper():
    for i in range(3): S.audit("e", i=i)
    assert S.verify_audit(); f = S.home() / "audit.log"; f.write_text(f.read_text().replace('"i": 0', '"i": 7')); assert not S.verify_audit()

# ---- manifests: real tools --------------------------------------------------------------------
def tool(name):
    p = shutil.which(name) or str(Path.home() / "go/bin" / name); return p if Path(p).exists() else None

K8S_KINDS = ("NetworkPolicy", "Role", "ClusterRole", "RoleBinding", "ServiceAccount", "Secret", "Deployment", "ValidatingAdmissionPolicy", "ValidatingAdmissionPolicyBinding", "Pod", "Namespace")

@pytest.mark.skipif(not tool("kubeconform"), reason="kubeconform not installed")
def test_core_manifests_pass_kubeconform():
    files = []
    for p in HERE.glob("*.yaml"):
        docs = [d for d in yaml.safe_load_all(p.read_text()) if isinstance(d, dict)]
        if docs and all(d.get("kind") in K8S_KINDS for d in docs): files.append(str(p))
    assert len(files) >= 8
    r = subprocess.run([tool("kubeconform"), "-strict", "-summary", *files], capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr

def test_workload_pinned_by_digest_and_restricted():
    d = yaml.safe_load((HERE / "workload.yaml").read_text()); c = d["spec"]["template"]["spec"]["containers"][0]
    assert "@sha256:" in c["image"] and c["securityContext"]["allowPrivilegeEscalation"] is False and c["securityContext"]["capabilities"]["drop"] == ["ALL"]

def test_default_deny_and_tls_port_policy():
    dd = yaml.safe_load((HERE / "networkpolicy_default_deny.yaml").read_text()); assert dd["spec"]["podSelector"] == {} and set(dd["spec"]["policyTypes"]) == {"Ingress", "Egress"}
    tls = yaml.safe_load((HERE / "networkpolicy_tls.yaml").read_text()); assert tls["spec"]["ingress"][0]["ports"][0]["port"] == 8443

def test_admission_policy_has_binding():
    docs = list(yaml.safe_load_all((HERE / "pss_admission.yaml").read_text())); kinds = [d["kind"] for d in docs]
    assert kinds == ["ValidatingAdmissionPolicy", "ValidatingAdmissionPolicyBinding"] and docs[1]["spec"]["policyName"] == docs[0]["metadata"]["name"]

def test_ci_scan_workflow_fails_on_high():
    w = yaml.safe_load((HERE / "cicd_scan.yaml").read_text()); steps = w["jobs"]["build-scan"]["steps"]
    assert any("--exit-code 1" in s.get("run", "") and "HIGH,CRITICAL" in s.get("run", "") for s in steps)
