import subprocess, os

chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
svg_path = os.path.abspath("test_timeline.svg")
png_path = os.path.abspath("test_timeline.png")

# Use Chrome to take a screenshot
cmd = [
    chrome_bin,
    "--headless",
    "--disable-gpu",
    "--window-size=1600,1200",
    f"--screenshot={png_path}",
    f"file://{svg_path}"
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("Render returncode:", res.returncode)
if os.path.exists(png_path):
    print("PNG generated! Size:", os.path.getsize(png_path))
else:
    print("Error:", res.stderr)
