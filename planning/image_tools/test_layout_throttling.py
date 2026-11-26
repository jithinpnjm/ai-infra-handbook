import re

# Font metric conservative estimates per Luna rules:
# sans: 0.6 * font-size per char
# monospace: 0.62 * font-size per char

def sans_w(text, fs=24):
    return len(text) * 0.6 * fs

def mono_w(text, fs=24):
    return len(text) * 0.62 * fs

print("Checking line fits...")

# Left Panel Card 1:
c1_lines = [
    "usage_usec, user_usec, system_usec,",
    "nr_periods, nr_throttled,",
    "throttled_usec, nr_bursts, burst_usec"
]
for l in c1_lines:
    w = mono_w(l, 24)
    print(f"C1 mono: {w:.1f}px (fits in 600px? {w <= 600}) '{l}'")

# Left Panel Card 2:
c2_lines = [
    "compare nr_throttled with nr_periods",
    "and check throttled_usec"
]
for l in c2_lines:
    w = sans_w(l, 25)
    print(f"C2 sans: {w:.1f}px (fits in 600px? {w <= 600}) '{l}'")

# Left Panel Card 3:
c3_lines = [
    "container_cpu_cfs_throttled_periods_total",
    "and container_cpu_cfs_periods_total"
]
for l in c3_lines:
    w = mono_w(l, 24)
    print(f"C3 mono: {w:.1f}px (fits in 640px? {w <= 640}) '{l}'")

# Left Panel Card 4:
c4_lines = ["cpu.pressure (PSI)"]
for l in c4_lines:
    w = mono_w(l, 28)
    print(f"C4 mono: {w:.1f}px (fits in 600px? {w <= 600}) '{l}'")

# Right Panel Host Box: '64 CPUs'
# Container Box: 'cpu.max = 200000 100000 (2 CPUs)'
w_cbox = mono_w("cpu.max = 200000 100000 (2 CPUs)", 24)
print(f"Container box mono: {w_cbox:.1f}px (fits in 520px? {w_cbox <= 520})")

# Result Box:
res_lines = [
    "the quota is burned early in each period,",
    "then every thread pauses even though",
    "other CPUs are idle"
]
for l in res_lines:
    w = sans_w(l, 24)
    print(f"Result sans: {w:.1f}px (fits in 600px? {w <= 600}) '{l}'")

# Fix Table 4 cards:
fix_cards = [
    "Go: automaxprocs (GOMAXPROCS)",
    "Java: -XX:ActiveProcessorCount",
    "OpenMP: OMP_NUM_THREADS",
    "Python: os.cpu_count() reports the host, pass the limit in"
]
for fc in fix_cards:
    w = mono_w(fc, 24)
    print(f"Fix card mono: {w:.1f}px '{fc}'")

