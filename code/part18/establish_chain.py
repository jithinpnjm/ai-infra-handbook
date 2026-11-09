"""Build a measurement chain for a node from its boot components in order (firmware -> bootloader -> kernel -> dpu -> cvm)
and sign it with the local attestation key. Input: $SEC_HOME/nodes/<node>/components.json {name: content-string}."""
import argparse, sys
import seclib as S

ORDER = ["firmware", "bootloader", "kernel", "dpu", "cvm"]

def chain_for(components: dict, order=ORDER):
    pcr = "0" * 64; steps = []
    for name in order:
        if name not in components: raise KeyError(f"missing component {name}")
        m = S.sha(components[name].encode()); pcr = S.extend(pcr, m); steps.append({"component": name, "measurement": m, "pcr": pcr})
    return steps

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--node", required=True); ap.add_argument("--output", required=True); a = ap.parse_args(argv)
    comps = S.load_json(f"nodes/{a.node}/components.json")
    if comps is None: print("unknown node"); return 1
    try: steps = chain_for(comps)
    except KeyError as e: print("CHAIN NOT ESTABLISHED:", e); return 1
    doc = {"node": a.node, "steps": steps, "final_pcr": steps[-1]["pcr"]}; doc["signature"] = S.sign(S.attest_key(), doc["final_pcr"] + a.node)
    import json; open(a.output, "w").write(json.dumps(doc, indent=2)); S.audit("chain_established", node=a.node, final=doc["final_pcr"]); print(f"chain established: {len(steps)} steps, final {doc['final_pcr'][:16]}"); return 0

if __name__ == "__main__": sys.exit(main())
