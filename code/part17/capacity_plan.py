"""Next-quarter GPU order: ceil(current * (1 + growth) * (1 + buffer)) - current is the ORDER; the total is the target fleet."""
import argparse, math, sys

def plan(current, growth, buffer):
    target = math.ceil(round(current * (1 + growth) * (1 + buffer), 9))
    return target, target - current

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--current-gpu-count", type=int, required=True); ap.add_argument("--growth-rate", type=float, required=True)
    ap.add_argument("--buffer", type=float, required=True); ap.add_argument("--output"); a = ap.parse_args(argv)
    target, order = plan(a.current_gpu_count, a.growth_rate, a.buffer)
    txt = f"# Procurement order\n\nCurrent: {a.current_gpu_count}\nTarget fleet (Q+1): {target}\nOrder: {order}\n"
    if a.output: open(a.output, "w").write(txt)
    print(f"target fleet {target} GPUs (order {order} more)"); return 0

if __name__ == "__main__": sys.exit(main())
