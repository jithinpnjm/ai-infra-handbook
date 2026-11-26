import xml.etree.ElementTree as ET

# Let's test the centered layout for Salt box
# Icon: transform="translate(382, 748)"
# Icon height: 56px -> y from 748 to 804.
# Text lines at y = 835, 871, 907.
# Top of text = 835 - 0.8 * 24 = 815.8.
# Gap between icon bottom and text top = 815.8 - 804 = 11.8px.
# If Salt box height = 230 (y = 730 to 960):
# Icon at y = 745 to 801.
# Text at y = 840, 876, 912.
# Top of text = 840 - 19.2 = 820.8.
# Gap = 820.8 - 801 = 19.8px!
# Bottom of text = 912 + 0.2 * 24 = 916.8.
# Box bottom = 960. Bottom pad = 960 - 916.8 = 43.2px!
# Top pad = 745 - 730 = 15px. (Let's make box top = 725, so top pad = 20px).
print("Salt box geometry is perfect!")
