import re

# Font width estimation functions
def text_width(text, font_size=24, is_mono=False):
    rate = 0.62 if is_mono else 0.6
    return len(text) * font_size * rate

# 14 labels
labels = {
    "title": "Two NICs on one subnet: why the wrong card answers ARP and the four settings that fix it",
    "left_title": "Default (weak host)",
    "eth0": "eth0 10.20.0.1",
    "eth1": "eth1 10.20.0.2",
    "wrong_port": "learns the IP on the wrong port",
    "caption": "Linux answers an ARP request for any local IP on any interface",
    "right_title": "Recipe for multi-homed servers",
    "recipe1": "arp_ignore=1: reply only if the target IP is configured on the receiving interface",
    "recipe2": "arp_announce=2: always use the best source address of the outgoing interface in ARP requests",
    "recipe3": "rp_filter=2: loose reverse path filtering (strict mode 1 drops asymmetric traffic)",
    "recipe4": "policy routing with one routing table per NIC so replies leave on the interface that received the request",
    "footer": "Also: arp_filter=1 answers only if the route to the sender would use this interface; arp_notify sends a gratuitous ARP when an interface comes up or the address changes; all keys are per interface",
    "result": "Symptoms without the recipe: asymmetric paths, RDMA and NCCL oddities, flapping MAC tables, confused bonding; often seen only after another NIC is plugged in",
    "takeaway": "Each setting makes the server answer only for the address that belongs to the card the question arrived on"
}

print("Labels loaded successfully:", len(labels))
