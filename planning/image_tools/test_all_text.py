import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_output.svg")
root = tree.getroot()
ns = {"svg": "http://www.w3.org/2000/svg"}

def get_text(elem):
    text = elem.text or ""
    for child in elem:
        text += get_text(child)
        if child.tail:
            text += child.tail
    return text

# Get all text elements in SVG
all_svg_text = ""
for t in root.findall(".//svg:text", ns):
    all_svg_text += " " + get_text(t)

all_svg_text = re.sub(r'\s+', ' ', all_svg_text).strip()
print("All text in SVG:")
print(all_svg_text)

expected_labels = [
    "Per node or total: the first two request options",
    "Worked comparison on a two-node job asking for four GPUs",
    "--gres=gpu:4 (or --gpus-per-node=4): per node; with --nodes=2 every node gets four GPUs, eight in total",
    "--gpus=4 (-G 4): total for the job; Slurm decides the split, for example 2 plus 2, or all four on one node; can fragment placement and hurt NCCL, use only for jobs that tolerate it",
    "single-node training, all GPUs: --gres=gpu:8 or --gpus-per-node=8, add --exclusive for a dedicated node",
    "multi-node, one process per GPU (PyTorch): --nodes=N --ntasks-per-node=8 --gpus-per-node=8 plus --cpus-per-gpu or --cpus-per-task for data-loader threads, result N times 8 ranks, one GPU each",
    "several independent tasks in one allocation: --gpus-per-task=1 with an explicit -n, each task gets its own GPU",
    "interactive: salloc --gres=gpu:1 --cpus-per-gpu=8 --mem-per-gpu=64G --time=1:00:00 then srun --pty bash",
    "Option notes:",
    "--gpus-per-task needs an explicit task count and implicitly sets --tres-bind=gres/gpu:per_task:N",
    "--cpus-per-gpu is not compatible with --cpus-per-task",
    "--mem-per-gpu is exclusive with --mem and --mem-per-cpu, default is the partition DefMemPerGPU"
]

all_expected_text = " ".join(expected_labels)
all_expected_text = re.sub(r'\s+', ' ', all_expected_text).strip()

print("\nAll expected text:")
print(all_expected_text)

print(f"\nLengths: SVG={len(all_svg_text)}, Expected={len(all_expected_text)}")
if all_svg_text == all_expected_text:
    print("PERFECT MATCH: The text in the SVG consists of EXACTLY the expected labels, each appearing once, with NOTHING ELSE!")
else:
    print("MISMATCH!")
    import difflib
    print("\n".join(difflib.ndiff([all_svg_text], [all_expected_text])))
