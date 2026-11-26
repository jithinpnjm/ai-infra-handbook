from sim_layout import check_wrap

# Let's check heights:
# Total height of left area = y=175 to y=800 -> 625px!
# Gaps between boxes must be at least 40px!

# If we have:
# 1. Top row: Client and Host NIC (height say 90)
# Gap: 40px
# 2. netfilter chains container (height say 240)
# Gap: 40px
# 3. Fixes box (height say 215)
# Total height = 90 + 40 + 240 + 40 + 215 = 625px! Exactly 625px!

print("Testing exact height fit: 90 + 40 + 240 + 40 + 215 =", 90 + 40 + 240 + 40 + 215)

# Let's check wrapping in Client box (w=420 - 48 = 372):
client_text = "Client on the office network or anywhere"
c_lines = check_wrap(client_text, 372, size=24)
print("\nClient lines (w=372):", c_lines)

# Host NIC (w=372):
host_text = "Host NIC"
print("Host NIC:", host_text)

# Inside Fixes box (w=900 - 48 = 852):
fix1 = "restrict a port with the DOCKER-USER chain"
fix2 = "bind the port to a specific address (for example 127.0.0.1:8080:80)"
fix3 = "if a published port must stay private on a shared host, restrict it in DOCKER-USER before you publish it"

print("\nFixes lines (w=852):")
for f in [fix1, fix2, fix3]:
    lines = check_wrap(f, 852, size=24)
    print(" ", len(lines), lines)
