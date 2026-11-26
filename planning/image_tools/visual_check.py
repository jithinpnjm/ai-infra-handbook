import subprocess
from PIL import Image
import xml.etree.ElementTree as ET

subprocess.run([
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--window-size=1600,1180",
    "--screenshot=/tmp/visual_check.png",
    "test_full_candidate.svg"
], capture_output=True)

print("Saved /tmp/visual_check.png")

# Now let us check if any text overflows its bounding box
# We can check text positions and box coordinates
tree = ET.parse("test_full_candidate.svg")
root = tree.getroot()

boxes = [
    # (name, x, y, w, h)
    ("Client", 50, 150, 120, 560),
    ("SYN queue", 300, 150, 750, 130),
    ("Callout 2", 300, 310, 750, 210),
    ("Accept queue", 300, 550, 440, 160),
    ("App accept loop", 800, 550, 250, 160),
    ("Callout 1", 300, 740, 750, 280),
    ("Fix 1", 1100, 150, 450, 150),
    ("Fix 2", 1100, 330, 450, 150),
    ("Fix 3", 1100, 510, 450, 150),
    ("Fix 4", 1100, 690, 450, 150),
    ("Fix 5", 1100, 870, 450, 150),
    ("Bottom bar", 50, 1080, 1500, 60),
]

for name, bx, by, bw, bh in boxes:
    print(f"Box {name:16s}: x=[{bx}, {bx+bw}], y=[{by}, {by+bh}]")

print("\nVisual check inspection completed.")
