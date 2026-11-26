import re
import xml.etree.ElementTree as ET

lifelines = {
    "U": 148,
    "A": 311,
    "S": 474,
    "K": 637,
    "R": 800,
    "C": 963,
    "V": 1126,
    "D": 1289,
    "X": 1452
}

steps_data = [
    # (step_num, sender, receiver, label, is_dashed, is_loop, is_note, is_orange)
    (1, "U", "A", "create Pod (admission, defaults, SA token, quota)", False, False, False, False),
    (2, "A", "S", "watch: Pod with no nodeName", True, False, False, False),
    (3, "S", "A", "bind Pod → node (spec.nodeName)", False, False, False, False),
    (4, "A", "K", "watch: Pod bound to my node", True, False, False, False),
    (5, "K", "K", "admit pod (resources, node-fit, kernel params), create pod dirs", False, True, False, False),
    (6, "K", "D", "Allocate(GPU devices) → env/mounts/CDI names", False, False, False, True),
    (7, "K", "V", "NodeStageVolume / NodePublishVolume (PVCs)", False, False, False, False),
    (8, "K", "R", "RunPodSandbox", False, False, False, False),
    (9, "R", "C", "ADD (netns, IP, routes)", False, False, False, False),
    (10, "K", "R", "PullImage (per container)", False, False, False, False),
    (11, "K", "R", "CreateContainer / StartContainer (init containers first)", False, False, False, False),
    (12, "R", "X", "create namespaces, cgroups, mounts, exec", False, False, False, False),
    (13, "K", "A", "status updates (PodScheduled, Initialized, ContainersReady, Ready)", False, False, False, False),
    (None, "K", "X", "running: probes, log rotation, cgroup accounting, status heartbeats", False, False, True, False),
    (14, "U", "A", "delete Pod", False, False, False, False),
    (15, "A", "K", "deletionTimestamp set (grace)", True, False, False, False),
    (16, "K", "X", "preStop, SIGTERM, wait, SIGKILL", False, False, False, False),
    (17, "K", "R", "StopContainer, StopPodSandbox → CNI DEL", False, False, False, False),
    (18, "K", "V", "unmount volumes", False, False, False, False),
    (19, "K", "A", "remove Pod object (grace 0)", False, False, False, False)
]

print("Steps data configured. Count:", len(steps_data))
