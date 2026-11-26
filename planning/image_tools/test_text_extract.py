import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_output.svg")
root = tree.getroot()
ns = {"svg": "http://www.w3.org/2000/svg"}

def get_text_from_node(elem):
    text = elem.text or ""
    for child in elem:
        text += get_text_from_node(child)
        if child.tail:
            text += child.tail
    return text

# Extract text per major group / card
cards = [
    ("Title", root.find("svg:title", ns)),
    ("Header", root.find(".//svg:g[@id='section-comparison']/svg:text", ns)),
    ("Card Left", root.find(".//svg:g[@id='card-left']", ns)),
    ("Card Right", root.find(".//svg:g[@id='card-right']", ns)),
    ("Recipe 1", root.find(".//svg:g[@id='recipe-1']", ns)),
    ("Recipe 2", root.find(".//svg:g[@id='recipe-2']", ns)),
    ("Recipe 3", root.find(".//svg:g[@id='recipe-3']", ns)),
    ("Recipe 4", root.find(".//svg:g[@id='recipe-4']", ns)),
    ("Notes Header", root.find(".//svg:g[@id='section-option-notes']/svg:text", ns)),
    ("Note 1", root.find(".//svg:g[@id='note-1']", ns)),
    ("Note 2", root.find(".//svg:g[@id='note-2']", ns)),
    ("Note 3", root.find(".//svg:g[@id='note-3']", ns)),
]

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

for (name, elem), expected in zip(cards, expected_labels):
    extracted = re.sub(r'\s+', ' ', get_text_from_node(elem)).strip()
    norm_expected = re.sub(r'\s+', ' ', expected).strip()
    match = (extracted == norm_expected)
    print(f"[{name}] Match: {match}")
    if not match:
        print(f"  Expected:  '{norm_expected}'")
        print(f"  Extracted: '{extracted}'")
