with open("test.svg") as f:
    s = f.read()

old_panic = """    <tspan x="1140" dy="0">panic thresholds: when</tspan>
    <tspan x="1140" dy="28">too many hosts are</tspan>
    <tspan x="1140" dy="28">unhealthy, spread traffic</tspan>
    <tspan x="1140" dy="28">to all rather than overload</tspan>
    <tspan x="1140" dy="28">the few that remain</tspan>"""

new_panic = """    <tspan x="1140" dy="0">panic thresholds:</tspan>
    <tspan x="1140" dy="28">when too many hosts</tspan>
    <tspan x="1140" dy="28">are unhealthy, spread</tspan>
    <tspan x="1140" dy="28">traffic to all rather</tspan>
    <tspan x="1140" dy="28">than overload the few</tspan>
    <tspan x="1140" dy="28">that remain</tspan>"""

assert old_panic in s
s = s.replace(old_panic, new_panic)
with open("test.svg", "w") as f:
    f.write(s)
print("Replaced successfully!")
