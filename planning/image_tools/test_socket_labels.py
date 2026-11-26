import re
import xml.etree.ElementTree as ET

# Define expected labels
expected_labels = [
    "Socket buffers: what to raise, what to leave alone, and why",
    "send buffer: unacknowledged data on the send side",
    "receive buffer: data the application has not read yet",
    "Linux autotunes both within limits",
    "net.ipv4.tcp_rmem and tcp_wmem: min default max in bytes, for example 4096 131072 6291456",
    "net.core.rmem_max and wmem_max: cap for explicit SO_RCVBUF and SO_SNDBUF",
    "net.ipv4.tcp_mem: system-wide pages, low, pressure, high",
    "tcp_moderate_rcvbuf: receive autotuning (1)",
    "tcp_notsent_lowat: limit unsent data queued in the send buffer, reduces latency and bufferbloat, for example 131072",
    "For 10 to 100 Gb/s long paths raise the maxima",
    "tcp_rmem 4096 131072 134217728",
    "tcp_wmem 4096 65536 134217728",
    "rmem_max = wmem_max = 134217728",
    "Do not",
    "setting SO_RCVBUF or SO_SNDBUF in an application disables autotuning for that socket, almost always a mistake",
    "huge buffers on short-RTT paths add memory pressure and queueing delay: bufferbloat",
    "a 128 MB buffer on each of thousands of connections exhausts RAM; tcp_mem guards against it",
    "Same rack 100 Gb/s 20 microseconds: 250 KB; Same DC 100 Gb/s 100 microseconds: 1.25 MB; Metro 10 Gb/s 2 ms: 2.5 MB; Cross-continent 10 Gb/s 70 ms: 87.5 MB; Intercontinental 10 Gb/s 180 ms: 225 MB",
    "Choose buffer sizes from the BDP of the path you use, and leave autotuning on"
]

print(f"Total expected labels: {len(expected_labels)}")
