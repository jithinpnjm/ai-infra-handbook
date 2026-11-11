"""Checks for chapter 19.1: parameter placement, sibling parameters, chapter == files."""
import pathlib
import re
import subprocess

import pytest

HERE = pathlib.Path(__file__).resolve().parent
CHAPTER = HERE.parents[1] / "docs" / "part-19-capstone" / "01-capstone-a-slurm-gpu-cluster.md"


def params(name):
    out = {}
    text = (HERE / name).read_text().replace("\\\n", " ")
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            for tok in re.findall(r'(\w+)=("[^"]*"|\S+)', line):
                out[tok[0]] = tok[1]
    return out


def test_constrain_keys_live_in_cgroup_conf_only():
    cg, sl = params("c01_cgroup.conf"), params("c01_slurm.conf")
    for k in ("ConstrainCores", "ConstrainRAMSpace", "ConstrainDevices", "CgroupPlugin"):
        assert cg[k]
        assert k not in sl
    assert all(cg[k] == "yes" for k in cg if k.startswith("Constrain"))


def test_autodetect_in_gres_conf_not_slurm_conf():
    assert params("c01_gres.conf")["AutoDetect"] == "nvml"
    assert "AutoDetect" not in params("c01_slurm.conf")


def test_slurm_secret_not_in_slurm_conf():
    assert "StoragePass" not in params("c01_slurm.conf")
    assert "StoragePass" in params("c01_slurmdbd.conf")


def test_sibling_parameters_present():
    sl = params("c01_slurm.conf")
    assert sl["SelectTypeParameters"].startswith("CR_")
    assert "limits" in sl["AccountingStorageEnforce"] and "qos" in sl["AccountingStorageEnforce"]
    assert sl["PriorityType"] == "priority/multifactor" and int(sl["PriorityWeightFairshare"]) > 0
    assert "gres/gpu" in sl["AccountingStorageTRES"]
    assert sl["JobAcctGatherType"] and sl["JobAcctGatherFrequency"]
    assert sl["GresTypes"] == "gpu"
    assert "task/affinity" in sl["TaskPlugin"]


def test_billing_weights_on_partition_line_with_gres_name():
    text = (HERE / "c01_slurm.conf").read_text().replace("\\\n", " ")
    line = [l for l in text.splitlines() if l.startswith("PartitionName")][0]
    assert "TRESBillingWeights=" in line and "GRES/gpu=" in line


def test_node_topology_arithmetic():
    sl = (HERE / "c01_slurm.conf").read_text().replace("\\\n", " ")
    node = [l for l in sl.splitlines() if l.startswith("NodeName")][0]
    v = dict(re.findall(r"(\w+)=(\S+)", node))
    assert int(v["Sockets"]) * int(v["CoresPerSocket"]) * int(v["ThreadsPerCore"]) == int(v["CPUs"])


def test_job_script_fits_node():
    t = (HERE / "c01_pretrain_job.sh").read_text()
    g = lambda k: int(re.search(rf"--{k}=(\d+)", t).group(1))
    assert g("ntasks-per-node") * g("cpus-per-task") <= 128
    assert g("mem") * 1024 <= 756000
    assert g("gpus-per-node") == 8


def test_health_fragment_is_excerpt_of_complete_file():
    full = (HERE / "c01_slurm.conf").read_text()
    for line in (HERE / "c01_slurm_health_check.conf").read_text().splitlines():
        if line and not line.startswith("#"):
            assert line in full


def test_health_check_drains_with_reason():
    t = (HERE / "c01_health_check.sh").read_text()
    assert t.count("State=drain Reason=") == 3


@pytest.mark.parametrize("f", sorted(p.name for p in HERE.glob("c01_*.sh")))
def test_shell_syntax(f):
    assert subprocess.run(["bash", "-n", str(HERE / f)]).returncode == 0


def test_shell_syntax_failure_is_detected(tmp_path):
    bad = tmp_path / "bad.sh"
    bad.write_text("if then fi\n")
    assert subprocess.run(["bash", "-n", str(bad)]).returncode != 0


def test_wrong_placement_would_be_caught():
    sl = params("c01_slurm.conf")
    sl["ConstrainDevices"] = "yes"  # simulate the old mistake
    assert "ConstrainDevices" in sl and "ConstrainDevices" not in params("c01_slurm.conf")


def chapter_blocks():
    return [m.group(2).strip("\n") for m in re.finditer(r"```(\w+)\n(.*?)\n```", CHAPTER.read_text(), re.S) if m.group(1) != "mermaid"]


def test_every_c01_file_appears_verbatim_in_chapter():
    blocks = chapter_blocks()
    for p in sorted(HERE.glob("c01_*")):
        assert p.read_text().strip("\n") in blocks, p.name


def test_every_chapter_block_is_a_file():
    files = [p.read_text().strip("\n") for p in HERE.glob("c01_*")]
    for b in chapter_blocks():
        assert b in files
