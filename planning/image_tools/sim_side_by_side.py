from sim_layout import check_wrap

# Footer box width = 740. inner width = 740 - 48 = 692
footer_text = "default subnet 172.17.0.0/16 may overlap corporate or VPN ranges: set default-address-pools in /etc/docker/daemon.json"
f_lines = check_wrap(footer_text, 692, size=24, mono=False)
print("Footer lines (w=692):")
for l in f_lines:
    print(" ", len(l), l)

# Inspect commands box width = 740. inner width = 740 - 48 = 692
cmd_text = "docker network ls; docker network inspect bridge; iptables -t nat -S DOCKER; bridge fdb show br docker0"
c_lines = check_wrap(cmd_text, 692, size=24, mono=True)
print("\nInspect commands lines (mono, w=692):")
for l in c_lines:
    print(" ", len(l), l)
