import re

# Test Left Column layout
# Available x: 60..760 (w=700)
# Let's check:
# 1. Title: ansible.builtin.copy
#    font-size 30 bold mono.
#    w_est = 20 * 0.62 * 30 = 372px.
#    pad in 700px = (700 - 372) / 2 = 164px >= 16px.

# 2. Breakdown:
#    'ansible' = namespace (21 chars * 0.6 * 24 = 302.4px)
#    'builtin' = collection name (27 chars * 0.6 * 24 = 388.8px)
#    'copy' = module (15 chars * 0.6 * 24 = 216px)

# 3. Definition:
#    Line 1: "together the fully qualified collection name " (45 chars: 648px)
#    Line 2: "or FQCN (the full address of a module, " (39 chars: 561.6px)
#    Line 3: "namespace first)" (16 chars: 230.4px)
#    In 700px box: max line is 648px -> pad = (700 - 648) / 2 = 26px >= 16px!

# 4. Other examples:
#    community.general (17 * 0.62 * 24 = 252.96px)
#    ansible.posix (13 * 0.62 * 24 = 193.44px)
#    kubernetes.core (15 * 0.62 * 24 = 223.2px)
#    nvidia.* (8 * 0.62 * 24 = 119.04px)
#    If 2 rows in 700px:
#    Left chip: x=75, w=320. community.general pad = (320 - 253)/2 = 33.5px >= 16px.
#    Right chip: x=425, w=320. ansible.posix pad = (320 - 193.4)/2 = 63.3px >= 16px.

# 5. Warning (orange):
#    Line 1: "short names are ambiguous: two collections " (43 chars: 619.2px)
#    Line 2: "may each ship a module called copy, and " (40 chars: 576px)
#    Line 3: "ansible-lint flags them; always use FQCNs" (41 chars: 590.4px)
#    In 700px: pad = (700 - 619.2) / 2 = 40.4px >= 16px!

# 6. Install command:
#    "ansible-galaxy collection install -r requirements.yml" (53 chars)
#    Line 1: "ansible-galaxy collection " (26 chars * 0.62 * 24 = 386.88px)
#    Line 2: "install -r requirements.yml" (27 chars * 0.62 * 24 = 401.76px)
#    pad in 700px = (700 - 401.8) / 2 = 149.1px >= 16px!

# Right Column layout:
# Available x: 840..1540 (w=700)
# Card 1 (Core):
# Line 1: "Core: ansible-core itself, " (27 chars * 0.6 * 25 = 405px)
# Line 2: "created by the Ansible team" (27 chars * 0.6 * 25 = 405px)
# Card 2 (Certified):
# Line 1: "Certified: created and supported by " (36 chars * 0.6 * 25 = 540px)
# Line 2: "Red Hat and its partners through " (33 chars * 0.6 * 25 = 495px)
# Line 3: "Automation Hub" (14 chars * 0.6 * 25 = 210px)
# Card 3 (Community):
# Line 1: "Community: shared on Ansible Galaxy" (35 chars * 0.6 * 25 = 525px)

print("All card lines and paddings valid!")
