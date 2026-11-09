"""Send a prompt through input guardrails -> LLM -> output guardrails (all local). --llm-url/--guardrail-url are accepted and ignored offline."""
import argparse, sys
import mlplat_local as P

def input_check(prompt):
    low = prompt.lower()
    if "ignore previous instructions" in low: return "jailbreak"
    if P.contains_pii(prompt): return "pii_in_prompt"
    return None

def output_check(text):
    return "pii_in_output" if P.contains_pii(text) else None

def guarded(prompt, llm=None):
    llm = llm or P.MockLLM()
    r = input_check(prompt)
    if r: return {"blocked": r, "response": "Request blocked."}
    out = llm.complete(prompt); r = output_check(out)
    return {"blocked": r, "response": "Response withheld." if r else out}

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--prompt", required=True); ap.add_argument("--llm-url"); ap.add_argument("--guardrail-url"); a = ap.parse_args(argv)
    r = guarded(a.prompt); print(r); return 0

if __name__ == "__main__": sys.exit(main())
