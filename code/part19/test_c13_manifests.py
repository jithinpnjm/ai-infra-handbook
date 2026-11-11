"""Tests for the chapter 19.13 Kubernetes and Helm files: schema, structure, kubeconform when present."""
import copy
import json
import pathlib
import shutil
import subprocess

import pytest
import yaml

HERE = pathlib.Path(__file__).resolve().parent
jsonschema = pytest.importorskip("jsonschema")


def merge(a, b):
    for k, v in b.items():
        a[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return a


# The chart validates the MERGED values: chart defaults (a copy of its values.yaml) + our values.
CHART_DEFAULTS = yaml.safe_load((HERE / "c13_z2jh_chart_values.yaml").read_text())


@pytest.fixture(scope="module")
def schema():
    return json.loads((HERE / "c13_z2jh_values.schema.json").read_text())


@pytest.fixture(scope="module")
def values():
    return yaml.safe_load((HERE / "c13_jupyterhub_values.yaml").read_text())


def errors(schema, vals):
    merged = merge(copy.deepcopy(CHART_DEFAULTS), copy.deepcopy(vals))
    return [e.message for e in jsonschema.Draft7Validator(schema).iter_errors(merged)]


def test_values_pass_the_chart_schema(schema, values):
    assert errors(schema, values) == []


def test_schema_rejects_a_misspelled_key(schema, values):
    bad = copy.deepcopy(values)
    bad["cull"]["timeOut"] = 10
    assert any("timeOut" in e for e in errors(schema, bad))


def test_schema_rejects_wrong_type(schema, values):
    bad = copy.deepcopy(values)
    bad["cull"]["timeout"] = "an hour"
    assert errors(schema, bad)


def test_notebook_policy_numbers(values):
    assert values["cull"]["timeout"] == 1800 and values["cull"]["every"] == 300
    km = values["singleuser"]["extraFiles"]["jupyter_server_config.json"]["data"]["MappingKernelManager"]
    assert km["cull_idle_timeout"] == 1200 and km["cull_busy"] is False
    assert values["scheduling"]["userPlaceholder"]["replicas"] == 2


def test_no_secret_in_values(values):
    text = (HERE / "c13_jupyterhub_values.yaml").read_text()
    assert "client_secret" not in text and "cookieSecret" not in text


def test_gpu_profiles_use_extra_resource_limits(values):
    gpu = [p for p in values["singleuser"]["profileList"] if "kubespawner_override" in p]
    assert gpu and all("extra_resource_limits" in p["kubespawner_override"] for p in gpu)


def load_all(name):
    return [d for d in yaml.safe_load_all((HERE / name).read_text()) if d]


def test_mlflow_deployment_flags_and_probes():
    dep = next(d for d in load_all("c13_mlflow.yaml") if d["kind"] == "Deployment")
    c = dep["spec"]["template"]["spec"]["containers"][0]
    assert c["command"] == ["mlflow", "server"]
    assert "--serve-artifacts" in c["args"] and any(a.startswith("--artifacts-destination=s3://") for a in c["args"])
    assert any(a.startswith("--allowed-hosts=") for a in c["args"])
    assert c["readinessProbe"]["httpGet"]["path"] == "/health"
    assert dep["spec"]["replicas"] >= 2


def test_mlflow_has_no_inline_credentials():
    text = (HERE / "c13_mlflow.yaml").read_text()
    assert "postgresql://" not in text and text.count("secretKeyRef") == 3


def test_queues_sum_to_batch_pool_and_share_a_cohort():
    cqs = [d for d in load_all("c13_research_queues.yaml") if d["kind"] == "ClusterQueue"]
    quotas = [cq["spec"]["resourceGroups"][0]["flavors"][0]["resources"][0]["nominalQuota"] for cq in cqs]
    assert sum(quotas) == 56 and len(cqs) == 4
    assert {cq["spec"]["cohortName"] for cq in cqs} == {"research"}
    assert all(cq["spec"]["preemption"]["reclaimWithinCohort"] == "Any" for cq in cqs)


def test_notebook_quota_matches_the_pool_split():
    q = next(d for d in load_all("c13_notebook_quota.yaml") if d["kind"] == "ResourceQuota")
    assert q["spec"]["hard"]["requests.nvidia.com/gpu"] == "8"


@pytest.mark.skipif(shutil.which("kubeconform") is None, reason="kubeconform not installed")
def test_kubeconform_accepts_core_manifests():
    r = subprocess.run(["kubeconform", "-strict", "-summary", str(HERE / "c13_mlflow.yaml"), str(HERE / "c13_notebook_quota.yaml")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("promtool") is None, reason="promtool not installed")
def test_promtool_accepts_idle_gpu_rules():
    r = subprocess.run(["promtool", "check", "rules", str(HERE / "c13_idle_gpu_rules.yml")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    rules = yaml.safe_load((HERE / "c13_idle_gpu_rules.yml").read_text())["groups"][0]["rules"]
    assert any(x.get("alert") == "ResearchGpuHeldIdle" and x["for"] == "30m" for x in rules)
