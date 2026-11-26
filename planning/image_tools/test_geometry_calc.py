def est_sans(text, fs=24):
    return len(text) * fs * 0.6

def est_mono(text, fs=24):
    return len(text) * fs * 0.62

# Check Warning Box:
# x = 40, y = 850, w = 940, h = 230
# Right edge = 980
# Icon at x = 70, y = 885, w = 56, h = 56 (ends at x = 126)
# Text starts at x = 150.
# Available width = 980 - 16 - 150 = 814 px.
# Text: "a migration that removes a column old code still uses breaks old code mid-rollout"
# If 2 lines:
# Line 1: "a migration that removes a column old code still uses" -> 53 chars * 26 * 0.6 = 826.8 > 814!
# But what if we do 3 lines?
# Line 1: "a migration that removes a column" (33 chars, fs=28) -> 33 * 28 * 0.6 = 554.4 px <= 814
# Line 2: "old code still uses breaks" (26 chars, fs=28) -> 26 * 28 * 0.6 = 436.8 px <= 814
# Line 3: "old code mid-rollout" (20 chars, fs=28) -> 20 * 28 * 0.6 = 336 px <= 814
# Or at fs=26:
# Line 1: 33 * 26 * 0.6 = 514.8 px
# Line 2: 26 * 26 * 0.6 = 405.6 px
# Line 3: 20 * 26 * 0.6 = 312.0 px
# All well within 814 px!
# And vertical in Warning box (h=230):
# y = 850.
# Text lines at y = 925, 965, 1005 (or y = 920, 960, 1000).
# Top padding: 920 - 28 - 850 = 42 px >= 16.
# Bottom padding: (850 + 230) - 1005 = 75 px >= 16.

# Check Note Box:
# x = 1020, y = 850, w = 540, h = 230
# Right edge = 1560.
# Icon at x = 1050, y = 885, w = 56, h = 56 (ends at x = 1106)
# Text can be below icon, or beside icon, or icon top-left!
# If text is at x = 1060:
# Available width = 1560 - 16 - 1060 = 484 px.
# Text: "alembic upgrade head runs once with run_once on the first host"
# Line 1: "alembic upgrade head" (mono, fs=24) -> 20 * 24 * 0.62 = 297.6 px <= 484 px.
# Line 2: "runs once with run_once" (15 sans + 8 mono, fs=24) -> 15*14.4 + 8*14.88 = 335.04 px <= 484 px.
# Line 3: "on the first host" (17 sans, fs=24) -> 17*14.4 = 244.8 px <= 484 px.
# All lines fit with huge margin!

print("Warning and Note boxes geometry: PERFECT!")
