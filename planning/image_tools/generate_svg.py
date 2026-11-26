import re
import xml.etree.ElementTree as ET

# Source labels exact list:
exact_labels = [
    "Why a published Docker port ignores your firewall rule",
    "Client on the office network or anywhere",
    "Host NIC",
    "netfilter chains",
    "Docker's own NAT and FORWARD rules (DOCKER chain) are inserted ahead of the rules managed by ufw or firewalld",
    "container port 80",
    "published port 8080 answers from anywhere",
    "ufw or firewalld rule that should block the port",
    "restrict a port with the DOCKER-USER chain",
    "bind the port to a specific address (for example 127.0.0.1:8080:80)",
    "if a published port must stay private on a shared host, restrict it in DOCKER-USER before you publish it",
    "Docker network modes",
    "bridge: private subnet, veth per container, NAT outbound, -p publishes via DNAT; user-defined bridges add DNS-based name resolution and isolation",
    "host: shares the host namespace, no isolation, no NAT, best performance, ports conflict with host: NCCL or HPC containers",
    "none: only loopback",
    "container:NAME: shares another container's namespace (how a Kubernetes pod works)",
    "overlay: VXLAN across Docker hosts (Swarm)",
    "macvlan or ipvlan: container on the physical network",
    "CNM: sandbox (the namespace config), endpoint (the attachment, typically a veth), network (a group of endpoints); local drivers bridge, host, none, macvlan, ipvlan; global driver overlay needs a key-value store",
    "default subnet 172.17.0.0/16 may overlap corporate or VPN ranges: set default-address-pools in /etc/docker/daemon.json",
    "docker network ls; docker network inspect bridge; iptables -t nat -S DOCKER; bridge fdb show br docker0",
    "Docker inserts its own rules ahead of the firewall's rules"
]

print("Ready to assemble SVG.")
