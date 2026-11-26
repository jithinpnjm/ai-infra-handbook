import re

# Let's inspect the layout and lines:

labels = {
    "title": "Why a published Docker port ignores your firewall rule",
    "client": "Client on the office network or anywhere",
    "host_nic": "Host NIC",
    "netfilter": "netfilter chains",
    "docker_rules": "Docker's own NAT and FORWARD rules (DOCKER chain) are inserted ahead of the rules managed by ufw or firewalld",
    "container_port": "container port 80",
    "orange_arrow_label": "published port 8080 answers from anywhere",
    "firewall_skipped": "ufw or firewalld rule that should block the port",
    "fix_1": "restrict a port with the DOCKER-USER chain",
    "fix_2": "bind the port to a specific address (for example 127.0.0.1:8080:80)",
    "fix_3": "if a published port must stay private on a shared host, restrict it in DOCKER-USER before you publish it",
    "right_title": "Docker network modes",
    "mode_bridge": "bridge: private subnet, veth per container, NAT outbound, -p publishes via DNAT; user-defined bridges add DNS-based name resolution and isolation",
    "mode_host": "host: shares the host namespace, no isolation, no NAT, best performance, ports conflict with host: NCCL or HPC containers",
    "mode_none": "none: only loopback",
    "mode_container": "container:NAME: shares another container's namespace (how a Kubernetes pod works)",
    "mode_overlay": "overlay: VXLAN across Docker hosts (Swarm)",
    "mode_macvlan": "macvlan or ipvlan: container on the physical network",
    "cnm": "CNM: sandbox (the namespace config), endpoint (the attachment, typically a veth), network (a group of endpoints); local drivers bridge, host, none, macvlan, ipvlan; global driver overlay needs a key-value store",
    "subnet": "default subnet 172.17.0.0/16 may overlap corporate or VPN ranges: set default-address-pools in /etc/docker/daemon.json",
    "commands": "docker network ls; docker network inspect bridge; iptables -t nat -S DOCKER; bridge fdb show br docker0",
    "takeaway": "Docker inserts its own rules ahead of the firewall's rules"
}

print(f"Total labels defined: {len(labels)}")
