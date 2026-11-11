import copy
import c12_design_autoscaling as a
import c12_size_inference_pool as p

HOT, BATCH, WARM = p.WORKLOADS


def test_inflight_target_is_70_percent_of_batch():
    assert a.inflight_target(HOT) == 45 and a.inflight_target(BATCH) == 22


def test_cold_start_arithmetic():
    assert a.cold_start(True) == 150 and a.cold_start(False) == 480


def test_generated_policies_pass_their_own_check():
    gpus = {"assistant": 8, "docsum": 8, "analyst": 16}
    for w in p.WORKLOADS:
        o = a.scaled_object(w, a.max_replicas(w, gpus[w.name]))
        assert a.check_policy(o, w, gpus[w.name]) == []


def test_bad_policies_are_rejected():
    o = a.scaled_object(HOT, 8)
    z = copy.deepcopy(o)
    z["spec"]["minReplicaCount"] = 0
    assert any("never scale to zero" in m for m in a.check_policy(z, HOT, 8))
    z = copy.deepcopy(o)
    z["spec"]["triggers"] = [{"type": "cpu", "metadata": {"value": "70"}}]
    assert any("CPU or GPU" in m for m in a.check_policy(z, HOT, 8))
    z = copy.deepcopy(o)
    z["spec"]["maxReplicaCount"] = 20
    assert any("more GPUs" in m for m in a.check_policy(z, HOT, 8))
    z = copy.deepcopy(o)
    z["spec"]["advanced"]["horizontalPodAutoscalerConfig"]["behavior"]["scaleDown"]["stabilizationWindowSeconds"] = 60
    assert any("flap" in m for m in a.check_policy(z, HOT, 8))
    z = copy.deepcopy(o)
    del z["spec"]["fallback"]
    assert any("fallback" in m for m in a.check_policy(z, HOT, 8))


def test_batch_model_may_scale_to_zero_on_queue_metric():
    o = a.scaled_object(BATCH, 8)
    assert o["spec"]["minReplicaCount"] == 0
    assert "gateway_queue_depth" in o["spec"]["triggers"][0]["metadata"]["query"]


def test_headroom_uses_20_20_formula():
    # 3 QPS per minute of growth over a 150 s cold start is 7.5 QPS: one replica of 9.19 QPS covers it
    assert a.headroom_replicas(HOT, 3) == 1
    # without a free node the cold start is 480 s, so 24 QPS of growth needs 3 replicas
    assert a.headroom_replicas(HOT, 3, has_node=False) == 3
