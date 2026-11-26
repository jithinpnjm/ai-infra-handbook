# Let's test the layout of the three items:
# 1. Docker rules
# 2. Firewall rule (beside it, skipped)
# 3. Container port 80
# Orange arrow: published port 8080 answers from anywhere

# Width of netfilter chains = 940 (x=40..980).
# Usable inner width = 940 - 40 = 900 (x=60..960).
# Height = 250 (y=290..540).

# Option 1:
# Header: netfilter chains (y=290..330)
# Inside:
# Left box: Docker rules (x=60..480, w=420)
# Right box: Firewall rule (x=540..960, w=420) [BESIDE IT, SKIPPED]
# But wait! Where is container port 80?
# If container port 80 is below netfilter chains?
# Or inside netfilter chains?
# Wait! If container port 80 is below netfilter chains, where is Fixes box?
# Left area height is 620px (y=160..780).
# Row 1 (Client & Host NIC): y=160..250 (90)
# Gap: 40px -> y=290
# Netfilter chains: y=290..540 (250)
# Gap: 40px -> y=580
# Fixes box: y=580..780 (200)
# Total height = 90 + 40 + 250 + 40 + 200 = 620px!
# Notice there is NO separate row for container port 80!
# Therefore, container port 80 MUST BE inside netfilter chains, OR inside Fixes, OR part of the flow!
# Where does container port 80 belong?
# It's the destination of the packet!
print("Let's see how container port 80 fits inside the flow!")
