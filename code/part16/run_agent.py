"""Minimal retrieval agent with an iteration cap and a cost cap. Tools: search (local index). Cost is counted per call."""
import argparse, sys
import mlplat_local as P

COST_PER_CALL = 0.02

def retrieve(snap: str, query: str, k=2):
    idx = P.load(f"index_{snap}.json", {"docs": {}})["docs"]; q = P.embed(query)
    return sorted(((P.cosine(q, d["vec"]), n, d["text"]) for n, d in idx.items()), reverse=True)[:k]

def run(query, snap, max_iterations=5, max_cost=0.10):
    trace, cost, ctx = [], 0.0, []
    for i in range(max_iterations):
        if cost + COST_PER_CALL > max_cost: trace.append({"stop": "budget"}); break
        cost += COST_PER_CALL
        hits = retrieve(snap, query) if i == 0 else []
        trace.append({"step": i, "tool": "search", "hits": [h[1] for h in hits]}); ctx += [h[2] for h in hits if h[0] > 0]
        if i == 0: continue
        break
    answer = P.MockLLM().complete(query + " " + " ".join(ctx)); cost += COST_PER_CALL
    P.audit("agent_run", query=query, cost=round(cost, 3), steps=len(trace))
    return {"trace": trace, "answer": answer, "cost": round(cost, 3)}

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--query", required=True); ap.add_argument("--snapshot"); ap.add_argument("--max-iterations", type=int, default=5)
    ap.add_argument("--max-cost", type=float, default=0.10); a = ap.parse_args(argv)
    snap = a.snapshot or (list(P.load("index_meta.json", {})) or [""])[-1]
    r = run(a.query, snap, a.max_iterations, a.max_cost)
    for t in r["trace"]: print(t)
    print("answer:", r["answer"]); print(f"cost: ${r['cost']:.2f}"); return 0 if r["cost"] <= a.max_cost else 1

if __name__ == "__main__": sys.exit(main())
