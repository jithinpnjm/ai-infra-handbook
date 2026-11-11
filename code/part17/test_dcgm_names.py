import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

import dcgm_names as d

HERE = Path(__file__).parent
CSV_NEW = Path("/private/tmp/claude-501/v20/dcgm/new/etc/default-counters.csv")
CSV_OLD = Path("/private/tmp/claude-501/v20/dcgm/old/etc/default-counters.csv")


def test_counts():
    assert len(d.DATA["renamed"]) == 23
    assert len(d.unit_changes()) == 11
    olds = [e["old"] for e in d.DATA["renamed"] + d.DATA["inferred_optional"]]
    news = [e["new"] for e in d.DATA["renamed"] + d.DATA["inferred_optional"]]
    assert len(set(olds)) == len(olds) and len(set(news)) == len(news)
    assert not set(olds) & set(news)


def test_simple_rename_and_labels():
    assert d.convert("DCGM_FI_DEV_GPU_TEMP > 85") == "DCGM_FI_DEV_GPU_TEMP_CELSIUS > 85"
    assert d.convert('max by (DCGM_FI_DRIVER_VERSION) (DCGM_FI_DEV_XID_ERRORS)') == \
        "max by (DCGM_FI_SYSTEM_DRIVER_VERSION) (DCGM_FI_DEV_XID_ERROR)"


@pytest.mark.parametrize("old,new", [
    ("DCGM_FI_DEV_GPU_UTIL > 95", "(DCGM_FI_DEV_GPU_UTIL_RATIO * 100) > 95"),
    ("DCGM_FI_DEV_SM_CLOCK < 1400", "(DCGM_FI_DEV_SM_CLOCK_HERTZ / 1000000) < 1400"),
    ("DCGM_FI_DEV_FB_USED / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE)",
     "(DCGM_FI_DEV_FB_USED_BYTES / 1048576) / ((DCGM_FI_DEV_FB_USED_BYTES / 1048576) + (DCGM_FI_DEV_FB_FREE_BYTES / 1048576))"),
    ("rate(DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION[5m])", "(rate(DCGM_FI_DEV_GPU_ENERGY_JOULES_TOTAL[5m]) * 1000)"),
    ('avg by (gpu) (DCGM_FI_DEV_GPU_UTIL{pod="x"})', 'avg by (gpu) ((DCGM_FI_DEV_GPU_UTIL_RATIO{pod="x"} * 100))'),
])
def test_old_to_new_scaling(old, new):
    assert d.convert(old) == new


def test_round_trip_is_semantics_preserving_names():
    for e in d.DATA["renamed"]:
        if e.get("scale_status"):
            continue
        n = e["new"]
        back = d.convert(d.convert(n, "new_to_old"), "old_to_new")
        # old->new of a scaled expression: ((NEW op f) inverse f) -- both sides reference NEW
        assert n in back


def test_new_to_old_scaling():
    assert d.convert("DCGM_FI_DEV_GPU_UTIL_RATIO > 0.95", "new_to_old") == "(DCGM_FI_DEV_GPU_UTIL / 100) > 0.95"
    assert d.convert("DCGM_FI_DEV_FB_USED_BYTES", "new_to_old") == "(DCGM_FI_DEV_FB_USED * 1048576)"
    assert d.convert("DCGM_FI_DEV_SM_CLOCK_HERTZ", "new_to_old") == "(DCGM_FI_DEV_SM_CLOCK * 1000000)"
    assert d.convert("increase(DCGM_FI_DEV_GPU_ENERGY_JOULES_TOTAL[1h])", "new_to_old") == \
        "(increase(DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION[1h]) / 1000)"


def test_names_only_and_unverified_scale():
    assert d.convert("DCGM_FI_DEV_GPU_UTIL > 95", scale="names_only") == "DCGM_FI_DEV_GPU_UTIL_RATIO > 95"
    with pytest.raises(d.UnitScaleError):
        d.convert("DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL")
    assert d.convert("DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL", scale="names_only") == "DCGM_FI_DEV_NVLINK_THROUGHPUT_BYTES_PER_SECOND"


def test_range_selector_outside_function_is_refused():
    with pytest.raises(d.UnitScaleError):
        d.convert("DCGM_FI_DEV_GPU_UTIL[5m]")


def test_unknown_and_unchanged_names_untouched():
    s = "DCGM_FI_DEV_ECC_DBE_VOL_TOTAL > 0 and up == 1"
    assert d.convert(s) == s
    assert d.convert("DCGM_FI_DEV_GPU_UTIL_RATIO") == "DCGM_FI_DEV_GPU_UTIL_RATIO"


def test_to_dual():
    assert d.to_dual("DCGM_FI_DEV_GPU_TEMP_CELSIUS > 85") == "(DCGM_FI_DEV_GPU_TEMP_CELSIUS > 85) or (DCGM_FI_DEV_GPU_TEMP > 85)"
    assert d.to_dual("up == 1") == "up == 1"


def test_json_is_valid_and_sourced():
    for e in d.DATA["renamed"] + d.DATA["inferred_optional"]:
        assert e["source"] and e["status"] in ("verified", "inferred")
        assert e["scale"] is None or (e["scale"]["op"] in ("multiply", "divide") and e["scale"]["factor"] > 0)


def _csv_names(p):
    names = set()
    for line in p.read_text().splitlines():
        mo = re.match(r"^#?\s*(DCGM_(?:FI|EXP)_[A-Z0-9_]+)\s*,", line.strip())
        if mo:
            names.add(mo.group(1))
    return names


@pytest.mark.skipif(not CSV_NEW.exists(), reason="dcgm-exporter worktrees not present")
def test_against_the_two_csvs():
    new, old = _csv_names(CSV_NEW), _csv_names(CSV_OLD)
    for e in d.DATA["renamed"]:
        assert e["new"] in new, e
        assert e["old"] in old, e
    for e in d.DATA["inferred_optional"]:
        assert e["new"] in new or e["new"].endswith("_L0_BYTES_PER_SECOND") or e["old"] == "DCGM_FI_DEV_FB_TOTAL", e
    # the default (uncommented) rows of the old file that vanished are exactly the 'old' names we list
    def active(p):
        return {m.group(1) for l in p.read_text().splitlines() if (m := re.match(r"^(DCGM_FI_[A-Z0-9_]+)\s*,", l))}
    gone = active(CSV_OLD) - active(CSV_NEW)
    assert gone == {e["old"] for e in d.DATA["renamed"]}


def test_converted_rules_pass_promtool_and_scale_matches():
    pt = shutil.which("promtool") or str(Path.home() / "go/bin/promtool")
    if not Path(pt).exists():
        pytest.skip("promtool not installed")
    exprs = ["avg(DCGM_FI_DEV_GPU_UTIL) > 95", "DCGM_FI_DEV_SM_CLOCK < 1400",
             "rate(DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION[5m])", "DCGM_FI_DEV_FB_USED / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE) > 0.9"]
    rules = {"groups": [{"name": "g", "rules": [{"record": f"r{i}", "expr": d.convert(x)} for i, x in enumerate(exprs)]}]}
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / "r.yaml"
        f.write_text(yaml.safe_dump(rules))
        r = subprocess.run([pt, "check", "rules", str(f)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


def test_gpu_alerts_promtool_unit_tests():
    pt = shutil.which("promtool") or str(Path.home() / "go/bin/promtool")
    if not Path(pt).exists():
        pytest.skip("promtool not installed")
    r = subprocess.run([pt, "test", "rules", "gpu_alerts_test.yml"], capture_output=True, text=True, cwd=HERE)
    assert r.returncode == 0, r.stdout + r.stderr
