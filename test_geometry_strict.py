import re

# Strict clearance tests
def check_line(label, text, font_size, is_mono, box_x, box_w, text_anchor, text_x):
    rate = 0.62 if is_mono else 0.6
    w = len(text) * font_size * rate
    if text_anchor == 'middle':
        left = text_x - w / 2
        right = text_x + w / 2
    elif text_anchor == 'start':
        left = text_x
        right = text_x + w
    else:
        left = text_x - w
        right = text_x
    
    pad_left = left - box_x
    pad_right = (box_x + box_w) - right
    print(f"[{label}] text='{text}' w={w:.1f}px: pad_left={pad_left:.1f}px, pad_right={pad_right:.1f}px")
    assert pad_left >= 16.0, f"[{label}] pad_left={pad_left:.1f} < 16px!"
    assert pad_right >= 16.0, f"[{label}] pad_right={pad_right:.1f} < 16px!"

print("--- TEXT PADDING CHECKS ---")
# Title: canvas 0 to 1600
check_line("Title 1", "The Ansible CI workflow: ", 48, False, 0, 1600, "middle", 800)
check_line("Title 2", "lint gates the Molecule matrix", 48, False, 0, 1600, "middle", 800)

# Container: 40 to 1560 (w=1520)
check_line("Container label", "ansible-ci workflow", 32, True, 40, 1520, "middle", 800)

# Job 1 (lint): sub-cards at x=90, w=340
check_line("Lint title", "lint", 32, False, 70, 380, "middle", 260)
check_line("Lint runs-on 1", "runs-on ", 24, True, 90, 340, "middle", 260)
check_line("Lint runs-on 2", "ubuntu-latest", 24, True, 90, 340, "middle", 260)
check_line("Lint step 1", "yamllint . && ", 24, True, 90, 340, "middle", 260)
check_line("Lint step 2", "ansible-lint", 24, True, 90, 340, "middle", 260)

# Arrow needs: lint (in gap between 450 and 610, w=160)
check_line("Arrow label 1", "needs: ", 24, True, 450, 160, "middle", 530)
check_line("Arrow label 2", "lint", 24, True, 450, 160, "middle", 530)

# Job 2 (molecule): sub-cards at x=630, w=340
check_line("Molecule title", "molecule", 32, False, 610, 380, "middle", 800)
check_line("Molecule role 1", "role: kernel_tuning, ", 24, True, 630, 340, "middle", 800)
check_line("Molecule role 2", "chrony_client, ", 24, True, 630, 340, "middle", 800)
check_line("Molecule role 3", "dcgm_exporter", 24, True, 630, 340, "middle", 800)
check_line("Molecule distro 1", "distro: ubuntu2204, ", 24, True, 630, 340, "middle", 800)
check_line("Molecule distro 2", "rockylinux9", 24, True, 630, 340, "middle", 800)
check_line("Molecule step", "molecule test", 24, True, 630, 340, "middle", 800)

# Note under molecule: x=610, w=380
check_line("Note mol 1", "a broken file never ", 24, False, 610, 380, "middle", 800)
check_line("Note mol 2", "starts a container", 24, False, 610, 380, "middle", 800)

# Job 3 (gpu-hw): sub-cards at x=1170, w=340
check_line("Gpu-hw title", "gpu-hw", 32, False, 1150, 380, "middle", 1340)
check_line("Gpu-hw runs-on 1", "runs-on ", 24, True, 1170, 340, "middle", 1340)
check_line("Gpu-hw runs-on 2", "self-hosted, gpu", 24, True, 1170, 340, "middle", 1340)
check_line("Gpu-hw step 1", "molecule test ", 24, True, 1170, 340, "middle", 1340)
check_line("Gpu-hw step 2", "-s gpu_hw", 24, True, 1170, 340, "middle", 1340)

# Note under gpu-hw: x=1150, w=380
check_line("Note gpu 1", "runs on schedule ", 24, False, 1150, 380, "middle", 1340)
check_line("Note gpu 2", "(nightly cron ", 24, False, 1150, 380, "middle", 1340)
check_line("Note gpu 3", "0 4 * * *) or ", 24, False, 1150, 380, "middle", 1340)
check_line("Note gpu 4", "when a pull request ", 24, False, 1150, 380, "middle", 1340)
check_line("Note gpu 5", "has the test-gpu label", 24, False, 1150, 380, "middle", 1340)

print("\nALL 27 TEXT LINES PASS THE >= 16PX PADDING REQUIREMENT!")
