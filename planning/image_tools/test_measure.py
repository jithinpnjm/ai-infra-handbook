import xml.etree.ElementTree as ET
import re

def test_measurements():
    # Test text lengths with 0.6 for sans and 0.62 for mono
    labels = {
        "title": "Checkpoint before the time limit: SIGUSR1 reaches the batch shell, then the trainer",
        "job_starts": "Job starts",
        "time_limit": "Time limit: SIGTERM, then SIGKILL after KillWait (default 30 s)",
        "marker": "#SBATCH --signal=B:USR1@180: Slurm sends SIGUSR1 to the batch shell",
        "box1_title": "Batch shell (script)",
        "box1_code": "trap kill -USR1 $pid; wait $pid USR1",
        "box2_text": "python train.py running in the background (&), pid saved in $pid",
        "box3_text": "wait $pid",
        "arrow1": "Slurm sends SIGUSR1 to the batch shell",
        "arrow2": "trap fires at once because the shell is in wait, not in a foreground command",
        "arrow3": "kill -USR1 forwards the signal to the training process",
        "arrow4": "training writes the checkpoint",
        "arrow5": "wait returns, job ends cleanly",
        "contrast": "If python train.py ran in the foreground, the shell would defer the trap until it finished",
        "bottom": "Start long-running children in the background and wait for them"
    }

    for k, v in labels.items():
        print(f"{k:12s} ({len(v):2d} chars): '{v}'")

test_measurements()
