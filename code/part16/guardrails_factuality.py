"""Grounding rail: an answer must be supported by its context. Word-overlap stand-in for an NLI/judge model."""
import re

JUDGE_PROMPT = """You are evaluating whether an answer is supported by its context.

Context: {context}
Answer: {answer}

If the answer is fully supported by the context, output "SUPPORTED".
If the answer contains claims not in the context, output "UNSUPPORTED: <claim>".

Output only the verdict."""

STOP = {"the", "a", "an", "is", "are", "of", "to", "and", "in", "on", "for", "it", "that"}

class FactualityClassifier:
    def score(self, answer: str, context: str) -> float:
        a = {w for w in re.findall(r"[a-z0-9]+", answer.lower()) if w not in STOP}
        c = set(re.findall(r"[a-z0-9]+", context.lower()))
        return len(a & c) / len(a) if a else 1.0

factuality_classifier = FactualityClassifier()

def factuality_filter(answer: str, context: str, threshold: float = 0.7) -> tuple[str, bool]:
    if factuality_classifier.score(answer, context) < threshold:
        return "I don't know based on the provided context.", False
    return answer, True
