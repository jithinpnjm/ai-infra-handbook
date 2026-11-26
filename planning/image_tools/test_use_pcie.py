import xml.etree.ElementTree as ET
import re

expected_labels = [
    "The USE method applied to a NIC and its PCIe slot",
    "Utilization: the busy fraction = throughput divided by the negotiated speed, counting all headers; with cloud caps use the limit the cloud imposes",
    "Saturation: queueing: qdisc backlog and drops, application threads blocked on send, TCP retransmits as a symptom, NIC ring overruns",
    "Errors: on RX bad checksums and frames too short or too long; on TX late collisions and carrier errors; check errors first",
    "PCIe Gen4 x16: about 252 Gb/s usable; one 400G NIC in that slot reaches only 252 / 400 = 0.63, about 63 percent of line rate",
    "PCIe Gen5 x16: about 504 Gb/s, enough for a 400G port",
    "apply the same method to the NIC controller and the bus: sum the port throughputs and compare the total with the PCIe bandwidth; and to the kernel stack: softirq CPU, memory for socket buffers, the conntrack table",
    "USE report for a 400G NIC: Gen4 x16 252 Gb/s versus Gen5 x16 504 Gb/s",
    "A slot can cap a NIC before the link does"
]

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels, 1):
    print(f"{i}. '{l}'")
