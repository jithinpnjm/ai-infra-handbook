def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

c1 = "ansible gpu001 -m ansible.builtin.setup | less: every fact for one host, scroll the whole dictionary"
c2 = "setup -a filter=ansible_default_ipv4: narrows to the default network route"
c3 = "setup -a gather_subset=!all,!min,network,hardware: excludes all and min, gathers only network and hardware: the command to run when a node misbehaves"

right = "distribution, kernel, CPU count, memory, mounts, network interfaces and addresses, DMI info (the hardware identity the BIOS reports, such as vendor and model), environment, date and time, SELinux, user, Python"

print("=== Split test: Left width 840 (max chars ~ 52 mono, 55 sans), Right width 640 (max chars ~ 40 sans) ===")
print("C1 (max 52):")
for l in wrap_text(c1, 52):
    print(" ", len(l), l)
print("C2 (max 52):")
for l in wrap_text(c2, 52):
    print(" ", len(l), l)
print("C3 (max 52):")
for l in wrap_text(c3, 52):
    print(" ", len(l), l)
print("Right (max 40):")
for l in wrap_text(right, 40):
    print(" ", len(l), l)
