"""Control-plane model for a dedicated endpoint (chapter 20.14).

The control plane owns desired state and lifecycle. Each region's data plane
serves traffic. The rules here are a design sketch: Nebius has not published its
internal state machine. Field names follow the public description: GPU type,
GPUs per replica, min and max replicas, region.
"""
from dataclasses import dataclass

GPU_TYPES = ("L40", "H100", "H200", "B200")
REGIONS = ("eu", "us")
TRANSITIONS = {
    "create": {None: "disabled"},
    "enable": {"disabled": "enabled"},
    "disable": {"enabled": "disabled"},
    "update": {"enabled": "enabled", "disabled": "disabled"},
    "delete": {"disabled": "deleted"},
}


@dataclass(frozen=True)
class EndpointSpec:
    model: str
    gpu_type: str
    gpus_per_replica: int
    min_replicas: int
    max_replicas: int
    region: str


def validate(spec: EndpointSpec) -> list:
    errs = []
    if spec.gpu_type not in GPU_TYPES:
        errs.append(f"gpu_type must be one of {GPU_TYPES}")
    if spec.region not in REGIONS:
        errs.append(f"region must be one of {REGIONS}")
    if spec.gpus_per_replica < 1:
        errs.append("gpus_per_replica must be at least 1")
    if spec.min_replicas < 0:
        errs.append("min_replicas cannot be negative")
    if spec.max_replicas < max(1, spec.min_replicas):
        errs.append("max_replicas must be at least min_replicas and at least 1")
    return errs


def next_state(state, action):
    """Return the new lifecycle state, or raise when the action is not allowed."""
    try:
        return TRANSITIONS[action][state]
    except KeyError:
        raise ValueError(f"cannot {action} an endpoint that is {state}") from None


def max_gpus(spec: EndpointSpec) -> int:
    """GPUs the data plane must be able to reserve at the ceiling, plus one surge replica."""
    return (spec.max_replicas + 1) * spec.gpus_per_replica
