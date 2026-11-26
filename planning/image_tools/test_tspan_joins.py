import re

cases = [
    # Title
    ("RED for LLM serving: duration splits into four parts, each with its own fix",
     ["RED for LLM serving: duration splits into ", "four parts, each with its own fix"]),
    # TTFT segment
    ("time to first token (TTFT)",
     ["time to first token ", "(TTFT)"]),
    # TPOT segment
    ("time per output token (TPOT)",
     ["time per output token ", "(TPOT)"]),
    # Card 1 body
    ("waiting before service starts: arrivals exceed capacity, or the batch scheduler holds batches for a fill timeout",
     ["waiting before ", "service starts: ", "arrivals exceed ", "capacity, or the ", "batch scheduler ", "holds batches for ", "a fill timeout"]),
    # Card 2 body
    ("prompt processing and everything before the first token",
     ["prompt processing and ", "everything before ", "the first token"]),
    # Card 3 body
    ("steady generation speed per token",
     ["steady generation ", "speed per token"]),
    # Rule box
    ("The request rate shows at once whether a slowdown comes with more load (a load problem) or with the same load (architecture or resources)",
     ["The request rate shows at once whether a ", "slowdown comes with more load (a load problem) ", "or with the same load (architecture or ", "resources)"]),
    # Side list
    ("Also track: tokens/s, batch size, KV-cache utilisation, preemptions and evictions",
     ["Also track: tokens/s, batch size, ", "KV-cache utilisation, preemptions ", "and evictions"])
]

for expected, parts in cases:
    joined = "".join(parts).strip()
    joined = re.sub(r'\s+', ' ', joined)
    assert joined == expected, f"FAIL!\nExpected: '{expected}'\nGot:      '{joined}'"
    print(f"[OK] '{expected[:40]}...'")
