import os
import shutil
import subprocess
import pytest
import yaml
import c12_design_autoscaling as a

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    return yaml.safe_load(open(os.path.join(HERE, name)))


def test_yaml_files_equal_generator_output():
    pol = a.all_policies()
    assert load("c12_inference_scaling.yaml") == pol["assistant"]
    assert load("c12_inference_scaling_batch.yaml") == pol["docsum"]


def test_priority_classes():
    docs = list(yaml.safe_load_all(open(os.path.join(HERE, "c12_priority_classes.yaml"))))
    by = {d["metadata"]["name"]: d for d in docs}
    assert by["llm-interactive"]["value"] > by["llm-batch"]["value"]
    assert by["llm-batch"]["preemptionPolicy"] == "Never"


@pytest.mark.skipif(not shutil.which("kubeconform"), reason="kubeconform not installed")
def test_priority_classes_pass_kubeconform():
    r = subprocess.run(["kubeconform", "-strict", "-ignore-missing-schemas",
                        os.path.join(HERE, "c12_priority_classes.yaml")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_scaledobject_schema_when_crd_available():
    crd = os.environ.get("KEDA_CRD")
    if not crd or not os.path.exists(crd):
        pytest.skip("set KEDA_CRD to keda.sh_scaledobjects.yaml from a clone of kedacore/keda")
    root = os.path.join(HERE, "..", "..")
    r = subprocess.run(["python3", "-I", os.path.join(root, "tools", "check_crd_yaml.py"), crd, "--",
                        os.path.join(HERE, "c12_inference_scaling.yaml"),
                        os.path.join(HERE, "c12_inference_scaling_batch.yaml")], capture_output=True, text=True)
    assert r.returncode == 0 and "0 problems" in r.stdout
