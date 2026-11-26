# Test multi-column flow
# Suppose we have 3 columns:
# Col 1 (Left): Bringup / Onboarding
# Start [*] -> Provisioned -> Configured -> Validating
# That's 3 states in Col 1, going top to bottom!
# Top: Start [*]
# Row 1: Provisioned
# Transition 1: "bare metal/VM created (image, BMC/PXE or cloud API)"
# Row 2: Configured
# Transition 2: "OS, kernel, drivers, runtime, kubelet (Ansible/image)"
# Row 3: Validating
# Transition 3: "join cluster tainted \"validating\""

# Then from Validating:
# Where does it go?
# Validating -> Ready: "health gates pass (GPU diag, NCCL, network, storage)"
# It goes from Col 1 to Col 2 (or Col 3)!

print("Testing Col 1 top-to-bottom bringup...")
