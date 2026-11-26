from sim_layout import check_wrap

fix1 = "restrict a port with the DOCKER-USER chain"
fix2 = "bind the port to a specific address (for example 127.0.0.1:8080:80)"
fix3 = "if a published port must stay private on a shared host, restrict it in DOCKER-USER before you publish it"

max_w = 820

for f in [fix1, fix2, fix3]:
    lines = check_wrap(f, max_w, size=24)
    print(f"Item ({len(lines)} lines):")
    for l in lines:
        w = len(l) * 24 * 0.6
        print(f"  [{len(l):2d} ch, {w:5.1f}px] {l}")
