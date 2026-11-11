"""Chart and collector tests for the observability capstone (Chapter 19.7).

Need helm and network access (charts are pulled at the pinned versions). The
OpenTelemetry validation also needs Docker and the pinned collector image.
Tests skip, with a reason, when a tool or the network is missing.
"""
import pathlib
import re
import shutil
import subprocess

import pytest
import yaml

HERE = pathlib.Path(__file__).resolve().parent
CHARTS = {
    "kube-prometheus-stack": ("https://prometheus-community.github.io/helm-charts", "93.1.1"),
    "dcgm-exporter": ("https://nvidia.github.io/dcgm-exporter/helm-charts", "4.9.0"),
    "loki": ("https://grafana.github.io/helm-charts", "7.5.0"),
    "opentelemetry-collector": ("https://open-telemetry.github.io/opentelemetry-helm-charts", "0.178.2"),
}
VALUES = {"kube-prometheus-stack": "c07_values_kps.yaml", "dcgm-exporter": "c07_values_dcgm.yaml",
          "loki": "c07_values_loki.yaml", "opentelemetry-collector": "c07_values_otel.yaml"}
OTEL_IMAGE = "otel/opentelemetry-collector-contrib:0.164.0"

pytestmark = pytest.mark.skipif(not shutil.which("helm"), reason="helm needed")


@pytest.fixture(scope="module")
def charts(tmp_path_factory):
    root = tmp_path_factory.mktemp("charts")
    for name, (repo, ver) in CHARTS.items():
        r = subprocess.run(["helm", "pull", name, "--repo", repo, "--version", ver,
                            "--untar", "--untardir", str(root)], capture_output=True, text=True)
        if r.returncode:
            pytest.skip(f"cannot pull {name} {ver}: {r.stderr.strip()[:100]}")
    return root


def template(charts, name, *extra):
    r = subprocess.run(["helm", "template", name if name != "opentelemetry-collector" else "otel-agent",
                        str(charts / name), "-n", "monitoring", "-f", str(HERE / VALUES[name]),
                        "--api-versions", "monitoring.coreos.com/v1", *extra],
                       capture_output=True, text=True)
    return r


@pytest.mark.parametrize("name", list(CHARTS))
def test_values_render(charts, name):
    r = template(charts, name)
    assert r.returncode == 0, r.stderr
    kinds = [d["kind"] for d in yaml.safe_load_all(r.stdout) if d]
    assert kinds


def test_chart_versions_match_the_pins(charts):
    for name, (_, ver) in CHARTS.items():
        meta = yaml.safe_load((charts / name / "Chart.yaml").read_text())
        assert meta["version"] == ver


def test_loki_render_fails_on_a_non_string_deployment_mode(charts):
    r = subprocess.run(["helm", "template", "loki", str(charts / "loki"), "-f", str(HERE / VALUES["loki"]),
                        "--set", "deploymentMode=5"], capture_output=True, text=True)
    assert r.returncode != 0


def test_kps_wires_alertmanager_secret_and_selectors(charts):
    docs = [d for d in yaml.safe_load_all(template(charts, "kube-prometheus-stack").stdout) if d]
    am = next(d for d in docs if d["kind"] == "Alertmanager")
    assert am["spec"]["configSecret"] == "alertmanager-gpu-platform"
    assert am["spec"]["secrets"] == ["alertmanager-receivers"]
    p = next(d for d in docs if d["kind"] == "Prometheus")
    assert p["spec"]["serviceMonitorSelector"] == {} and p["spec"]["ruleSelector"] == {}
    assert p["spec"]["enforcedSampleLimit"] == 100000
    assert p["spec"]["enforcedLabelLimit"] == 30
    names = {r["alert"] for d in docs if d["kind"] == "PrometheusRule"
             for g in d["spec"]["groups"] for r in g["rules"] if "alert" in r}
    assert "Watchdog" in names and "KubeNodeNotReady" in names     # the names the route and inhibit rule use


def test_kps_output_is_valid_kubernetes(charts, tmp_path):
    if not shutil.which("kubeconform"):
        pytest.skip("kubeconform missing")
    f = tmp_path / "kps.yaml"
    f.write_text(template(charts, "kube-prometheus-stack").stdout)
    r = subprocess.run(["kubeconform", "-summary", "-ignore-missing-schemas", "-schema-location", "default",
                        "-schema-location",
                        "https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json",
                        str(f)], capture_output=True, text=True)
    out = r.stdout + r.stderr
    if "failed downloading" in out:
        pytest.skip("schemas not reachable")
    assert r.returncode == 0, out


def test_dcgm_chart_exports_every_field_the_platform_uses(charts):
    csv = (charts / "dcgm-exporter" / "files" / "default-counters.csv").read_text()
    exported = set(re.findall(r"^(DCGM_\w+)\s*,", csv, re.M))
    used = set()
    for f in ("c07_stack_rules.yaml", "c07_dashboard_gpu_platform.json", "c07_synth_exporter.py"):
        used |= set(re.findall(r"DCGM_FI_[A-Z_]+", (HERE / f).read_text()))
    assert used - exported == set(), used - exported
    assert len([ln for ln in csv.splitlines() if re.match(r"^DCGM_", ln) and ", label," not in ln]) == 26


def test_dcgm_servicemonitor_sets_the_node_label(charts):
    docs = [d for d in yaml.safe_load_all(template(charts, "dcgm-exporter").stdout) if d]
    sm = next(d for d in docs if d["kind"] == "ServiceMonitor")
    rel = sm["spec"]["endpoints"][0]["relabelings"]
    assert rel[0]["targetLabel"] == "node"
    svc = next(d for d in docs if d["kind"] == "Service")
    assert svc["metadata"]["name"] == "dcgm-exporter"


def _relay(charts):
    docs = [d for d in yaml.safe_load_all(template(charts, "opentelemetry-collector").stdout) if d]
    cm = next(d for d in docs if d["kind"] == "ConfigMap")
    return cm["data"]["relay"]


def _docker_ok():
    return shutil.which("docker") and subprocess.run(
        ["docker", "image", "inspect", OTEL_IMAGE], capture_output=True).returncode == 0


def _validate(path):
    return subprocess.run(["docker", "run", "--rm", "-e", "K8S_NODE_NAME=node1",
                           "-v", f"{path}:/etc/otelcol/config.yaml:ro", OTEL_IMAGE,
                           "validate", "--config=/etc/otelcol/config.yaml"],
                          capture_output=True, text=True)


@pytest.mark.skipif(not _docker_ok(), reason=f"docker image {OTEL_IMAGE} not available")
def test_rendered_collector_config_validates_and_a_broken_one_does_not(charts, tmp_path):
    relay = _relay(charts)
    good = tmp_path / "good.yaml"
    good.write_text(relay)
    assert _validate(good).returncode == 0
    bad = tmp_path / "bad.yaml"
    bad.write_text(relay.replace("memory_limiter,", "no_such_processor,", 1)
                   if "memory_limiter," in relay else relay.replace("- memory_limiter", "- no_such_processor", 1))
    assert _validate(bad).returncode != 0


def test_rendered_collector_pipelines(charts):
    cfg = yaml.safe_load(_relay(charts))
    pipes = cfg["service"]["pipelines"]
    assert set(pipes) == {"logs", "traces"}
    assert pipes["logs"]["processors"][0] == "memory_limiter"      # first, so backpressure reaches senders
    assert pipes["traces"]["processors"][-1] == "batch"
    assert cfg["exporters"]["otlp_http/loki"]["endpoint"].endswith(":3100/otlp")
    assert cfg["service"]["telemetry"]["metrics"]["readers"][0]["pull"]["exporter"]["prometheus"]["port"] == 8888
