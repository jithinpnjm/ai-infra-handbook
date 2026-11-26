import xml.etree.ElementTree as ET
import re, subprocess, pathlib

# List of the 19 expected labels
expected_labels = [
    "Transfer, loss recovery and teardown: why TIME_WAIT fills up",
    "Receiving the body",
    "segments arrive shuffled",
    "socket receive buffer",
    "sends ACKs, often one for every second segment, with delayed ACK timers",
    "advertises its window: the amount of data it is ready to accept right now",
    "curl reads with recv",
    "Loss",
    "fast retransmit after three duplicate ACKs, or through SACK",
    "retransmission timeout fires",
    "congestion window collapses, then regrows",
    "Closing",
    "FIN, ACK exchange (or RST on abort)",
    "the side that closes first holds the connection in TIME_WAIT for about 60 seconds on Linux",
    "stops late packets from corrupting a new connection that reuses the same 5-tuple",
    "Thousands of short connections can exhaust ephemeral ports (32768 to 60999) or fill the table with TIME_WAIT entries",
    "ss -s",
    "ss -tni dst 93.184.216.34 (rtt, cwnd, mss, retrans, bytes)",
    "If your service opens thousands of short connections, watch the TIME_WAIT count before you scale it up"
]

print("Expected labels count:", len(expected_labels))
