"""Tests for the kubectl-output triage helper (chapter 20.23)."""
import pathlib
import subprocess
import sys

from c23_triage import diagnose, parse_describe, parse_events, render

HERE = pathlib.Path(__file__).parent
SAMPLES = HERE / "samples"


def sample(name):
    return (SAMPLES / name).read_text()


def causes(findings):
    return [f.cause for f in findings]


def test_oom_kill_is_found_from_last_state():
    d = parse_describe(sample("c23_describe_oomkilled.txt"))
    c = d.containers[0]
    assert c.name == "simmemleak"
    assert c.last_reason == "OOMKilled" and c.exit_code == "137" and c.restarts == 5
    found = diagnose(sample("c23_describe_oomkilled.txt"))
    assert causes(found)[0] == "container_oom_kill"
    assert "limit" in found[0].next_step


def test_liveness_kill_found_from_events_and_not_oom():
    found = diagnose(sample("c23_describe_liveness_kill.txt"))
    assert "liveness_probe_kill" in causes(found)
    assert "container_oom_kill" not in causes(found)
    assert found[0].confidence == "high"


def test_events_table_columns_with_multiword_age():
    events = parse_events(sample("c23_describe_liveness_kill.txt"))
    unhealthy = [e for e in events if e.reason == "Unhealthy"][0]
    assert unhealthy.age == "10s (x3 over 20s)"
    assert unhealthy.message.startswith("Liveness probe failed")


def test_pending_gpu_with_no_gpu_capacity():
    found = diagnose(sample("c23_describe_pending_gpu.txt"))
    assert causes(found) == ["gpu_unavailable"]
    assert "Allocatable" in found[0].next_step


def test_pending_taint_and_gpu_both_reported():
    found = diagnose(sample("c23_describe_pending_taint.txt"))
    assert set(causes(found)) == {"untolerated_taint", "gpu_unavailable"}


def test_image_pull_from_state_and_events_deduplicated_by_evidence():
    found = diagnose(sample("c23_describe_image_pull.txt"))
    assert "image_pull_failure" in causes(found)


def test_node_not_ready_with_unknown_condition():
    found = diagnose(sample("c23_describe_node_notready.txt"))
    assert found[0].cause == "node_not_ready"
    assert "kubelet stopped posting status" in found[0].evidence
    assert "node.kubernetes.io/unreachable:NoExecute" in found[0].evidence


def test_get_events_table_finds_eviction_webhook_and_scheduling():
    found = diagnose("", sample("c23_get_events_mixed.txt"))
    got = set(causes(found))
    assert {"cpu_memory_capacity", "node_pressure_eviction",
            "admission_webhook_unreachable", "node_not_ready"} <= got
    wh = [f for f in found if f.cause == "admission_webhook_unreachable"][0]
    assert "policy.example.com" in wh.evidence
    ev = [f for f in found if f.cause == "node_pressure_eviction"][0]
    assert "memory" in ev.next_step


def test_oom_and_liveness_together_demote_liveness():
    text = sample("c23_describe_oomkilled.txt")
    text += "\nEvents:\n  Type     Reason     Age   From     Message\n  ----     ------     ----  ----     -------\n"
    text += "  Warning  Unhealthy  10s   kubelet  Liveness probe failed: HTTP probe failed with statuscode: 500\n"
    found = diagnose(text)
    assert found[0].cause == "container_oom_kill"
    live = [f for f in found if f.cause == "liveness_probe_kill"][0]
    assert live.confidence == "medium"


def test_node_pressure_conditions():
    text = ("Name:  n1\nTaints:  node.kubernetes.io/memory-pressure:NoSchedule\nUnschedulable:  false\n"
            "Conditions:\n  Type             Status\n  MemoryPressure   True\n  DiskPressure     False\n  Ready            True\n")
    assert causes(diagnose(text)) == ["node_memory_pressure"]


def test_webhook_denied_message():
    msg = 'Error from server: admission webhook "x.example.com" denied the request: no'
    text = f"LAST SEEN   TYPE   REASON       OBJECT   MESSAGE\n1m   Warning   FailedCreate   rs/a   {msg}\n"
    assert causes(diagnose("", text)) == ["admission_webhook_denied"]


def test_no_match_message():
    assert "No known pattern" in render(diagnose("Name: x\nStatus: Running\n"))


def test_cli_runs_on_sample():
    out = subprocess.run(
        [sys.executable, str(HERE / "c23_triage.py"), str(SAMPLES / "c23_describe_pending_gpu.txt")],
        capture_output=True, text=True, check=True).stdout
    assert out.startswith("1. gpu_unavailable [high]")
