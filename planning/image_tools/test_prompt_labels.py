import xml.etree.ElementTree as ET
import re

prompt_labels = [
    "Checkpoint before the time limit: SIGUSR1 reaches the batch shell, then the trainer",
    "Job starts",
    "Time limit: SIGTERM, then SIGKILL after KillWait (default 30 s)",
    "#SBATCH --signal=B:USR1@180: Slurm sends SIGUSR1 to the batch shell",
    "Batch shell (script)",
    "trap kill -USR1 $pid; wait $pid USR1",
    "python train.py running in the background (&), pid saved in $pid",
    "wait $pid",
    "Slurm sends SIGUSR1 to the batch shell",
    "trap fires at once because the shell is in wait, not in a foreground command",
    "kill -USR1 forwards the signal to the training process",
    "training writes the checkpoint",
    "wait returns, job ends cleanly",
    "If python train.py ran in the foreground, the shell would defer the trap until it finished",
    "Start long-running children in the background and wait for them"
]

print(f"Total prompt labels: {len(prompt_labels)}")
for i, l in enumerate(prompt_labels, 1):
    print(f"{i:2d}. {l}")
