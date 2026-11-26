import re

# We have 12 rows.
# Width of table = 1520 (x from 40 to 1560)
# Let's see the 3 columns:
# Col 1: Symptom (Error text)
# Col 2: Likely cause
# Col 3: First fix

# Col 1 max length is 54 chars: "attempted relative import with no known parent package"
# Col 2 max length is 63 chars: "wrong interpreter or venv, not installed, typo, wrong directory"
# Col 3 max length is 66 chars: "read the chain, relax pins, pip install -vv, separate environments"

# Let's test column widths:
# e.g., col1_w = 460, col2_w = 480, col3_w = 580 (total = 1520)
# Or col1_w = 470, col2_w = 470, col3_w = 580.
# At font-size 24:
# sans char width = 24 * 0.60 = 14.4 px.
# mono char width = 24 * 0.62 = 14.88 px.
# With 16px padding on left and right, available text width = col_w - 32.

col1_w = 460
col2_w = 480
col3_w = 580

print(f"Max chars per line (conservative):")
print(f"Col 1 (mono/sans): {(col1_w - 32) / 14.88:.1f} mono, {(col1_w - 32) / 14.4:.1f} sans")
print(f"Col 2 (sans):      {(col2_w - 32) / 14.4:.1f} sans")
print(f"Col 3 (mono/sans): {(col3_w - 32) / 14.88:.1f} mono, {(col3_w - 32) / 14.4:.1f} sans")

