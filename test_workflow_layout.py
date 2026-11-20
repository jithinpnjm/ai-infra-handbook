import re

def text_width(text, size=24, is_mono=False):
    rate = 0.62 if is_mono else 0.6
    return len(text) * size * rate

# Box width = 380. Available text width with 20px padding on each side = 340px.
avail_w = 340

print("Testing Box 1 (lint):")
print("runs-on ubuntu-latest:", text_width("runs-on ubuntu-latest", 24, True))
# 312.48 < 340! Fits on 1 line!
print("yamllint . && ansible-lint:", text_width("yamllint . && ansible-lint", 24, True))
# 386.88 > 340! Needs wrapping:
l1 = "yamllint . && "
l2 = "ansible-lint"
print("  wrap line 1:", text_width(l1, 24, True), "line 2:", text_width(l2, 24, True))

print("\nTesting Box 2 (molecule):")
# role: kernel_tuning, chrony_client, dcgm_exporter
role_full = "role: kernel_tuning, chrony_client, dcgm_exporter"
print("role full:", text_width(role_full, 24, True))
# Wrap role into 3 lines:
r1 = "role: kernel_tuning, "
r2 = "chrony_client, "
r3 = "dcgm_exporter"
print("  r1:", text_width(r1, 24, True))
print("  r2:", text_width(r2, 24, True))
print("  r3:", text_width(r3, 24, True))

# distro: ubuntu2204, rockylinux9
distro_full = "distro: ubuntu2204, rockylinux9"
print("distro full:", text_width(distro_full, 24, True))
d1 = "distro: ubuntu2204, "
d2 = "rockylinux9"
print("  d1:", text_width(d1, 24, True))
print("  d2:", text_width(d2, 24, True))

print("molecule test:", text_width("molecule test", 24, True))

print("\nTesting Box 3 (gpu-hw):")
print("runs-on self-hosted, gpu:", text_width("runs-on self-hosted, gpu", 24, True))
g1 = "runs-on "
g2 = "self-hosted, gpu"
print("  g1:", text_width(g1, 24, True))
print("  g2:", text_width(g2, 24, True))

print("molecule test -s gpu_hw:", text_width("molecule test -s gpu_hw", 24, True))
m1 = "molecule test "
m2 = "-s gpu_hw"
print("  m1:", text_width(m1, 24, True))
print("  m2:", text_width(m2, 24, True))

print("\nTesting Note under molecule:")
note_mol = "a broken file never starts a container"
print("note_mol full:", text_width(note_mol, 24, False))
nm1 = "a broken file never "
nm2 = "starts a container"
print("  nm1:", text_width(nm1, 24, False))
print("  nm2:", text_width(nm2, 24, False))

print("\nTesting Note under gpu-hw:")
note_gpu = "runs on schedule (nightly cron 0 4 * * *) or when a pull request has the test-gpu label"
print("note_gpu full:", text_width(note_gpu, 24, False))
ng1 = "runs on schedule "
ng2 = "(nightly cron 0 4 * * *) "
ng3 = "or when a pull request "
ng4 = "has the test-gpu label"
print("  ng1:", text_width(ng1, 24, False))
print("  ng2:", text_width(ng2, 24, False))
print("  ng3:", text_width(ng3, 24, False))
print("  ng4:", text_width(ng4, 24, False))

print("\nTesting Arrow label needs: lint:")
arrow_lbl = "needs: lint"
print("arrow label full:", text_width(arrow_lbl, 24, True))
al1 = "needs: "
al2 = "lint"
print("  al1:", text_width(al1, 24, True))
print("  al2:", text_width(al2, 24, True))
