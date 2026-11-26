import xml.etree.ElementTree as ET
import re

# Exact labels:
TITLE = "The twelve lab steps, from a healthy trace to the faults"
DESC = "Visual infographic ladder of twelve lab steps in three groups: reading a healthy trace, injecting faults and comparing, and using wider diagnostic tools."

GROUP_1 = "Read a healthy trace"
GROUP_2 = "Inject a fault and compare"
GROUP_3 = "Wider tools"

PRE_STEP = "python3 code/part02/packet_capture_bpf_lab.py checks the byte-offset filters, the 8.13 Mpps rate at 100 Gb/s, ring storage with -s 96, and the two-endpoint comparison"
BOTTOM_BAR = "The healthy trace from step 1 is the reference that makes the faulty traces stand out"

STEP_LABELS = {
    1: "1 Handshake and teardown: curl to local nginx, label SYN, SYN-ACK, ACK, FIN, export with tshark -z follow",
    2: "2 Filters: five capture filters for SYN only, RST, a port range, DSCP EF and VLAN, verified with tcpdump -d and hit counts, then the same logic as display filters",
    3: "3 Retransmissions and loss: tc qdisc add dev veth1 root netem loss 2%, compare with 0% loss",
    4: "4 MTU black hole: smaller MTU on a router namespace, drop ICMP type 3 code 4, then fix with MSS clamping",
    5: "5 Zero window: a server that sleeps before it reads",
    6: "6 TLS: SSLKEYLOGFILE=/tmp/keys.log curl https://localhost, read SNI and ALPN",
    7: "7 Offload artefacts: TSO and checksum offload on then off",
    8: "8 Overlay: VXLAN link as in chapter 2.17, Decode As",
    9: "9 Ring buffer and trigger: tcpdump -C 10 -W 5 plus a stop script",
    10: "10 BPF tools: tcplife, tcpconnect, tcpretrans, tcpdrop, three bpftrace one-liners",
    11: "11 Container capture: nsenter, then docker run --network container:NAME nicolaka/netshoot tcpdump",
    12: "12 Clean up and delete captures, key log and ring-buffer directory",
}

print("Configuration ready.")
