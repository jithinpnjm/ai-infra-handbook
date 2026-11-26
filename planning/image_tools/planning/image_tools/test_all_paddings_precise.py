#!/usr/bin/env python3

def line_w(segments):
    w = 0.0
    for text, fs, is_mono in segments:
        rate = 0.62 if is_mono else 0.60
        w += len(text) * rate * fs
    return w

boxes_to_check = [
    ("Box 1 Phase", 40, 480, [
        [("Pull image ", 30, False)],
        [("(vLLM v0.32.0 amd64 ", 24, False)],
        [("image is about 9.2 GB on ", 24, False)],
        [("Docker Hub, not under 5 GB ", 24, False)],
        [("as the book says): ", 24, False)]
    ]),
    ("Box 1 Remedy", 56, 448, [
        [("pin the tag or digest and ", 24, False)],
        [("use ", 24, False), ("IfNotPresent", 24, True), (" so a node ", 24, False)],
        [("that has the image does not ", 24, False)],
        [("pull again; pre-pull", 24, False)]
    ]),
    ("Box 2 Phase", 560, 480, [
        [("Fetch and mount model: ", 30, False)]
    ]),
    ("Box 2 Remedy", 576, 448, [
        [("weights on a PVC, an OCI ", 24, False)],
        [("image or node-local NVMe ", 24, False)],
        [("instead of downloading from ", 24, False)],
        [("Hugging Face on every start", 24, False)]
    ]),
    ("Box 3 Phase", 1080, 480, [
        [("Start runtime: ", 30, False)]
    ]),
    ("Box 3 Remedy", 1096, 448, [
        [("a second or less ", 24, False)],
        [("per the book", 24, False)]
    ]),
    ("Box 4 Phase", 40, 480, [
        [("Load weights to GPU: ", 30, False)]
    ]),
    ("Box 4 Remedy", 56, 448, [
        [("bounded by I/O into GPU ", 24, False)],
        [("memory; faster loader such ", 24, False)],
        [("as Run:ai Model Streamer ", 24, False)],
        [("with ", 24, False), ("--load-format", 24, True), (" ", 24, False)],
        [("runai_streamer, ", 24, True)],
        [("no repackaging", 24, False)]
    ]),
    ("Box 5 Phase", 560, 480, [
        [("Warm-up: ", 30, False)],
        [("allocate KV pool, profile, ", 24, False)],
        [("compile and capture ", 24, False)],
        [("CUDA graphs: ", 24, False)]
    ]),
    ("Box 5 Remedy", 576, 448, [
        [("reuse the ", 24, False)],
        [("torch.compile", 24, True), (" cache ", 24, False)],
        [("under ", 24, False), ("VLLM_CACHE_ROOT,", 24, True), (" ", 24, False)],
        [("set ", 24, False), ("VLLM_FORCE_AOT_LOAD=1", 24, True), (" ", 24, False)],
        [("to fail loudly on a ", 24, False)],
        [("cache miss, pass ", 24, False)],
        [("--kv-cache-memory ", 24, True)],
        [("to skip profiling", 24, False)]
    ]),
    ("Box 6 Phase", 1080, 480, [
        [("API opens: ", 30, False)]
    ]),
    ("Box 6 Remedy", 1096, 448, [
        [("/health 200", 24, True)]
    ]),
    ("Footer", 40, 1520, [
        [("book says these together can cut scale-up from many minutes ", 24, False)],
        [("to tens of seconds depending on model size; ", 24, False), ("--enforce-eager", 24, True), (" and ", 24, False)],
        [("-O0", 24, True), (" make boot fast but decode slower, use them in development only; ", 24, False)],
        [("most time goes to model download and weight load; measure each phase on your own cluster", 24, False)]
    ])
]

print("Verifying padding >= 16px for every line:")
all_pass = True
for name, bx, bw, lines in boxes_to_check:
    for idx, line in enumerate(lines, 1):
        w = line_w(line)
        pad = (bw - w) / 2.0
        text_str = "".join(t for t, fs, m in line)
        ok = (pad >= 16.0)
        if not ok:
            all_pass = False
        print(f"[{name:12s}] line {idx:2d}: pad={pad:5.1f}px (w={w:5.1f}px, box_w={bw}px) | ok={ok} | '{text_str}'")

assert all_pass, "Some lines have padding < 16px!"
print("\n>>> ALL PADDING CHECKS PASSED PERFECTLY (MINIMUM PAD >= 16PX)! <<<")
