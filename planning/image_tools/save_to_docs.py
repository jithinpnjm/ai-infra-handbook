import pathlib

svg = pathlib.Path("final_pinned_budget.svg").read_text()
dst = pathlib.Path("../../docs/part-20-nebius-sre-interview/img/p2-2005-pinned-budget.svg")
dst.write_text(svg)
print("Saved to", dst)
