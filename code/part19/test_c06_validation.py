"""Cross-checks for the chapter 19.6 files: metric names, rules, Alertmanager, chapter blocks."""
import csv
import pathlib
import re
import shutil
import subprocess

import pytest
import yaml

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parents[1]
CHAPTER = ROOT / "docs/part-19-capstone/06-capstone-node-health-automation-with-dcgm-and-an-operator.md"
GO_BIN = pathlib.Path.home() / "go/bin"
PROMTOOL = shutil.which("promtool") or str(GO_BIN / "promtool")
AMTOOL = shutil.which("amtool") or str(GO_BIN / "amtool")
# Names from older exporter files that the chapter mentions only to say "do not use".
LEGACY_NAMES_ALLOWED_IN_PROSE = {
    "DCGM_FI_DEV_GPU_UTIL", "DCGM_FI_DEV_XID_ERRORS", "DCGM_FI_DEV_FB_USED", "DCGM_FI_DEV_FB_TOTAL",
    "DCGM_FI_DEV_ROW_REMAP_FAILURE", "DCGM_FI_DEV_THERMAL_VIOLATION", "DCGM_FI_DEV_POWER_USAGE",
    "DCGM_FI_DEV_CLOCK_THROTTLE_REASONS", "DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL",
    "DCGM_FI_DEV_GPU_TEMP", "DCGM_FI_DEV_SM_CLOCK",
}


LAB_COMMANDS = {"cd", "promtool", "amtool", "python3", "go", "KUBEBUILDER_ASSETS=\"<path", "kubectl", "curl"}


def snapshot():
    rows = {}
    for line in (HERE / "c06_dcgm_exporter_4_9_0_metrics.tsv").read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        name, mtype, state = line.split("\t")
        rows[name] = (mtype, state)
    return rows


def rules():
    doc = yaml.safe_load((HERE / "c06_node_health_alerts.yml").read_text())
    return [r for g in doc["groups"] for r in g["rules"]]


def counters():
    out = {}
    for line in (HERE / "c06_dcgm_counters.csv").read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = [p.strip() for p in line.split(",", 2)]
        assert len(parts) == 3, line
        out[parts[0]] = (parts[1], parts[2])
    return out


def test_every_metric_in_the_rules_exists_in_the_exporter_snapshot():
    snap = snapshot()
    used = set()
    for r in rules():
        used |= set(re.findall(r"DCGM_[A-Z0-9_]+", r["expr"]))
    assert used, "rules must use DCGM metrics"
    assert used <= set(snap), used - set(snap)


def test_every_dcgm_metric_in_the_rules_is_enabled_in_the_counters_file():
    used = set()
    for r in rules():
        used |= set(re.findall(r"DCGM_[A-Z0-9_]+", r["expr"]))
    assert used <= set(counters()), used - set(counters())


def test_counters_file_matches_the_snapshot_types_and_every_row_is_used():
    snap, used = snapshot(), set()
    for r in rules():
        used |= set(re.findall(r"DCGM_[A-Z0-9_]+", r["expr"]))
    for name, (mtype, _help) in counters().items():
        assert name in snap and snap[name][0] == mtype
        assert name in used, f"{name} is enabled but no rule uses it"


def test_counters_that_are_off_by_default_are_the_ones_the_chapter_says():
    off = sorted(n for n in counters() if snapshot()[n][1] == "commented")
    assert off == ["DCGM_FI_DEV_ECC_DBE_VOL_TOTAL", "DCGM_FI_DEV_ECC_SBE_VOL_TOTAL",
                   "DCGM_FI_DEV_GPU_POWER_THROTTLE_SECONDS_TOTAL",
                   "DCGM_FI_DEV_GPU_THERMAL_THROTTLE_SECONDS_TOTAL", "DCGM_FI_DEV_NVLINK_CRC_ERROR_TOTAL"]


def test_legacy_names_are_not_in_the_snapshot():
    snap = snapshot()
    for name in ("DCGM_FI_DEV_GPU_UTIL", "DCGM_FI_DEV_XID_ERRORS", "DCGM_FI_DEV_FB_USED",
                 "DCGM_FI_DEV_ROW_REMAP_FAILURE", "DCGM_FI_DEV_THERMAL_VIOLATION"):
        assert name not in snap


def test_every_rule_has_severity_event_class_and_a_test_case():
    tests = yaml.safe_load((HERE / "c06_node_health_alerts_test.yml").read_text())["tests"]
    tested = {a["alertname"] for t in tests for a in t.get("alert_rule_test", [])}
    for r in rules():
        assert r["labels"]["severity"] in ("critical", "warning"), r["alert"]
        assert r["labels"]["event_class"], r["alert"]
    skipped = {r["alert"] for r in rules()} - tested
    assert skipped <= {"GpuSingleBitEccRate", "GpuPcieReplays", "GpuNvlinkCrcRising", "GpuPowerThrottle",
                       "GpuRowRemapFailed"}, skipped


def test_tier1_codes_are_not_real_time_alerts():
    for r in rules():
        for code in ("== 63", "== 92", "== 13", "== 31", "== 45"):
            assert code not in r["expr"], (r["alert"], code)


@pytest.mark.skipif(not pathlib.Path(PROMTOOL).exists(), reason="promtool not installed")
def test_promtool_checks_and_tests_pass():
    for args in (["check", "rules", "c06_node_health_alerts.yml"], ["test", "rules", "c06_node_health_alerts_test.yml"]):
        done = subprocess.run([PROMTOOL, *args], cwd=HERE, capture_output=True, text=True)
        assert done.returncode == 0, done.stdout + done.stderr


@pytest.mark.skipif(not pathlib.Path(AMTOOL).exists(), reason="amtool not installed")
@pytest.mark.parametrize("labels,receiver", [
    (["severity=critical", "event_class=fleet"], "pagerduty-node-health"),
    (["severity=critical", "event_class=unrecoverable"], "pagerduty-node-health"),
    (["severity=warning", "event_class=thermal_power"], "slack-node-health"),
    (["severity=info"], "node-health-default"),
])
def test_alertmanager_config_is_valid_and_routes_by_severity(labels, receiver):
    base = [AMTOOL, "--alertmanager.url=http://127.0.0.1:1"]
    ok = subprocess.run([AMTOOL, "check-config", "c06_alertmanager.yml"], cwd=HERE, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    done = subprocess.run([*base[:1], "config", "routes", "test", "--config.file=c06_alertmanager.yml", *labels],
                          cwd=HERE, capture_output=True, text=True)
    assert done.stdout.strip() == receiver, done.stdout + done.stderr


def test_no_secret_values_in_alertmanager_file():
    text = (HERE / "c06_alertmanager.yml").read_text()
    assert "routing_key_file" in text and "api_url_file" in text
    assert not re.search(r"(routing_key|api_url):", text)


def test_crd_defaults_match_the_model_defaults():
    import c06_node_policy as m
    crd = yaml.safe_load((ROOT / "code/gpuhealth/config/crd/platform.example.com_gpuhealthpolicies.yaml").read_text())
    spec = crd["spec"]["versions"][0]["schema"]["openAPIV3Schema"]["properties"]["spec"]["properties"]
    assert m.parse_duration(spec["unhealthyFor"]["default"]) == m.Policy().unhealthy_for
    assert m.parse_duration(spec["healthyFor"]["default"]) == m.Policy().healthy_for
    assert spec["action"]["enum"] == [e.value for e in m.Mode]
    assert spec["action"]["default"] == "Cordon"


def _chapter_blocks():
    text = CHAPTER.read_text()
    return re.findall(r"```(\w+)\n(.*?)```", text, flags=re.S), text


@pytest.mark.skipif(not CHAPTER.exists(), reason="chapter file missing")
def test_every_code_block_in_the_chapter_equals_a_c06_file():
    blocks, _ = _chapter_blocks()
    files = {p.name: p.read_text() for p in HERE.glob("c06_*") if p.is_file()}
    for lang, body in blocks:
        if lang in ("mermaid", "text"):
            continue
        assert lang in ("yaml", "bash", "python", "csv"), lang
        if any(body.strip() == t.strip() for t in files.values()):
            continue
        # Lab command blocks are short invocations of tools, not scripts or configs.
        assert lang == "bash", body.splitlines()[0]
        for line in body.strip().splitlines():
            assert line.split()[0] in LAB_COMMANDS, line


@pytest.mark.skipif(not CHAPTER.exists(), reason="chapter file missing")
def test_dcgm_names_in_the_chapter_exist_or_are_flagged_legacy():
    _, text = _chapter_blocks()
    snap = snapshot()
    for name in set(re.findall(r"DCGM_[A-Z]+_[A-Z0-9_]+", text)):
        assert name in snap or name in LEGACY_NAMES_ALLOWED_IN_PROSE, name


@pytest.mark.skipif(not CHAPTER.exists(), reason="chapter file missing")
def test_chapter_xid_table_rows_match_the_catalog_snapshot():
    text = CHAPTER.read_text()
    rows = {}
    for line in (HERE / "c06_xid_catalog_snapshot.csv").read_text().splitlines():
        if line.startswith("#") or line.startswith("xid,"):
            continue
        r = next(csv.reader([line]))
        rows[r[0]] = r[2]
    for xid, action in rows.items():
        m = re.search(rf"^\| {xid} \|.*\|$", text, flags=re.M)
        if m and action not in ("N/A",):
            assert action.split(" ")[0] in m.group(0), (xid, action)
