bw = 1520

example_lines = [
    "the client capture shows a SYN-ACK arriving and the server capture shows",
    "the same SYN-ACK leaving with the same sequence numbers: the packet is gone",
    "between the two hosts, not inside the server; check route and NAT next"
]

print("=== Example pairing ===")
for txt in example_lines:
    w = len(txt) * 0.6 * 24
    rem = bw - w
    print(f"  '{txt}' ({len(txt)}c, {w:.1f}px) -> pad_r (if pad_l=30) = {rem - 30:.1f}px")
    assert rem - 30 >= 16

clock_lines = [
    "if the two captures disagree on order, check clocks first, then match",
    "by sequence number or IP ID, not by time; PTP with hardware timestamps",
    "is precise, NTP is good to about a millisecond; merge with mergecap -a"
]

print("\n=== Clock note ===")
# with icon at x=65, w=56 -> icon_r = 121
# text at x = 145 -> pad_l from box = 105, pad from icon = 24
for txt in clock_lines:
    w = len(txt) * 0.6 * 24
    rem = bw - (105 + w)
    print(f"  '{txt}' ({len(txt)}c, {w:.1f}px) -> pad_r = {rem:.1f}px")
    assert rem >= 16
