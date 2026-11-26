import re
import xml.etree.ElementTree as ET

# Canvas: 1600 x 1200
# Layout:
# Margin: 40 px everywhere
# Title: 48 px bold at (40, 75) and (40, 130)
# Table: x = 40, y = 165, w = 1170, h = 885
# Right strip (NCCL hierarchy): x = 1230, y = 165, w = 330, h = 885
# Bottom bar: x = 40, y = 1075, w = 1520, h = 85

# Table columns:
# Col 0 (Fabric): width = 270 (x = 40 to 310)
# Col 1 (L1/L2): width = 260 (x = 310 to 570)
# Col 2 (L3): width = 250 (x = 570 to 820)
# Col 3 (L4 and transport): width = 390 (x = 820 to 1210)

# Table rows:
# Header: y = 165, h = 55 (y: 165 to 220)
# Row 1 (Ethernet with TCP): y = 220, h = 165 (y: 220 to 385)
# Row 2 (RoCE v2): y = 385, h = 160 (y: 385 to 545)
# Row 3 (InfiniBand): y = 545, h = 185 (y: 545 to 730)
# Row 4 (NVLink / NVSwitch): y = 730, h = 160 (y: 730 to 890)
# Row 5 (PCIe): y = 890, h = 160 (y: 890 to 1050)
# Table h = 1050 - 165 = 885 px. Exactly matches!

print("Vertical coordinates computed.")
