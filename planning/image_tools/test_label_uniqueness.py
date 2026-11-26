import xml.etree.ElementTree as ET

tree = ET.parse("output_first60.svg")
root = tree.getroot()

# Collect all text snippets from the SVG
text_nodes = []
for elem in root.iter():
    tag = elem.tag.split('}')[-1]
    if tag in ['title', 'desc', 'text', 'tspan']:
        t = elem.text
        if t and t.strip():
            text_nodes.append((tag, t.strip()))

for tag, t in text_nodes:
    print(f"<{tag}>: {t}")

# Check exact labels
labels = [
    "The first minute: ten commands, each asks one question",
    "The first 60 seconds, command by command",
    "1 second interval",
    "read top to bottom",
    "CPU",
    "Memory and disk",
    "Network",
    "uptime",
    "Is demand rising or falling? Compare the 1, 5 and 15 minute numbers.",
    "dmesg -T | tail",
    "Did the kernel log errors, including OOM kills?",
    "vmstat -SM 1",
    "first row is since boot",
    "Run queue, swapping and overall CPU split, one second at a time.",
    "mpstat -P ALL 1",
    "Is one CPU busy while the others idle?",
    "pidstat 1",
    "Which processes use the CPU, and user or kernel time?",
    "iostat -sxz 1",
    "Disk IOPS, throughput, wait time and percent busy.",
    "free -m",
    "Memory in use, including the page cache.",
    "sar -n DEV 1",
    "Network interface throughput and packets.",
    "sar -n TCP,ETCP 1",
    "TCP connection rates and retransmits.",
    "top",
    "A sanity overview of everything above.",
    "Run the checklist top to bottom without stopping to theorise, then say what each line told you."
]

print("\n--- OCCURRENCE CHECK ---")
full_doc = open("output_first60.svg").read()
# Note that <desc> has:
# <desc>Ten numbered commands in order, each beside the one question it answers, grouped by CPU, memory and disk, and network.</desc>

for l in labels:
    # count how many times label l appears in the SVG text
    c = full_doc.count(l)
    print(f"'{l[:40]}...': count = {c}")
    assert c == 1, f"Label '{l}' appeared {c} times (expected exactly 1)!"

print("\nSUCCESS: Every single label appears exactly once!")
