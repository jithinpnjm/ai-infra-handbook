"""Input rail: block prompts that look like jailbreaks. Rule-based stand-in for a trained classifier."""
PATTERNS = ("ignore previous instructions", "disregard your rules", "pretend you have no restrictions", "developer mode")

class JailbreakClassifier:
    def score(self, prompt: str) -> float:
        low = prompt.lower()
        return 0.95 if any(p in low for p in PATTERNS) else 0.05

jailbreak_classifier = JailbreakClassifier()

def jailbreak_filter(prompt: str, threshold: float = 0.8) -> bool:
    """Return True if the prompt is safe to send to the LLM."""
    return jailbreak_classifier.score(prompt) < threshold
