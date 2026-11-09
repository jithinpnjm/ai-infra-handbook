"""LLM-as-judge. The judge model is passed in; with MockLLM it uses keyword overlap so it is deterministic."""
import re

JUDGE_PROMPT = """You are evaluating the quality of an answer to a question.

Question: {question}
Ground truth: {ground_truth}
Candidate answer: {candidate_answer}

Score the candidate answer on a scale of 1-5:
- 1: completely wrong
- 3: partially correct
- 5: fully correct and matches the ground truth

Output only the integer score."""

def overlap_score(ground_truth: str, candidate: str) -> int:
    g = set(re.findall(r"[a-z]+", ground_truth.lower())); c = set(re.findall(r"[a-z]+", candidate.lower()))
    return 1 + round(4 * len(g & c) / max(len(g), 1))

def judge(question: str, ground_truth: str, candidate: str, judge_model=None) -> int:
    prompt = JUDGE_PROMPT.format(question=question, ground_truth=ground_truth, candidate_answer=candidate)
    if judge_model is None or type(judge_model).__name__ == "MockLLM":
        return overlap_score(ground_truth, candidate)   # offline stand-in for the judge's reply
    score = int(judge_model.complete(prompt).strip())
    if not 1 <= score <= 5: raise ValueError(f"judge returned out-of-range score {score}")
    return score
