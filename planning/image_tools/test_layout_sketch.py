# Let us test an exact layout sketch
# Canvas: 1600 x 1180

# Margins: 40px everywhere
# Width: 1600
# Height: 1180

# Title: y=58, font-size=48 bold
# Subtitle / Header: y=105

# Two main panels:
# Left Panel: "hosts.ini" container (x=40, y=105, w=740, h=540)
# Right Panel: "Tree" container (x=820, y=105, w=740, h=540)

# Inside Left Panel (x=40..780, y=105..645):
# We have 4 file lines:
# Line 1: [gpu] gpu01 ansible_host=10.0.10.11, gpu02 ansible_host=10.0.10.12
# Line 2: [login] login01 ansible_host=10.0.10.5
# Line 3: [cluster:children] gpu login
# Line 4: [cluster:vars] ansible_user=automation, ansible_python_interpreter=/usr/bin/python3
# And Callouts 1 and 2:
# Callout 1: each host has a name and optionally an address
# Callout 2: a group collects hosts that share a role

# Let us see how they can be arranged inside or beside Left Panel.
print("Sketching...")
