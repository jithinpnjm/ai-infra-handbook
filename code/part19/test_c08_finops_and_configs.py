"""Tests for the cost calculator, rules, dashboard and the YAML files of Chapter 19.8."""
import json
import os
import pathlib
import shutil
import subprocess

import pytest
import yaml

import c08_finops as f
import c08_mig_planner as m

HERE = pathlib.Path(__file__).resolve().parent
H100 = f.EXAMPLE_PRODUCT


def _tool(name, env):
    if os.environ.get(env):
        return os.environ[env]
    return shutil.which(name) or shutil.which(name, path=str(pathlib.Path.home() / "go" / "bin"))


# ------------------------------------------------------------ cost maths


def test_weights_of_one_gpu_never_exceed_one():
    prof = m.profiles_for(H100)
    for names in (["7g.80gb"], ["4g.40gb", "3g.40gb"], ["3g.40gb"] * 2, ["1g.10gb"] * 7, ["2g.20gb"] * 3 + ["1g.10gb"], ["1g.20gb"] * 4):
        assert m.feasible([prof[n] for n in names]) is not None
        assert sum(f.blended_weight(prof[n]) for n in names) <= 1, names


def test_whole_gpu_slice_costs_the_whole_gpu():
    prof = m.profiles_for(H100)
    assert f.blended_weight(prof["7g.80gb"]) == 1
    assert f.slice_price(prof["7g.80gb"], 4.0) == 4.0


def test_chargeback_parts_add_up_to_the_node_cost():
    layout = f.node_layout()
    reserved = {t: {p: n} for t, p, n in f.TENANT_MIX}
    res = f.chargeback(layout, reserved, 4.0)
    total = sum(res["tenants"].values()) + res["idle"] + res["layout_loss"]
    assert total == pytest.approx(res["gpu_cost"])
    assert res["gpu_cost"] == pytest.approx(4.0 * 730 * 8)


def test_worked_example_numbers_quoted_in_the_chapter():
    layout = f.node_layout()
    reserved = {t: {p: n} for t, p, n in f.TENANT_MIX}
    res = f.chargeback(layout, reserved, 4.0)
    assert round(res["tenants"]["search-embeddings"], 2) == 3910.71
    assert round(res["tenants"]["chat-llm"], 2) == 5422.86
    assert round(res["tenants"]["notebooks"], 2) == 4692.86
    assert round(res["tenants"]["finetune"], 2) == 3128.57
    assert round(res["tenants"]["batch-eval"], 2) == 2920.00
    assert round(res["idle"], 2) == 2346.43
    assert round(res["layout_loss"], 2) == 938.57
    assert res["offered"] == {"7g.80gb": 1, "4g.40gb": 2, "3g.40gb": 4, "2g.20gb": 6, "1g.10gb": 16}


def test_idle_cost_is_exactly_the_six_spare_slices():
    layout = f.node_layout()
    reserved = {t: {p: n} for t, p, n in f.TENANT_MIX}
    res = f.chargeback(layout, reserved, 4.0)
    spare = 6 * f.slice_price(layout.profiles["1g.10gb"], 4.0) * 730
    assert res["idle"] == pytest.approx(spare)


def test_fully_loaded_spreads_idle_but_keeps_layout_loss():
    layout = f.node_layout()
    reserved = {t: {p: n} for t, p, n in f.TENANT_MIX}
    res = f.chargeback(layout, reserved, 4.0)
    loaded = f.fully_loaded(res)
    assert sum(loaded.values()) == pytest.approx(sum(res["tenants"].values()) + res["idle"])
    assert all(loaded[t] > res["tenants"][t] for t in loaded)


def test_over_reservation_is_refused():
    layout = f.node_layout()
    with pytest.raises(ValueError, match="only 4 offered"):
        f.chargeback(layout, {"a": {"3g.40gb": 5}}, 4.0)
    with pytest.raises(ValueError, match="does not offer"):
        f.chargeback(layout, {"a": {"1g.20gb": 1}}, 4.0)
    with pytest.raises(ValueError):
        f.chargeback(layout, {"a": {"3g.40gb": 1}}, -1.0)


def test_utilisation_raises_cost_per_busy_hour():
    assert f.cost_per_busy_hour(1.857, 1.0) == pytest.approx(1.857)
    assert f.cost_per_busy_hour(1.857, 0.25) == pytest.approx(7.428)
    with pytest.raises(ValueError):
        f.cost_per_busy_hour(1.0, 0)


def test_demand_that_does_not_fit_stops_the_layout_builder():
    with pytest.raises(m.PlannerError):
        f.node_layout(demand=[("t", "7g.80gb", 9)])


# ------------------------------------------------------------ generated files equal committed files


def test_committed_rules_and_dashboard_match_the_generator():
    rules, dash = f.render_files()
    assert (HERE / "c08_mig_rules.yml").read_text() == rules
    assert (HERE / "c08_finops_mig_dashboard.json").read_text() == dash


def test_dashboard_is_valid_json_with_unique_panel_ids():
    d = json.loads((HERE / "c08_finops_mig_dashboard.json").read_text())
    ids = [p["id"] for p in d["panels"]]
    assert len(ids) == len(set(ids)) == 10
    assert all(p["targets"][0]["expr"] for p in d["panels"])


PROMTOOL = _tool("promtool", "PROMTOOL")


@pytest.mark.skipif(not PROMTOOL, reason="promtool not installed")
def test_every_promql_expression_in_the_dashboard_parses(tmp_path):
    d = json.loads((HERE / "c08_finops_mig_dashboard.json").read_text())
    exprs = f.expressions(d)
    assert len(exprs) == 10
    rules = {"groups": [{"name": "x", "rules": [{"record": f"test:expr{i}", "expr": e} for i, e in enumerate(exprs)]}]}
    p = tmp_path / "exprs.yml"
    p.write_text(yaml.safe_dump(rules))
    r = subprocess.run([PROMTOOL, "check", "rules", str(p)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.skipif(not PROMTOOL, reason="promtool not installed")
def test_promtool_rejects_a_broken_expression(tmp_path):
    p = tmp_path / "bad.yml"
    p.write_text(yaml.safe_dump({"groups": [{"name": "x", "rules": [{"record": "t:bad", "expr": "sum by (team (up)"}]}]}))
    r = subprocess.run([PROMTOOL, "check", "rules", str(p)], capture_output=True, text=True)
    assert r.returncode != 0


@pytest.mark.skipif(not PROMTOOL, reason="promtool not installed")
def test_committed_rules_file_passes_promtool():
    r = subprocess.run([PROMTOOL, "check", "rules", str(HERE / "c08_mig_rules.yml")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


# ------------------------------------------------------------ mig-parted config


def _layout_from_yaml(path):
    cfg = yaml.safe_load(path.read_text())
    return cfg


def test_mig_parted_file_equals_planner_output():
    p = f.node_layout()
    assert (HERE / "c08_mig_parted_config.yaml").read_text() == m.mig_parted_yaml(p, "tenant-mix-v1")


def test_configmap_embeds_the_same_config():
    cm = yaml.safe_load((HERE / "c08_mig_config_configmap.yaml").read_text())
    assert cm["kind"] == "ConfigMap"
    assert "config.yaml" in cm["data"]  # NVIDIA: the key must be named config.yaml
    assert yaml.safe_load(cm["data"]["config.yaml"]) == yaml.safe_load((HERE / "c08_mig_parted_config.yaml").read_text())


def test_every_gpu_in_the_mig_parted_config_is_a_feasible_geometry():
    cfg = yaml.safe_load((HERE / "c08_mig_parted_config.yaml").read_text())
    assert cfg["version"] == "v1"
    prof = m.profiles_for(H100)
    covered = []
    for entry in cfg["mig-configs"]["tenant-mix-v1"]:
        assert entry["mig-enabled"] is True
        names = [n for n, c in entry["mig-devices"].items() for _ in range(c)]
        assert m.feasible([prof[n] for n in names]) is not None, entry
        covered += entry["devices"]
    assert sorted(covered) == list(range(8))


def test_mig_parted_rules_reject_bad_files():
    """Mirror of the upstream rules: enabled needs mig-devices, disabled must have none."""
    bad_enabled = {"version": "v1", "mig-configs": {"x": [{"devices": "all", "mig-enabled": True}]}}
    assert not _mirror_valid(bad_enabled)
    bad_disabled = {"version": "v1", "mig-configs": {"x": [{"devices": "all", "mig-enabled": False, "mig-devices": {"1g.10gb": 1}}]}}
    assert not _mirror_valid(bad_disabled)
    assert not _mirror_valid({"version": "v2", "mig-configs": {"x": [{"devices": "all", "mig-enabled": False}]}})
    good = yaml.safe_load((HERE / "c08_mig_parted_config.yaml").read_text())
    assert _mirror_valid(good)


def _mirror_valid(spec):
    if spec.get("version") != "v1" or not spec.get("mig-configs"):
        return False
    for entries in spec["mig-configs"].values():
        if not entries:
            return False
        for e in entries:
            if "devices" not in e or "mig-enabled" not in e:
                return False
            if e["mig-enabled"] and "mig-devices" not in e:
                return False
            if not e["mig-enabled"] and e.get("mig-devices"):
                return False
    return True


VALIDATOR = os.environ.get("C08_MIGPARTED_VALIDATOR")


@pytest.mark.skipif(not VALIDATOR or not os.path.exists(VALIDATOR), reason="set C08_MIGPARTED_VALIDATOR to the built upstream validator (see chapter)")
def test_upstream_mig_parted_parser_accepts_and_rejects(tmp_path):
    ok = subprocess.run([VALIDATOR, str(HERE / "c08_mig_parted_config.yaml")], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout
    # the upstream parser checks structure and profile-name format, not whether a profile exists on a GPU
    for i, body in enumerate([
        'version: v1\nmig-configs:\n  x:\n    - devices: all\n      mig-enabled: true\n',
        'version: v1\nmig-configs:\n  x:\n    - devices: all\n      mig-enabled: false\n      mig-devices:\n        "1g.10gb": 1\n',
        'version: v1\nmig-configs:\n  x:\n    - devices: all\n      mig-enabled: true\n      mig-devices:\n        "bogus": 1\n',
        'version: v2\nmig-configs:\n  x:\n    - devices: all\n      mig-enabled: false\n',
    ]):
        bad = tmp_path / f"bad{i}.yaml"
        bad.write_text(body)
        r = subprocess.run([VALIDATOR, str(bad)], capture_output=True, text=True)
        assert r.returncode != 0, body


# ------------------------------------------------------------ Kueue, quota and workload YAML agree with the layout


def _docs(name):
    return [d for d in yaml.safe_load_all((HERE / name).read_text()) if d]


def test_kueue_nominal_quotas_equal_the_slices_the_node_offers():
    offered = f.node_layout()
    counts = {}
    for g in offered.gpus:
        for pr in g.profiles():
            counts["nvidia.com/mig-" + pr.name] = counts.get("nvidia.com/mig-" + pr.name, 0) + 1
    quota = {}
    for d in _docs("c08_kueue_mig.yaml"):
        if d["kind"] != "ClusterQueue":
            continue
        for rg in d["spec"]["resourceGroups"]:
            for fl in rg["flavors"]:
                for r in fl["resources"]:
                    if r["name"].startswith("nvidia.com/mig-"):
                        quota[r["name"]] = quota.get(r["name"], 0) + r["nominalQuota"]
    assert quota == counts


def test_only_the_spare_queue_lends_and_only_search_borrows():
    lend, borrow = [], []
    for d in _docs("c08_kueue_mig.yaml"):
        if d["kind"] != "ClusterQueue":
            continue
        for rg in d["spec"]["resourceGroups"]:
            for fl in rg["flavors"]:
                for r in fl["resources"]:
                    if "lendingLimit" in r:
                        lend.append(d["metadata"]["name"])
                    if "borrowingLimit" in r:
                        borrow.append((d["metadata"]["name"], r["borrowingLimit"]))
    assert lend == ["cq-platform-spare"]
    assert borrow == [("cq-search", 6)]


def test_flavor_label_matches_the_mig_parted_config_name():
    flavor = next(d for d in _docs("c08_kueue_mig.yaml") if d["kind"] == "ResourceFlavor")
    cfg = yaml.safe_load((HERE / "c08_mig_parted_config.yaml").read_text())
    assert flavor["spec"]["nodeLabels"]["nvidia.com/mig.config"] in cfg["mig-configs"]


def test_every_local_queue_points_at_an_existing_cluster_queue():
    docs = _docs("c08_kueue_mig.yaml")
    cqs = {d["metadata"]["name"] for d in docs if d["kind"] == "ClusterQueue"}
    lqs = [d for d in docs if d["kind"] == "LocalQueue"]
    assert len(lqs) == 5
    assert all(lq["spec"]["clusterQueue"] in cqs for lq in lqs)


def test_resource_quota_matches_cluster_queue_plus_borrowing():
    cq_quota = {}
    for d in _docs("c08_kueue_mig.yaml"):
        if d["kind"] == "ClusterQueue" and d["metadata"]["name"] != "cq-platform-spare":
            ns = d["spec"]["namespaceSelector"]["matchLabels"]["kubernetes.io/metadata.name"]
            for fl in d["spec"]["resourceGroups"][0]["flavors"]:
                for r in fl["resources"]:
                    if r["name"].startswith("nvidia.com/"):
                        cq_quota[ns] = (r["name"], r["nominalQuota"] + r.get("borrowingLimit", 0))
    rq = {}
    for d in _docs("c08_namespaces_quota.yaml"):
        if d["kind"] == "ResourceQuota":
            (k, v), = d["spec"]["hard"].items()
            assert k.startswith("requests.nvidia.com/mig-")  # extended resources: requests. prefix only
            rq[d["metadata"]["namespace"]] = (k[len("requests."):], int(v))
    assert rq == cq_quota


def test_workload_requests_a_resource_its_queue_covers():
    job = _docs("c08_mig_workload.yaml")[0]
    assert job["metadata"]["labels"]["kueue.x-k8s.io/queue-name"] == "main"
    res = job["spec"]["template"]["spec"]["containers"][0]["resources"]
    (name,) = [k for k in res["limits"] if k.startswith("nvidia.com/")]
    cq = next(d for d in _docs("c08_kueue_mig.yaml") if d["metadata"]["name"] == "cq-chat")
    covered = cq["spec"]["resourceGroups"][0]["coveredResources"]
    assert name in covered
    assert {"cpu", "memory"} <= set(covered)  # Kueue rejects requests for resources the queue does not cover
    assert set(res["requests"]) <= set(covered)


def test_workload_for_an_uncovered_profile_would_be_refused():
    cq = next(d for d in _docs("c08_kueue_mig.yaml") if d["metadata"]["name"] == "cq-chat")
    covered = cq["spec"]["resourceGroups"][0]["coveredResources"]
    assert "nvidia.com/mig-1g.10gb" not in covered


KUBECONFORM = _tool("kubeconform", "KUBECONFORM")


@pytest.mark.skipif(not KUBECONFORM, reason="kubeconform not installed")
def test_core_manifests_pass_kubeconform():
    files = [HERE / n for n in ("c08_namespaces_quota.yaml", "c08_mig_workload.yaml", "c08_mig_config_configmap.yaml")]
    r = subprocess.run([KUBECONFORM, "-strict", "-ignore-missing-schemas", "-summary", *map(str, files)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
