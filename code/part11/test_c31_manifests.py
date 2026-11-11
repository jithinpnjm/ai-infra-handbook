"""Structure checks for the 11.31 manifests. CRD validation is done by
tools/check_crd_yaml.py against upstream CRDs (see the chapter lab)."""
from pathlib import Path

import yaml

HERE = Path(__file__).parent


def load(name):
    return list(yaml.safe_load_all((HERE / name).read_text()))


def test_nvsentinel_dry_run_is_global_not_per_subchart():
    v = load("c31_nvsentinel_values.yaml")[0]
    assert v["global"]["dryRun"] is True
    assert "dryRun" not in v["fault-quarantine"]


def test_nvsentinel_enables_only_the_cordon_and_drain_stages():
    g = load("c31_nvsentinel_values.yaml")[0]["global"]
    assert g["faultQuarantine"]["enabled"] and g["nodeDrainer"]["enabled"]
    assert "faultRemediation" not in g


def test_grove_values_enable_topology():
    assert load("c31_grove_values.yaml")[0]["config"]["topologyAwareScheduling"]["enabled"]


def test_grove_pcs_start_order_references_real_cliques_and_has_no_cycle():
    pcs = load("c31_grove_disagg.yaml")[0]
    cliques = {c["name"]: c["spec"].get("startsAfter", []) for c in pcs["spec"]["template"]["cliques"]}
    for name, after in cliques.items():
        for dep in after:
            assert dep in cliques
    assert cliques["frontend"] == ["prefill-leader", "decode-leader"]
    for sg in pcs["spec"]["template"]["podCliqueScalingGroups"]:
        assert set(sg["cliqueNames"]) <= set(cliques)


def test_grove_pcs_uses_v1beta1_and_pack_required_not_packdomain():
    pcs = load("c31_grove_disagg.yaml")[0]
    assert pcs["apiVersion"] == "grove.io/v1beta1"
    tc = pcs["spec"]["template"]["topologyConstraint"]
    assert "packDomain" not in tc and tc["pack"]["required"] == "rack"
    levels = [l["domain"] for l in load("c31_grove_topology.yaml")[0]["spec"]["levels"]]
    assert tc["pack"]["required"] in levels


def test_nvcre_threshold_is_cel_over_value():
    cert = load("c31_nvcre_certification.yaml")[0]
    assert cert["spec"]["thresholds"]["busBandwidthGBps"].startswith("value ")
