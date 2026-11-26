import xml.etree.ElementTree as ET

participants_row1 = [
    ("U", 148, "User /", "controller", "window"),
    ("S", 474, "Scheduler", "", "clock"),
    ("R", 800, "containerd", "(CRI)", "cube"),
    ("V", 1126, "CSI node", "plugin", "disk"),
    ("X", 1452, "runc /", "kernel", "chip"),
]

participants_row2 = [
    ("A", 311, "API server", "(+etcd)", "shield"),
    ("K", 637, "Kubelet", "", "gear"),
    ("C", 963, "CNI", "plugin", "cable"),
    ("D", 1289, "Device", "plugin", "gpu"),
]

print("Participants layout config valid.")
