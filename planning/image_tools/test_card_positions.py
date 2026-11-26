centers = {
    "U": 150.0,
    "A": 312.5,
    "S": 475.0,
    "K": 637.5,
    "R": 800.0,
    "C": 962.5,
    "V": 1125.0,
    "D": 1287.5,
    "X": 1450.0
}

# The 20 steps:
steps = [
    (1, "U", "A", "create Pod (admission, defaults, SA token, quota)"),
    (2, "A", "S", "watch: Pod with no nodeName"),
    (3, "S", "A", "bind Pod → node (spec.nodeName)"),
    (4, "A", "K", "watch: Pod bound to my node"),
    (5, "K", "K", "admit pod (resources, node-fit, kernel params), create pod dirs"),
    (6, "K", "D", "Allocate(GPU devices) → env/mounts/CDI names"),
    (7, "K", "V", "NodeStageVolume / NodePublishVolume (PVCs)"),
    (8, "K", "R", "RunPodSandbox"),
    (9, "R", "C", "ADD (netns, IP, routes)"),
    (10, "K", "R", "PullImage (per container)"),
    (11, "K", "R", "CreateContainer / StartContainer (init containers first)"),
    (12, "R", "X", "create namespaces, cgroups, mounts, exec"),
    (13, "K", "A", "status updates (PodScheduled, Initialized, ContainersReady, Ready)"),
    (0, "K", "X", "running: probes, log rotation, cgroup accounting, status heartbeats"), # Note
    (14, "U", "A", "delete Pod"),
    (15, "A", "K", "deletionTimestamp set (grace)"),
    (16, "K", "X", "preStop, SIGTERM, wait, SIGKILL"),
    (17, "K", "R", "StopContainer, StopPodSandbox → CNI DEL"),
    (18, "K", "V", "unmount volumes"),
    (19, "K", "A", "remove Pod object (grace 0)")
]

for i in range(len(steps)):
    num, src, dst, text = steps[i]
    print(f"Step {num}: {src} -> {dst} | len={len(text)} | \"{text[:30]}...\"")
