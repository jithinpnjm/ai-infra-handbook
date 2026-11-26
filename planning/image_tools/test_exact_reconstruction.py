import re

labels_data = {
    "interval": ["interval: how often"],
    "timeout": ["timeout: how long to wait"],
    "fall": ["fall: failures needed", "to mark down"],
    "rise": ["rise: successes needed", "to mark up"],
    "worked": [
        "Detection takes about",
        "interval x fall:",
        "inter 2s fall 3 = 6.0 s"
    ],
    "warn1": [
        "too aggressive:",
        "a loaded backend flaps"
    ],
    "warn2": [
        "too lax:",
        "dead nodes keep",
        "receiving traffic"
    ],
    "active_title": [
        "Active checks",
        "(the balancer probes",
        "on a schedule)"
    ],
    "active_body": [
        "open a TCP connection,",
        "GET /healthz expecting 200,",
        "gRPC health protocol",
        "grpc.health.v1,",
        "or a custom script"
    ],
    "passive_title": [
        "Passive checks",
        "(watch real traffic)"
    ],
    "passive_body": [
        "eject a backend after",
        "N consecutive 5xx responses",
        "or connection failures,",
        "for a period; Envoy outlier",
        "detection, HAProxy observe",
        "layer7, nginx max_fails;",
        "catches failures a probe",
        "misses, and brownouts,",
        "a backend answering slowly",
        "or half the time"
    ],
    "liveness": [
        "Liveness:",
        "is the process up?"
    ],
    "readiness": [
        "Readiness:",
        "can it serve right now:",
        "the model is loaded,",
        "the GPU is healthy,",
        "the queue is not full"
    ],
    "endpoints": [
        "Triton /v2/health/ready,",
        "vLLM /health, GPU health",
        "through DCGM Xid or ECC",
        "data; mark a replica",
        "not-ready during model",
        "load; slowstart for cold",
        "replicas"
    ],
    "bottom": [
        "A failing backend that keeps its address keeps receiving traffic unless a check removes it"
    ]
}

expected_labels = [
    "interval: how often",
    "timeout: how long to wait",
    "fall: failures needed to mark down",
    "rise: successes needed to mark up",
    "Detection takes about interval x fall: inter 2s fall 3 = 6.0 s",
    "too aggressive: a loaded backend flaps",
    "too lax: dead nodes keep receiving traffic",
    "Active checks (the balancer probes on a schedule)",
    "open a TCP connection, GET /healthz expecting 200, gRPC health protocol grpc.health.v1, or a custom script",
    "Passive checks (watch real traffic)",
    "eject a backend after N consecutive 5xx responses or connection failures, for a period; Envoy outlier detection, HAProxy observe layer7, nginx max_fails; catches failures a probe misses, and brownouts, a backend answering slowly or half the time",
    "Liveness: is the process up?",
    "Readiness: can it serve right now: the model is loaded, the GPU is healthy, the queue is not full",
    "Triton /v2/health/ready, vLLM /health, GPU health through DCGM Xid or ECC data; mark a replica not-ready during model load; slowstart for cold replicas",
    "A failing backend that keeps its address keeps receiving traffic unless a check removes it"
]

for k, exp in zip(labels_data.keys(), expected_labels):
    lines = labels_data[k]
    # join with space as suffix in tspan
    joined = " ".join([l.strip() for l in lines])
    assert joined == exp, f"Mismatch on {k}:\n  Got:      '{joined}'\n  Expected: '{exp}'"
    print(f"[OK] {k}")
