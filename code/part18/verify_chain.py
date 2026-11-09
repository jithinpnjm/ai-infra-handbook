"""Verify a chain file: recompute every extend, check the signature, and compare each step with the golden values for the node
($SEC_HOME/golden/<node>.json {component: measurement}) so a changed component is named."""
import argparse, hmac, json, sys
import seclib as S

def verify(doc, golden=None):
    problems = []; pcr = "0" * 64
    for st in doc["steps"]:
        pcr = S.extend(pcr, st["measurement"])
        if pcr != st["pcr"]: problems.append(f"{st['component']}: chain broken (recomputed PCR differs)")
        if golden and golden.get(st["component"]) not in (None, st["measurement"]): problems.append(f"{st['component']}: measurement differs from golden value")
    if not hmac.compare_digest(S.sign(S.attest_key(), pcr + doc["node"]), doc["signature"]): problems.append("signature invalid")
    return problems

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--chain", required=True); a = ap.parse_args(argv)
    doc = json.load(open(a.chain)); p = verify(doc, S.load_json(f"golden/{doc['node']}.json"))
    S.audit("chain_verified", node=doc["node"], ok=not p)
    print("chain valid" if not p else "CHAIN INVALID:\n  " + "\n  ".join(p)); return 1 if p else 0

if __name__ == "__main__": sys.exit(main())
