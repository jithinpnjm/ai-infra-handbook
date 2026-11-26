import re

def calc_w(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text.strip()) * factor * fs

def check_card(card_name, box_w, lines, fs=24, is_mono=False, pad=20):
    avail = box_w - 2 * pad
    print(f"\n--- {card_name} (box_w={box_w}, avail={avail}, fs={fs}) ---")
    all_ok = True
    for l in lines:
        w = calc_w(l, fs, is_mono)
        ok = w <= avail
        if not ok: all_ok = False
        print(f"  [{'OK' if ok else 'OVERFLOW'}] w={w:5.1f} / {avail:5.1f} | '{l}'")
    return all_ok

# Left column (box_w = 480, or subcards box_w = 440)
# Subcards inside left column: x = 60, w = 440. pad = 20 -> avail = 400.

# 1. interval: how often
check_card("interval", 440, ["interval: how often"], fs=26)

# 2. timeout: how long to wait
check_card("timeout", 440, ["timeout: how long to wait"], fs=26)

# 3. fall: failures needed to mark down
check_card("fall", 440, ["fall: failures needed to mark down"], fs=25)
check_card("fall wrapped", 440, ["fall: failures needed", "to mark down"], fs=26)

# 4. rise: successes needed to mark up
check_card("rise", 440, ["rise: successes needed to mark up"], fs=25)
check_card("rise wrapped", 440, ["rise: successes needed", "to mark up"], fs=26)

# 5. Detection takes about interval x fall: inter 2s fall 3 = 6.0 s
check_card("worked line", 440, [
    "Detection takes about",
    "interval x fall:",
    "inter 2s fall 3 = 6.0 s"
], fs=24, is_mono=False)

# 6. too aggressive: a loaded backend flaps
check_card("warning 1", 440, [
    "too aggressive:",
    "a loaded backend flaps"
], fs=26)

# 7. too lax: dead nodes keep receiving traffic
check_card("warning 2", 440, [
    "too lax:",
    "dead nodes keep",
    "receiving traffic"
], fs=26)

# Middle column (box_w = 480, pad = 25 -> avail = 430)
# 8. Active checks (the balancer probes on a schedule)
check_card("Active checks title", 480, [
    "Active checks",
    "(the balancer probes on a schedule)"
], fs=24)
check_card("Active checks title wrapped", 480, [
    "Active checks",
    "(the balancer probes",
    "on a schedule)"
], fs=26)

# 9. open a TCP connection, GET /healthz expecting 200, gRPC health protocol grpc.health.v1, or a custom script
check_card("Active checks body", 480, [
    "open a TCP connection,",
    "GET /healthz expecting 200,",
    "gRPC health protocol",
    "grpc.health.v1,",
    "or a custom script"
], fs=24)

# 10. Passive checks (watch real traffic)
check_card("Passive checks title", 480, [
    "Passive checks",
    "(watch real traffic)"
], fs=26)

# 11. eject a backend after N consecutive 5xx responses or connection failures, for a period; Envoy outlier detection, HAProxy observe layer7, nginx max_fails; catches failures a probe misses, and brownouts, a backend answering slowly or half the time
check_card("Passive checks body", 480, [
    "eject a backend after",
    "N consecutive 5xx responses",
    "or connection failures,",
    "for a period;",
    "Envoy outlier detection,",
    "HAProxy observe layer7,",
    "nginx max_fails;",
    "catches failures a probe misses,",
    "and brownouts, a backend",
    "answering slowly",
    "or half the time"
], fs=24)

# Right column (box_w = 480, pad = 25 -> avail = 430)
# 12. Liveness: is the process up?
check_card("Liveness", 480, [
    "Liveness:",
    "is the process up?"
], fs=28)

# 13. Readiness: can it serve right now: the model is loaded, the GPU is healthy, the queue is not full
check_card("Readiness", 480, [
    "Readiness:",
    "can it serve right now:",
    "the model is loaded,",
    "the GPU is healthy,",
    "the queue is not full"
], fs=25)

# 14. Triton /v2/health/ready, vLLM /health, GPU health through DCGM Xid or ECC data; mark a replica not-ready during model load; slowstart for cold replicas
check_card("Inference endpoints body", 480, [
    "Triton /v2/health/ready,",
    "vLLM /health, GPU health through",
    "DCGM Xid or ECC data;",
    "mark a replica not-ready",
    "during model load;",
    "slowstart for cold replicas"
], fs=24)

# 15. A failing backend that keeps its address keeps receiving traffic unless a check removes it
check_card("Bottom bar", 1520, [
    "A failing backend that keeps its address keeps receiving traffic unless a check removes it"
], fs=25)
