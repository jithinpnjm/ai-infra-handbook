import re

def text_width(text, size=24, is_mono=False):
    rate = 0.62 if is_mono else 0.6
    return len(text) * size * rate

# Check items
items = [
    "own interfaces",
    "own IP addresses",
    "own routing tables",
    "own ARP and ND neighbour tables",
    "own netfilter rules",
    "own conntrack table",
    "own /proc/net"
]

box_w = 700
card_w = box_w - 40 # 660
inner_w = card_w - 32 # 628 (16px padding on each side)
icon_w = 56 + 16 # 72

print(f"Card width: {card_w}, Inner width with icon: {inner_w - icon_w}")

for it in items:
    w_26 = text_width(it, 26, False)
    w_24 = text_width(it, 24, False)
    print(f"Item: '{it}' len={len(it)}: w(26)={w_26:.1f}px, w(24)={w_24:.1f}px")

callout = "two containers can both serve on port 8080: each has its own port space"
print(f"Callout: w(26)={text_width(callout, 26):.1f}px, w(24)={text_width(callout, 24):.1f}px")

cmds = [
    "ip netns add red",
    "ip netns exec red ip link",
    "(only a down loopback at first)",
    "ip -n red link set lo up"
]
for c in cmds:
    is_m = not c.startswith("(")
    print(f"Cmd: '{c}' w={text_width(c, 24, is_m):.1f}px")

note = "nsenter -t <pid> -n ip addr enters a container namespace by PID"
print(f"Note: w(24)={text_width(note, 24, False):.1f}px, w(26)={text_width(note, 26, False):.1f}px")

