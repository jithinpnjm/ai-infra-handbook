from sim_layout import check_wrap

cnm = "CNM: sandbox (the namespace config), endpoint (the attachment, typically a veth), network (a group of endpoints); local drivers bridge, host, none, macvlan, ipvlan; global driver overlay needs a key-value store"
lines = check_wrap(cnm, 1400, size=24)
print(f"CNM ({len(lines)} lines):")
for l in lines:
    print(f"  [{len(l):3d} ch, {len(l)*24*0.6:6.1f}px] {l}")
