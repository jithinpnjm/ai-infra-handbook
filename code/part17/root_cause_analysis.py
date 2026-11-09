"""LLM-assisted root-cause hypotheses. The model call is injected (llm.complete(prompt) -> str), so the prompt and the
parser are testable offline. The model must answer in JSON; anything else is rejected rather than guessed at."""
import json

def build_prompt(traces, logs, metrics, failure_mode_catalogue):
    return f"""You are an SRE analysing a production incident.

Failure mode catalogue:
{chr(10).join(failure_mode_catalogue)}

Traces:
{json.dumps(traces)[:4000]}

Logs (first 100):
{chr(10).join(logs[:100])}

Metrics:
{json.dumps(metrics)}

Return a JSON list of exactly 3 objects with keys: hypothesis, evidence, mitigation, confidence (integer 1-5).
Return JSON only."""

def parse_hypotheses(text: str) -> list[dict]:
    try:
        items = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"model did not return JSON: {e}")
    need = {"hypothesis", "evidence", "mitigation", "confidence"}
    if not isinstance(items, list) or not items or any(not need <= set(i) for i in items):
        raise ValueError("hypotheses missing required keys")
    if any(not isinstance(i["confidence"], int) or not 1 <= i["confidence"] <= 5 for i in items):
        raise ValueError("confidence must be an integer 1-5")
    return sorted(items, key=lambda i: -i["confidence"])

def analyze_root_cause(llm, traces, logs, metrics, failure_mode_catalogue):
    return parse_hypotheses(llm.complete(build_prompt(traces, logs, metrics, failure_mode_catalogue)))
