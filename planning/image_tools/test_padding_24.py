# Check text_width <= col_w - 40 for left padding 24 and right padding >= 16
col1_w = 470
col2_w = 470
col3_w = 580

# Col 1: error names. Let's see if monospace or sans-serif.
# "Fonts: sans-serif for labels, monospace for commands and file names."
# Col 1 has error messages like ModuleNotFoundError, ImportError, etc.
# Some are python exception classes, some are phrases.
# If monospace 24px: factor = 0.62.
# Let's check max width of Col 1 lines:
