"""Draft a runbook with an LLM, then refuse to return it unless it passes runbook_validation. llm.complete(prompt) -> str is injected."""
from runbook_validation import validate_runbook

def build_prompt(incident_transcript: str, existing_runbooks: list[str]) -> str:
    return f"""You are an SRE generating a runbook for a new incident.

Existing runbooks for reference:
{chr(10).join(existing_runbooks)}

Incident transcript:
{incident_transcript}

Generate a runbook with exactly these 6 sections, as headings:
What the alert means / Symptoms / Diagnostic steps / Mitigation steps / Escalation path / Post-mortem template.
Put every command on its own line."""

def generate_runbook(llm, incident_transcript: str, existing_runbooks: list[str]) -> str:
    draft = llm.complete(build_prompt(incident_transcript, existing_runbooks))
    ok, errors = validate_runbook(draft)
    if not ok:
        raise ValueError("generated runbook rejected: " + "; ".join(errors))
    return draft
