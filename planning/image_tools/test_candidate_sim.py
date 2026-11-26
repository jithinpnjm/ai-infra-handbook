import re

# Let's inspect the text of all 4 cards
t1 = 'Collect as you go: incident log with UTC timeline, observations, commands run, changes made, who did what; exact error strings; kubectl get -o yaml snapshots, describe output, pod logs including --previous, node journals, dmesg, pcaps, metric screenshots with time ranges, nvidia-bug-report, Hubble flows, audit log excerpts; for support kubectl cluster-info dump, sosreport, vendor bundles'
t2 = 'Communicate: status updates at fixed intervals, state the impact clearly, give an ETA only when you have a basis for it'
t3 = 'Blameless review: timeline, contributing factors (not one single root cause), detection gaps, how well the mitigation worked, action items with owners for automation, alerts, guardrails, docs and tests; turn recurring manual diagnosis into automated checks'
t4 = 'game day: planned drill with a fault the team has not seen; measure time-to-detect and time-to-recover; tools tc netem, Chaos Mesh NetworkChaos, kill pods and nodes, fill disks, stop kubelet, break CNI'

print("Text 1:", len(t1))
print("Text 2:", len(t2))
print("Text 3:", len(t3))
print("Text 4:", len(t4))
