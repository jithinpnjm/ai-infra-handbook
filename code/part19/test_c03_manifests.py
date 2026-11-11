"""Cross-file consistency checks for the chapter 19.3 manifests. Schema checks run separately
(kubeconform and tools/check_crd_yaml.py); these tests catch disagreements between files."""
import pathlib
import re

import pytest
import yaml

import c03_kv_sizing as k

HERE = pathlib.Path(__file__).parent


def load(name):
    return list(yaml.safe_load_all((HERE / name).read_text()))


ISVC = load("c03_isvc_llama31_8b.yaml")[0]
RT = load("c03_servingruntime_vllm.yaml")[0]
POOL = (HERE / "c03_node_pool.sh").read_text()
TRITON = load("c03_triton_deployment.yaml")[0]
NIM = load("c03_nim_cache_service.yaml")
SECRETS_SH = (HERE / "c03_namespace_secret.sh").read_text()


def isvc_args():
    return ISVC["spec"]["predictor"]["model"]["args"]


def flag(args, name):
    for a in args:
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    raise KeyError(name)


def test_runtime_name_and_format_match_inference_service():
    m = ISVC["spec"]["predictor"]["model"]
    assert m["runtime"] == RT["metadata"]["name"]
    assert m["modelFormat"]["name"] in [f["name"] for f in RT["spec"]["supportedModelFormats"]]
    assert ISVC["metadata"]["namespace"] == RT["metadata"]["namespace"]


def test_container_is_named_kserve_container():
    assert RT["spec"]["containers"][0]["name"] == "kserve-container"


def test_image_is_pinned_not_latest():
    img = RT["spec"]["containers"][0]["image"]
    assert ":" in img and not img.endswith(":latest")
    assert re.search(r":v\d+\.\d+\.\d+$", img)


def test_startup_window_covers_a_slow_first_download():
    p = RT["spec"]["containers"][0]["startupProbe"]
    window = p["periodSeconds"] * p["failureThreshold"]
    assert window >= 600        # chapter: at least ten minutes for a 16 GB download plus load


def test_liveness_cannot_kill_a_pod_that_is_only_slow_at_start():
    c = RT["spec"]["containers"][0]
    assert "startupProbe" in c   # liveness waits for startup to pass


def test_one_gpu_requested_and_limited():
    r = ISVC["spec"]["predictor"]["model"]["resources"]
    assert r["limits"]["nvidia.com/gpu"] == r["requests"]["nvidia.com/gpu"] == "1"


def test_max_replicas_do_not_exceed_gpus_in_pool():
    nodes = int(re.search(r"--num-nodes=(\d+)\s+\\\n\s+--machine-type=a2", POOL).group(1))
    assert ISVC["spec"]["predictor"]["maxReplicas"] <= nodes


def test_rolling_update_does_not_need_a_spare_gpu():
    pr = ISVC["spec"]["predictor"]
    if pr["maxReplicas"] == 2:
        assert pr["deploymentStrategy"]["rollingUpdate"]["maxSurge"] == 0


def test_keda_mode_has_autoscaling_and_no_scale_metric():
    ann = ISVC["metadata"]["annotations"]
    pr = ISVC["spec"]["predictor"]
    assert ann["serving.kserve.io/deploymentMode"] == "Standard"
    assert ann["serving.kserve.io/autoscalerClass"] == "keda"
    assert "autoScaling" in pr and "scaleMetric" not in pr
    q = pr["autoScaling"]["metrics"][0]["external"]["metric"]["query"]
    assert "vllm:num_requests_running" in q and "vllm:num_requests_waiting" in q


def test_prometheus_query_selects_the_served_model_name():
    q = ISVC["spec"]["predictor"]["autoScaling"]["metrics"][0]["external"]["metric"]["query"]
    assert f'model_name="{ISVC["metadata"]["name"]}"' in q
    assert "--served-model-name={{.Name}}" in RT["spec"]["containers"][0]["args"]


def test_model_context_fits_the_model_and_the_kv_plan():
    args = isvc_args()
    assert args[0] == "meta-llama/Llama-3.1-8B-Instruct"       # 8192 context for Llama 3 would reject 16384
    mml = int(flag(args, "--max-model-len"))
    seqs = int(flag(args, "--max-num-seqs"))
    util = float(flag(args, "--gpu-memory-utilization"))
    p = k.plan(k.LLAMA31_8B, 40, util, 3.0, 1024, 256, mml, seqs)
    assert mml <= 131072
    assert p["typical_batch_fits"]
    assert not p["worst_case_fits"]       # honest: the worst case needs preemption, so it is a known limit
    assert util < 1.0


def test_removed_or_invented_flags_are_absent():
    all_args = " ".join(isvc_args() + RT["spec"]["containers"][0]["args"])
    assert "--swap-space" not in all_args        # removed in vLLM v0.32.0


def test_node_pool_uses_a2_machine_for_a100_and_matching_count():
    assert "--machine-type=a2-highgpu-1g" in POOL
    assert "type=nvidia-tesla-a100,count=1" in POOL
    assert "n1-standard" not in POOL.split("node-pools create")[1]
    assert "--cluster=" in POOL and "--cluster-name" not in POOL


def test_selector_label_matches_gke_accelerator_name():
    assert ISVC["spec"]["predictor"]["nodeSelector"]["cloud.google.com/gke-accelerator"] == "nvidia-tesla-a100"


def test_triton_ports_http_8000_grpc_8001_metrics_8002():
    ports = {p["name"]: p["containerPort"] for p in TRITON["spec"]["template"]["spec"]["containers"][0]["ports"]}
    assert ports == {"http": 8000, "grpc": 8001, "metrics": 8002}


def test_triton_probes_use_v2_health_on_the_http_port():
    c = TRITON["spec"]["template"]["spec"]["containers"][0]
    assert c["readinessProbe"]["httpGet"]["path"] == "/v2/health/ready"
    assert c["livenessProbe"]["httpGet"]["path"] == "/v2/health/live"
    assert c["readinessProbe"]["httpGet"]["port"] == "http"


def test_triton_uses_poll_mode_for_live_reload():
    args = TRITON["spec"]["template"]["spec"]["containers"][0]["args"]
    assert "--model-control-mode=poll" in args and "--model-control-mode=explicit" not in args


def test_nim_secrets_are_referenced_consistently():
    cache, svc = NIM
    assert cache["spec"]["source"]["ngc"]["authSecret"] == svc["spec"]["authSecret"]
    assert cache["spec"]["source"]["ngc"]["pullSecret"] in svc["spec"]["image"]["pullSecrets"]
    assert svc["spec"]["storage"]["nimCache"]["name"] == cache["metadata"]["name"]
    assert 'NGC_API_KEY' in SECRETS_SH and "ngc-api-secret" in SECRETS_SH and "ngc-secret" in SECRETS_SH


def test_nim_tag_matches_between_cache_and_service():
    cache, svc = NIM
    pulled = cache["spec"]["source"]["ngc"]["modelPuller"]
    assert pulled == f'{svc["spec"]["image"]["repository"]}:{svc["spec"]["image"]["tag"]}'


@pytest.mark.parametrize("name", sorted(p.name for p in HERE.glob("c03_*") if p.suffix in {".yaml", ".sh"}))
def test_no_secret_values_in_files(name):
    text = (HERE / name).read_text()
    assert not re.search(r"hf_[A-Za-z0-9]{20,}", text)
    assert not re.search(r"nvapi-[A-Za-z0-9_-]{10,}", text)
