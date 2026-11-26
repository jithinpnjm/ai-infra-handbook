def est_sans(s, fs=24):
    return len(s) * 0.6 * fs

def est_mono(s, fs=24):
    return len(s) * 0.62 * fs

# Col width = 470
# Icon width = 56, icon margin = 20 -> available text width in col = 470 - 24 (left pad) - 56 (icon) - 16 (gap) - 24 (right pad) = 350 px.
# Or if icon is above text:
# Box width = 470. With 24px pad each side: available width = 422 px!

# Check Phase 1:
# "Phase 1 expand:" (fs=30): len=15 * 0.6 * 30 = 270 px < 422 px!
# "add the new piece in a way" (fs=24): len=25 * 0.6 * 24 = 360 px < 422 px!
# "old code ignores" (fs=24): len=16 * 0.6 * 24 = 230 px < 422 px!
print("Phase 1 line 1 (fs=30):", est_sans("Phase 1 expand:", 30))
print("Phase 1 line 2 (fs=24):", est_sans("add the new piece in a way", 24))
print("Phase 1 line 3 (fs=24):", est_sans("old code ignores", 24))

# Check Phase 2:
# "Phase 2 move the code over" (fs=30): len=26 * 0.6 * 30 = 468 px -> too wide for 422!
# Let's wrap Phase 2:
# Line 1: "Phase 2 move the" (fs=30): 16 * 18 = 288 px
# Line 2: "code over with serial rolling," (fs=24): 30 * 14.4 = 432 -> 30 chars is close to 422.
# Let's split better:
# Line 1: "Phase 2" (fs=30): len=7 * 18 = 126 px
# Line 2: "move the code over with" (fs=24): len=23 * 14.4 = 331 px
# Line 3: "serial rolling, old and new" (fs=24): len=27 * 14.4 = 388 px
# Line 4: "run side by side" (fs=24): len=16 * 14.4 = 230 px
print("Phase 2 split:")
print("  Line 1:", est_sans("Phase 2", 30))
print("  Line 2:", est_sans("move the code over with", 24))
print("  Line 3:", est_sans("serial rolling, old and new", 24))
print("  Line 4:", est_sans("run side by side", 24))

# Check Phase 3:
# Line 1: "Phase 3 contract:" (fs=30): 17 * 18 = 306 px < 422
# Line 2: "later remove the old piece" (fs=24): 26 * 14.4 = 374 px < 422
print("Phase 3 split:")
print("  Line 1:", est_sans("Phase 3 contract:", 30))
print("  Line 2:", est_sans("later remove the old piece", 24))

# Check warning box (w = 940 px):
# "a migration that removes a column old code still uses breaks old code mid-rollout"
# Line 1: "a migration that removes a column" (fs=24): 33 * 14.4 = 475 px < 800 px
# Line 2: "old code still uses breaks old code mid-rollout" (fs=24): 47 * 14.4 = 676 px < 800 px
print("Warning box:")
print("  Line 1:", est_sans("a migration that removes a column", 24))
print("  Line 2:", est_sans("old code still uses breaks old code mid-rollout", 24))

# Check note box (w = 510 px):
# "alembic upgrade head runs once with run_once on the first host"
# Line 1: "alembic upgrade head runs once with" (35 chars): 35 * 14.4 = 504 -> let's wrap onto 2 lines!
# Line 1: "alembic upgrade head runs once" (30 chars) -> monospace alembic upgrade head: 20 * 0.62 * 24 = 297 + 10 * 0.6 * 24 = 144 = 441 px
# Line 2: "with run_once on the first host" (31 chars) -> 31 * 15 = 465 px
# Or 3 lines:
# Line 1: "alembic upgrade head" (mono): 20 * 0.62 * 24 = 297.6 px
# Line 2: "runs once with run_once" (mono on run_once): 15 * 14.4 + 8 * 14.88 = 335 px
# Line 3: "on the first host": 17 * 14.4 = 244.8 px
print("Note box 3 lines:")
print("  Line 1:", est_mono("alembic upgrade head", 24))
print("  Line 2:", est_sans("runs once with ", 24) + est_mono("run_once", 24))
print("  Line 3:", est_sans("on the first host", 24))
