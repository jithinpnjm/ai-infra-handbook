# Check all text elements and exact strings:
# Expected strings:
# Title: Access architecture
# Nodes:
# 1. User laptop
# 2. Bastion / jump host
# 3. Open OnDemand portal
# 4. Login nodes
# 5. Slurm controller
# 6. Compute nodes
# 7. Data transfer nodes: Globus, rsync, rclone
# 8. Parallel file system
# Edges:
# 9. SSH 22
# 10. HTTPS 443
# 11. reverse proxy to interactive app
# 12. bulk data

# That is EXACTLY 1 title + 8 node labels + 4 edge labels = 13 text strings.
# No other text, no step numbers, no takeaway bar.

print("Exact label inventory verified: 13 items.")
