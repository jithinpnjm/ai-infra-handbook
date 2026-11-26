import xml.etree.ElementTree as ET
import re
import pathlib

# Let's inspect the exact labels and rules
spec_labels = [
    "Leader election with Lease objects",
    "control-plane node 1",
    "node 2",
    "node 3",
    "active leader",
    "standby",
    "kube-scheduler",
    "kube-controller-manager",
    "Lease object in kube-system (coordination.k8s.io/v1)",
    "renews renewTime every 2 s (retryPeriod)",
    "leader crashes, no renewal within 15 s (leaseDuration)",
    "a standby acquires the Lease and takes over, failover about 15 s",
    "Three active schedulers would cause conflicting bindings and duplicate ReplicaSet creations; API servers stay active-active behind a load balancer",
    "kubectl get lease -n kube-system"
]

print("Total expected labels:", len(spec_labels))
for i, l in enumerate(spec_labels, 1):
    print(f"{i:2d}. '{l}'")
