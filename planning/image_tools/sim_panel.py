import textwrap

# Panel width = 740. Inside card width = 740 - 2*24 = 692.
# Let's say card width = 680, x_offset = 30 inside panel.
# If an icon is placed on the left:
# Icon width = 56, plus gap = 16. Total icon indent = 72 px.
# Or icon placed at top-left:
# If icon is 56x56 at (x+20, y+20).
# Text starts at x + 20 + 56 + 16 = x + 92.
# Text width = 680 - 92 - 20 = 568 px.
# With sans font size 24px: char width = 0.6 * 24 = 14.4 px.
# Max chars per line = 568 / 14.4 = 39.4 -> 38 chars.

# Alternatively, if icon is in a header row or left column:
# What if each node card has icon at top-left, or left side?
# Let's see how many cards Panel 1 and Panel 2 have.

# Panel 1:
# Header: Case 1: SNAT port exhaustion (font size 32 bold)
# Card 1: Flow + Arithmetic?
# Wait! Prompt says:
# Panel 'Case 1: SNAT port exhaustion':
# flow 'about 5,000 containers connect through one NAT IP to one database IP and port'
# with arithmetic 'one source IP has about 60,000 usable ephemeral ports per destination IP and port; each connection to that one database needs its own source port on the gateway'
# leading to 'ports run out, new connections get no mapping and time out; the database is healthy, CPU is low, dmesg shows no conntrack drops';
# metaphor 'a car park with a fixed number of spaces: the traffic is not heavy but all the spaces are taken' ;
# fix 'add NAT gateway IPs and ports (Cloud NAT port allocation), use a pooler such as PgBouncer, shorten TIME_WAIT, reuse connections';
# lesson 'count the tuple dimensions: source IP, destination IP and port'.

# Total items in Panel 1 = 6 items.
# If we have 5 cards (e.g. Card 1: Flow, Card 2: Arithmetic -> Arrow -> Card 3: Failure, Card 4: Metaphor, Card 5: Fix, Card 6: Lesson)
# Wait, can Flow and Arithmetic be grouped or separate?
# "a line with no arrowhead in the source ('---') means 'grouped together', so draw NO arrowhead and no step numbers for it."
# "flow '...' with arithmetic '...' leading to '...'"
# If Flow and Arithmetic are two boxes grouped together or in a container, then an arrow leads from that to Failure!

print("Testing card line wrapping:")
def wrap_test(text, width_chars):
    lines = textwrap.wrap(text, width=width_chars)
    return lines

