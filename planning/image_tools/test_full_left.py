# Let's map out the exact boxes in Left Column:
# Column bounds: x = 50 to 780 (width = 730)

# Nodes:
# 1. Lookup query node: cfg["timeout"]
# 2. Layer 1: cli_args
# 3. Layer 2: os.environ (MYOPS_ prefixed, lowercased)
# 4. Layer 3: file_cfg (/etc/myops.json)
# 5. Layer 4: defaults {retries: 3, timeout: 30}
# 6. Resolution: first mapping wins
# 7. Small example: ChainMap({retries: 5}, {retries: 3, timeout: 10}): cfg[retries] is 5, cfg[timeout] is 10
# 8. Write rule (orange): a write such as chain[c] = -1 changes only the first mapping
# 9. Note: CLI values of None are dropped so they do not hide lower layers: {k: v for k, v in cli.items() if v is not None}

print("Nodes count on Left: 9")
