# Verify padding of every text element

boxes = {
    "Card 1": {"x": 65, "y": 120, "w": 690, "h": 135},
    "Card 2": {"x": 65, "y": 275, "w": 690, "h": 115},
    "Card 3": {"x": 65, "y": 410, "w": 690, "h": 170},
    "Card 4": {"x": 65, "y": 600, "w": 690, "h": 280},
    "Card 5": {"x": 65, "y": 900, "w": 690, "h": 80},
    "Input":  {"x": 840, "y": 200, "w": 700, "h": 240},
    "Output": {"x": 840, "y": 660, "w": 700, "h": 260},
    "Warning":{"x": 40, "y": 1025, "w": 1520, "h": 60},
    "Bottom": {"x": 40, "y": 1105, "w": 1520, "h": 65}
}

# Check all text lines:
items = [
    # Card 1
    ("Card 1", "# {{ ansible_managed }}", 160, 26, True),
    ("Card 1", "first line marks the file as generated", 160, 24, False),
    ("Card 1", "so nobody edits it by hand", 160, 24, False),
    # Card 2
    ("Card 2", "127.0.0.1 localhost", 160, 26, True),
    ("Card 2", "second line keeps the loopback address", 160, 24, False),
    # Card 3
    ("Card 3", "for h in groups[cluster] | sort", 160, 26, True),
    ("Card 3", "the loop writes one line per host in sorted order:", 160, 24, False),
    ("Card 3", "the sort keeps the output the same on every render", 160, 24, False),
    # Card 4
    ("Card 4", "{{ hostvars[h][ansible_host] }}", 160, 24, True),
    ("Card 4", "{{ h }}.{{ cluster_domain }} {{ h }}", 160, 24, True),
    ("Card 4", "each line uses the host's ansible_host and", 160, 24, False),
    ("Card 4", "its name, so the file follows the inventory:", 160, 24, False),
    ("Card 4", "add a host to the inventory, run the", 160, 24, False),
    ("Card 4", "playbook, and the new line appears", 160, 24, False),
    ("Card 4", "without anyone touching the file", 160, 24, False),
    # Card 5
    ("Card 5", "endfor", 160, 26, True),
    # Input
    ("Input", "inventory entry gpu001 with its", 955, 26, False),
    ("Input", "ansible_host value, and the", 955, 26, False),
    ("Input", "cluster_domain variable", 955, 26, False),
    # Output
    ("Output", "the ansible_host value, then gpu001", 955, 26, False),
    ("Output", "followed by the cluster_domain", 955, 26, False),
    ("Output", "value, then gpu001", 955, 26, False),
    # Warning
    ("Warning", "cross-host data needs facts for those hosts: see the --limit trap", 120, 24, False),
]

all_pass = True
for box_name, text, text_x, fs, is_mono in items:
    b = boxes[box_name]
    char_w = 0.62 * fs if is_mono else 0.6 * fs
    w = len(text) * char_w
    right_edge = text_x + w
    box_right = b["x"] + b["w"]
    padding = box_right - right_edge
    left_padding = text_x - b["x"]
    if padding < 16 or left_padding < 16:
        print(f"FAIL: {box_name} '{text}' right_padding={padding:.1f}, left_padding={left_padding:.1f}")
        all_pass = False
    else:
        print(f"PASS: {box_name} '{text[:30]}' left={left_padding:.1f} right_pad={padding:.1f}")

print(f"\nAll padding > 16px: {all_pass}")
