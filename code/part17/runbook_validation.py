import re

REQUIRED_SECTIONS = [
    "What the alert means",
    "Symptoms",
    "Diagnostic steps",
    "Mitigation steps",
    "Escalation path",
    "Post-mortem template",
]

COMMAND = re.compile(r"^\s*(?:\$ )?(kubectl|dcgmi|nvidia-smi|helm|systemctl|journalctl|scontrol|sinfo)\b", re.M)

def validate_runbook(runbook: str) -> tuple[bool, list[str]]:
    errors = [f"Missing section: {s}" for s in REQUIRED_SECTIONS if s not in runbook]
    if not COMMAND.search(runbook):
        errors.append("No runnable commands found (expected at least one kubectl/dcgmi/nvidia-smi/... line)")
    return len(errors) == 0, errors
