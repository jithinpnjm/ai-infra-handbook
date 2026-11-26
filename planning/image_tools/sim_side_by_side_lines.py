from sim_layout import check_wrap

# Footer in w=720: inner width = 720 - 56 (icon) - 40 = 624
footer_text = "default subnet 172.17.0.0/16 may overlap corporate or VPN ranges: set default-address-pools in /etc/docker/daemon.json"
f_lines = check_wrap(footer_text, 624, size=24, mono=False)
print("Footer lines (inner=624):")
for l in f_lines:
    w = len(l) * 24 * 0.6
    print(f"  [{len(l):2d} ch, {w:5.1f}px / 624px] {l}")

# Inspect commands in w=760: inner width = 760 - 56 (icon) - 40 = 664
cmd_text = "docker network ls; docker network inspect bridge; iptables -t nat -S DOCKER; bridge fdb show br docker0"
c_lines = check_wrap(cmd_text, 664, size=24, mono=True)
print("\nInspect commands lines (mono, inner=664):")
for l in c_lines:
    w = len(l) * 24 * 0.62
    print(f"  [{len(l):2d} ch, {w:5.1f}px / 664px] {l}")
