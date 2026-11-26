import re
import xml.etree.ElementTree as ET

# Define the exact 17 labels
expected_labels = [
    "How the three QoS classes are derived and what they change",
    "QoS is derived by the API server, never set by a field; check with kubectl get pod -o jsonpath={.status.qosClass}",
    "Guaranteed",
    "every container sets CPU and memory requests equal to limits",
    "oom_score_adj -997",
    "cgroup kubepods.slice/guaranteed",
    "evicted last; required for CPU Manager static policy exclusive cores and Topology Manager alignment",
    "Burstable",
    "some requests or limits set, but not Guaranteed rules",
    "oom_score_adj scaled between 2 and 999",
    "cgroup kubepods.slice/burstable",
    "BestEffort",
    "no requests or limits at all",
    "oom_score_adj 1000",
    "cgroup kubepods.slice/besteffort",
    "first to be killed or evicted under pressure",
    "GPU extended resources must be whole integers and requests equal limits (no overcommit); setting only limits defaults requests to the same value"
]

print(f"Total expected labels: {len(expected_labels)}")
assert len(expected_labels) == 17
