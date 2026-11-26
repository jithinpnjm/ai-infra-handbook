import re

# Test lines and character counts
label1 = "Count visible GPUs: shell nvidia-smi -L | wc -l, args executable /bin/bash, register gpu_count, changed_when false (read-only, never changed), failed_when gpu_count.rc != 0 or (gpu_count.stdout | int) != expected_gpus, check_mode false (run even under --check, safe because read-only)"
label2 = "Ansible starts /bin/bash, which runs nvidia-smi -L and pipes the listing into wc -l; the count comes back as text in gpu_count.stdout; failed_when converts it with int and compares with the expected count; a node showing seven GPUs when eight are expected fails the task at once and the message names the task"
label3 = "nvidia-smi fails with an error while wc succeeds on empty output: the pipeline reports success and the playbook believes the node has no GPUs and moves on"
label4 = "set -o pipefail works only in bash, so the probe needs executable /bin/bash and set -o pipefail; if that gets fragile keep the probe simple or split it into a module call plus Jinja filters"
label5 = "A pipe takes the exit code of its last command"

# Card 1 lines:
lines1 = [
    "Count visible GPUs:",
    "shell nvidia-smi -L | wc -l,",
    "args executable /bin/bash,",
    "register gpu_count,",
    "changed_when false (read-only, never changed),",
    "failed_when gpu_count.rc != 0 or",
    "(gpu_count.stdout | int) != expected_gpus,",
    "check_mode false (run even under --check,",
    "safe because read-only)"
]
assert " ".join(lines1) == label1

# Card 2 lines:
lines2 = [
    "Ansible starts /bin/bash, which runs",
    "nvidia-smi -L and pipes the listing into",
    "wc -l; the count comes back as text in",
    "gpu_count.stdout; failed_when converts",
    "it with int and compares with the expected",
    "count; a node showing seven GPUs when eight",
    "are expected fails the task at once and",
    "the message names the task"
]
assert " ".join(lines2) == label2

# Card 3 lines:
lines3 = [
    "nvidia-smi fails with an error while wc",
    "succeeds on empty output: the pipeline",
    "reports success and the playbook believes",
    "the node has no GPUs and moves on"
]
assert " ".join(lines3) == label3

# Card 4 lines:
lines4 = [
    "set -o pipefail works only in bash, so the",
    "probe needs executable /bin/bash and",
    "set -o pipefail; if that gets fragile keep",
    "the probe simple or split it into a module",
    "call plus Jinja filters"
]
assert " ".join(lines4) == label4

print("All line splits exactly reconstruct labels!")
