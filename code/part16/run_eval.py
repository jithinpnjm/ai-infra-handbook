"""Run an eval set (jsonl: {question, ground_truth}) through a prompt template and a model. --model mock uses the offline MockLLM."""
import argparse, json, sys
import mlplat_local as P
from llm_as_judge import judge

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--eval-set", required=True); ap.add_argument("--prompt-template", default=None)
    ap.add_argument("--model", default="mock"); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    if a.model != "mock": print("only --model mock runs offline"); return 2
    llm = P.MockLLM(); tmpl = open(a.prompt_template).read() if a.prompt_template else "{question}"
    res = []
    for line in open(a.eval_set):
        if not line.strip(): continue
        c = json.loads(line); ans = llm.complete(tmpl.replace("{{ question }}", c["question"]).replace("{question}", c["question"]))
        res.append({"question": c["question"], "answer": ans, "score": judge(c["question"], c["ground_truth"], ans, llm)})
    out = {"n": len(res), "mean_score": sum(r["score"] for r in res) / max(len(res), 1), "results": res}
    json.dump(out, open(a.output, "w"), indent=2); print(f"{out['n']} cases, mean score {out['mean_score']:.2f}"); return 0

if __name__ == "__main__": sys.exit(main())
