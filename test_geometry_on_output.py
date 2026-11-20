# Check text bounding boxes vs container/box boundaries
lines_to_check = [
    # (label, text, size, is_mono, box_x, box_w, anchor, text_x)
    ("Title 1", "The Ansible CI workflow: ", 48, False, 0, 1600, "middle", 800),
    ("Title 2", "lint gates the Molecule matrix", 48, False, 0, 1600, "middle", 800),
    ("Workflow container", "ansible-ci workflow", 32, True, 40, 1520, "middle", 800),

    ("Lint title", "lint", 32, False, 70, 380, "middle", 260),
    ("Lint runs-on 1", "runs-on ", 24, True, 90, 340, "middle", 260),
    ("Lint runs-on 2", "ubuntu-latest", 24, True, 90, 340, "middle", 260),
    ("Lint step 1", "yamllint . && ", 24, True, 90, 340, "middle", 260),
    ("Lint step 2", "ansible-lint", 24, True, 90, 340, "middle", 260),

    ("Needs lint 1", "needs: ", 24, True, 450, 160, "middle", 530),
    ("Needs lint 2", "lint", 24, True, 450, 160, "middle", 530),

    ("Mol title", "molecule", 32, False, 610, 380, "middle", 800),
    ("Mol role 1", "role: ", 24, True, 630, 340, "middle", 800),
    ("Mol role 2", "kernel_tuning, ", 24, True, 630, 340, "middle", 800),
    ("Mol role 3", "chrony_client, ", 24, True, 630, 340, "middle", 800),
    ("Mol role 4", "dcgm_exporter", 24, True, 630, 340, "middle", 800),
    ("Mol distro 1", "distro: ", 24, True, 630, 340, "middle", 800),
    ("Mol distro 2", "ubuntu2204, ", 24, True, 630, 340, "middle", 800),
    ("Mol distro 3", "rockylinux9", 24, True, 630, 340, "middle", 800),
    ("Mol step", "molecule test", 24, True, 630, 340, "middle", 800),

    ("Note mol 1", "a broken file never ", 24, False, 610, 380, "middle", 800),
    ("Note mol 2", "starts a container", 24, False, 610, 380, "middle", 800),

    ("Gpu title", "gpu-hw", 32, False, 1150, 380, "middle", 1340),
    ("Gpu runs-on 1", "runs-on ", 24, True, 1170, 340, "middle", 1340),
    ("Gpu runs-on 2", "self-hosted, gpu", 24, True, 1170, 340, "middle", 1340),
    ("Gpu step 1", "molecule test ", 24, True, 1170, 340, "middle", 1340),
    ("Gpu step 2", "-s gpu_hw", 24, True, 1170, 340, "middle", 1340),

    ("Note gpu 1", "runs on schedule ", 24, False, 1150, 380, "middle", 1340),
    ("Note gpu 2", "(nightly cron ", 24, False, 1150, 380, "middle", 1340),
    ("Note gpu 3", "0 4 * * *) or ", 24, False, 1150, 380, "middle", 1340),
    ("Note gpu 4", "when a pull request ", 24, False, 1150, 380, "middle", 1340),
    ("Note gpu 5", "has the test-gpu label", 24, False, 1150, 380, "middle", 1340),
]

all_ok = True
for name, text, sz, mono, bx, bw, anc, tx in lines_to_check:
    rate = 0.62 if mono else 0.6
    w = len(text) * sz * rate
    l = tx - w/2
    r = tx + w/2
    pl = l - bx
    pr = (bx + bw) - r
    ok = (pl >= 16.0) and (pr >= 16.0)
    if not ok:
        all_ok = False
        print(f"FAILED: {name} pl={pl:.1f} pr={pr:.1f}")
    else:
        print(f"PASS: {name} (w={w:.1f}px, pl={pl:.1f}px, pr={pr:.1f}px)")

assert all_ok, "Some lines failed strict clearance!"
print("\nALL LINES SATISFY >= 16px STRICT CLEARANCE!")
