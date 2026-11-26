import re

# Exact labels from content
labels = [
    "Timeline overview",
    "User / controller",
    "API server (+etcd)",
    "Scheduler",
    "Kubelet",
    "containerd (CRI)",
    "CNI plugin",
    "CSI node plugin",
    "Device plugin",
    "runc / kernel",
    "create Pod (admission, defaults, SA token, quota)",
    "watch: Pod with no nodeName",
    "bind Pod → node (spec.nodeName)",
    "watch: Pod bound to my node",
    "admit pod (resources, node-fit, kernel params), create pod dirs",
    "Allocate(GPU devices) → env/mounts/CDI names",
    "NodeStageVolume / NodePublishVolume (PVCs)",
    "RunPodSandbox",
    "ADD (netns, IP, routes)",
    "PullImage (per container)",
    "CreateContainer / StartContainer (init containers first)",
    "create namespaces, cgroups, mounts, exec",
    "status updates (PodScheduled, Initialized, ContainersReady, Ready)",
    "running: probes, log rotation, cgroup accounting, status heartbeats",
    "delete Pod",
    "deletionTimestamp set (grace)",
    "preStop, SIGTERM, wait, SIGKILL",
    "StopContainer, StopPodSandbox → CNI DEL",
    "unmount volumes",
    "remove Pod object (grace 0)"
]

print(f"Total source labels: {len(labels)}")
