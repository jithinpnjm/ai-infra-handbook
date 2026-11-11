"""Tests for the chapter 19.13 reproducibility checklist runner."""
import copy
import json
import subprocess
import sys

import pytest

import c13_repro_checklist as r

HERE = r.pathlib.Path(__file__).resolve().parent


@pytest.fixture
def good():
    return json.loads((HERE / "c13_run_manifest_good.json").read_text())


def failed(m):
    return {x.rule for x in r.check(m) if not x.ok and x.required}


def test_good_manifest_passes(good):
    assert r.passed(r.check(good))


def test_bad_manifest_fails_on_the_four_planted_problems():
    bad = json.loads((HERE / "c13_run_manifest_bad.json").read_text())
    assert failed(bad) == {"working tree clean", "image pinned by digest",
                           "every dataset pinned (name, version, content hash)", "seed recorded"}


@pytest.mark.parametrize("path,value,rule", [
    (("code", "git_commit"), "abc123", "code commit recorded"),
    (("environment", "image"), "reg/img:1.0", "image pinned by digest"),
    (("environment", "lockfile_sha256"), "", "lockfile hash recorded"),
    (("randomness", "seed"), True, "seed recorded"),
    (("run", "mlflow_run_id"), "", "tracking run id recorded"),
    (("hardware", "driver"), "", "hardware recorded (gpu model, driver)"),
])
def test_each_rule_catches_its_own_defect(good, path, value, rule):
    m = copy.deepcopy(good)
    m[path[0]][path[1]] = value
    assert rule in failed(m)


def test_empty_manifest_fails_everything_required():
    assert len(failed({})) == 9


def test_warnings_do_not_fail_a_run(good):
    m = copy.deepcopy(good)
    m["randomness"]["deterministic_algorithms"] = None
    res = r.check(m)
    assert r.passed(res) and any(not x.ok and not x.required for x in res)


def test_mlflow_tags_use_the_real_system_tag_key(good):
    t = r.to_mlflow_tags(good)
    assert t["mlflow.source.git.commit"] == good["code"]["git_commit"]
    assert t["research.dataset.web-text-v3"].startswith("dvc:rev-9d41:")


def test_cli_exit_codes():
    ok = subprocess.run([sys.executable, str(HERE / "c13_repro_checklist.py"), str(HERE / "c13_run_manifest_good.json")], capture_output=True)
    bad = subprocess.run([sys.executable, str(HERE / "c13_repro_checklist.py"), str(HERE / "c13_run_manifest_bad.json")], capture_output=True)
    assert ok.returncode == 0 and bad.returncode == 1


def test_capture_sees_dirty_tree(tmp_path):
    def g(*a):
        subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)
    g("init", "-q")
    g("config", "user.email", "t@example.com")
    g("config", "user.name", "t")
    (tmp_path / "uv.lock").write_text("x")
    g("add", ".")
    g("commit", "-qm", "c")
    clean = r.capture(str(tmp_path), "uv.lock")
    assert clean["code"]["git_dirty"] is False and len(clean["code"]["git_commit"]) == 40
    assert clean["environment"]["lockfile_sha256"] == r.file_sha256(tmp_path / "uv.lock")
    (tmp_path / "new.py").write_text("y")
    assert r.capture(str(tmp_path))["code"]["git_dirty"] is True
