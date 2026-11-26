import pathlib, subprocess

svg = pathlib.Path("test_distribution.svg").read_text()
svg = svg.replace('d="M 710 430 C 760 430, 780 310, 830 310"', 'd="M 710 440 C 770 440, 770 310, 830 310"')
svg = svg.replace('d="M 710 570 C 760 570, 780 690, 830 690"', 'd="M 710 560 C 770 560, 770 690, 830 690"')

pathlib.Path("test_distribution.svg").write_text(svg)

chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
subprocess.run([
    chrome_path, '--headless=new', '--disable-gpu', '--hide-scrollbars',
    '--window-size=1600,900', f'--screenshot=/tmp/test_distribution2.png',
    f'file://{pathlib.Path("test_distribution.svg").resolve()}'
], capture_output=True, timeout=60)
print("Updated and re-rendered.")
