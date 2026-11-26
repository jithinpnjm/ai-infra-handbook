#!/usr/bin/env python3
import re

# Expected labels
expected_labels = [
    "Three layers that limit database access",
    "app host",
    "unlisted host",
    "ufw allow tcp 5432 from each app host",
    "limits the port at the firewall",
    "listen_addresses = localhost plus ansible_host",
    "limits the network interface",
    "pg_hba.conf host db_name db_user app host /32 scram-sha-256",
    "limits the client address",
    "PostgreSQL on db01",
    "passes all three",
    "stopped"
]

print("Total expected labels:", len(expected_labels))
for i, l in enumerate(expected_labels, 1):
    print(f" {i:2d}. '{l}'")
