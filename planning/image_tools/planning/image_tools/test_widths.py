#!/usr/bin/env python3
import sys

# Conservative width estimator:
# Sans-serif: 0.6 * font_size per character
# Monospace: 0.62 * font_size per character

def text_width(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * factor * fs

def check_wrap(lines, cell_width, padding=16, fs=24, is_mono=False):
    max_avail = cell_width - 2 * padding
    for line in lines:
        w = text_width(line, fs, is_mono)
        status = "OK" if w <= max_avail else "OVERFLOW"
        print(f"  [{status}] w={w:.1f} / {max_avail:.1f} (fs={fs}) | '{line}'")
        if w > max_avail:
            return False
    return True

print("=== CHECKING ROW 1 ===")
# Row 1:
# Type: Resource
# Source API: metrics.k8s.io (mono)
# Provider: metrics-server from kubelet and cAdvisor
# Example: CPU or memory average utilisation relative to requests, or average value

print("Col 1: Resource")
check_wrap(["Resource"], 290, fs=28)

print("Col 2: metrics.k8s.io")
check_wrap(["metrics.k8s.io"], 360, fs=25, is_mono=True)

print("Col 3: Provider")
lines_r1_p = [
    "metrics-server from",
    "kubelet and cAdvisor"
]
check_wrap(lines_r1_p, 425, fs=24)

print("Col 4: Example")
lines_r1_ex = [
    "CPU or memory average",
    "utilisation relative to",
    "requests, or average value"
]
check_wrap(lines_r1_ex, 400, fs=24)

print("\n=== CHECKING ROW 2 ===")
# Row 2:
# Type: ContainerResource
# Source API: metrics.k8s.io per container
# Example: scale on the app container only, ignoring sidecars

print("Col 1: ContainerResource")
check_wrap(["ContainerResource"], 290, fs=26)

print("Col 2: metrics.k8s.io per container")
lines_r2_api = [
    "metrics.k8s.io",
    "per container"
]
check_wrap(lines_r2_api, 360, fs=24)

print("Col 4: scale on the app container only, ignoring sidecars")
lines_r2_ex = [
    "scale on the app container",
    "only, ignoring sidecars"
]
check_wrap(lines_r2_ex, 400, fs=24)

print("\n=== CHECKING ROW 3 ===")
# Row 3:
# Type: Pods
# Source API: custom.metrics.k8s.io
# Provider: via Prometheus Adapter, KEDA or vendor adapters
# Example: per-pod requests_in_flight or queue_length_per_pod

print("Col 1: Pods")
check_wrap(["Pods"], 290, fs=28)

print("Col 2: custom.metrics.k8s.io")
check_wrap(["custom.metrics.k8s.io"], 360, fs=25, is_mono=True)

print("Col 3: Provider")
lines_r3_p = [
    "via Prometheus Adapter,",
    "KEDA or vendor adapters"
]
check_wrap(lines_r3_p, 425, fs=24)

print("Col 4: Example")
lines_r3_ex = [
    "per-pod requests_in_flight",
    "or queue_length_per_pod"
]
check_wrap(lines_r3_ex, 400, fs=24)

print("\n=== CHECKING ROW 4 ===")
# Row 4:
# Type: Object
# Source API: custom.metrics.k8s.io for one object
# Example: Ingress requests_per_second

print("Col 1: Object")
check_wrap(["Object"], 290, fs=28)

print("Col 2: Source API")
lines_r4_api = [
    "custom.metrics.k8s.io",
    "for one object"
]
check_wrap(lines_r4_api, 360, fs=24)

print("Col 4: Example")
lines_r4_ex = [
    "Ingress requests_per_second"
]
check_wrap(lines_r4_ex, 400, fs=24)

print("\n=== CHECKING ROW 5 ===")
# Row 5:
# Type: External
# Source API: external.metrics.k8s.io
# Provider: via KEDA, Prometheus Adapter or cloud adapters
# Example: SQS queue length, Pub/Sub backlog, global QPS

print("Col 1: External")
check_wrap(["External"], 290, fs=28)

print("Col 2: Source API")
check_wrap(["external.metrics.k8s.io"], 360, fs=25, is_mono=True)

print("Col 3: Provider")
lines_r5_p = [
    "via KEDA, Prometheus",
    "Adapter or cloud adapters"
]
check_wrap(lines_r5_p, 425, fs=24)

print("Col 4: Example")
lines_r5_ex = [
    "SQS queue length, Pub/Sub",
    "backlog, global QPS"
]
check_wrap(lines_r5_ex, 400, fs=24)
