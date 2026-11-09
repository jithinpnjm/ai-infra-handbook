"""Output rails: safety and PII redaction. Rule-based stand-ins for trained classifiers."""
import re

UNSAFE = ("how to build a bomb", "kill yourself")
PII_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|\b\d{3}-\d{2}-\d{4}\b|\b\d{10}\b")

class SafetyClassifier:
    def score(self, text: str) -> float:
        return 0.99 if any(u in text.lower() for u in UNSAFE) else 0.01

safety_classifier = SafetyClassifier()

def redact_unsafe(text: str) -> str:
    return "[removed: unsafe content]"

def safety_filter(response: str, threshold: float = 0.9) -> tuple[str, bool]:
    """Return (filtered_response, passed). Redact if score exceeds threshold."""
    if safety_classifier.score(response) > threshold:
        return redact_unsafe(response), False
    return response, True

def pii_filter(response: str) -> tuple[str, bool]:
    """Return (filtered_response, passed). Redact PII if found."""
    redacted, n = PII_RE.subn("[REDACTED]", response)
    return (redacted, False) if n else (response, True)
