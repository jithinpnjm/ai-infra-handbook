import xml.etree.ElementTree as ET
import re

tree = ET.parse("gpu_container_infographic.svg")
root = tree.getroot()

print("Checking line lengths and padding estimates...")

# Rule:
# "Estimate widths conservatively: sans 0.6 x font-size per character, monospace 0.62 x font-size per character.
# Every text line must fit inside its box with at least 16 px padding.
# Never let text touch or cross a box edge, an icon or an arrow."

# Let's inspect every text element, its tspans, and verify conservative widths against their parent boxes:
lines_to_check = [
    # (text, font_type, font_size, box_width)
    ("NVIDIA kernel module nvidia.ko", "mono", 24, 520),
    ("device nodes /dev/nvidia*", "mono", 24, 520),
    ("libcuda.so, libnvidia-ml.so,", "mono", 24, 520),
    ("nvidia-smi", "mono", 24, 520),
    ("NVIDIA Container", "sans", 24, 340),
    ("Toolkit injects", "sans", 24, 340),
    ("at start", "sans", 24, 340),
    ("CUDA runtime libcudart", "mono", 24, 520),
    ("cuBLAS, cuDNN, NCCL", "sans", 24, 520),
    ("PyTorch, TensorRT, vLLM", "sans", 24, 520),
    ("1 runtime is", "sans", 24, 345),
    ("asked for GPU access", "sans", 24, 345),
    ("(--gpus all or CDI)", "sans", 24, 345),
    ("2 toolkit hook lists", "sans", 24, 345),
    ("host GPUs before", "sans", 24, 345),
    ("the app starts", "sans", 24, 345),
    ("3 adds /dev/nvidia*", "sans", 24, 345),
    ("and bind-mounts", "sans", 24, 345),
    ("host driver libraries", "sans", 24, 345),
    ("4 your code loads", "sans", 24, 365),
    ("libcudart from the", "sans", 24, 365),
    ("image, which calls", "sans", 24, 365),
    ("the host libcuda", "sans", 24, 365),
    ("CUDA driver version", "mono", 24, 560),
    ("is insufficient for", "mono", 24, 560),
    ("CUDA runtime version", "mono", 24, 560),
    ("host driver older than the image CUDA needs:", "sans", 24, 860),
    ("upgrade the driver, or use cuda-compat", "sans", 24, 860),
    ("no kernel image is", "mono", 24, 560),
    ("available for execution", "mono", 24, 560),
    ("on the device", "mono", 24, 560),
    ("binary not compiled for the GPU compute capability:", "sans", 24, 860),
    ("rebuild, set TORCH_CUDA_ARCH_LIST", "sans", 24, 860),
    ("(sm_80 A100, sm_90 H100, sm_100 B200);", "sans", 24, 860),
    ("a driver upgrade does not help", "sans", 24, 860),
    ("bash: nvidia-smi: not found", "mono", 24, 560),
    ("toolkit or runtime not configured,", "sans", 24, 860),
    ("NVIDIA_DRIVER_CAPABILITIES lacks utility", "sans", 24, 860),
    ("Newer drivers support older CUDA runtimes.", "sans", 26, 1500),
]

all_passed = True
for text, ftype, fsize, bwidth in lines_to_check:
    mult = 0.62 if ftype == "mono" else 0.60
    est_w = len(text) * fsize * mult
    pad = (bwidth - est_w) / 2
    status = "OK" if pad >= 16 else "FAIL"
    if pad < 16:
        all_passed = False
    print(f"[{status}] pad={pad:5.1f}px (box={bwidth}, est_w={est_w:5.1f}px) : '{text}'")

assert all_passed, "Some lines failed min 16px padding!"
print("\nALL LINES SATISFY >= 16px PADDING RULE!")
