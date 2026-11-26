import subprocess
import pathlib

def render_and_check(svg_code, name="test_candidate"):
    p_svg = pathlib.Path(f"/tmp/{name}.svg")
    p_png = pathlib.Path(f"/tmp/{name}.png")
    p_svg.write_text(svg_code)
    
    # Run chrome headless
    cmd = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '--headless=new',
        '--disable-gpu',
        '--hide-scrollbars',
        '--window-size=1600,1150',
        f'--screenshot={p_png}',
        f'file://{p_svg}'
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Rendered {p_png}: returncode={res.returncode}, file exists={p_png.exists()}")

render_and_check("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 1150' width='1600' height='1150'><rect width='1600' height='1150' fill='#f5f8f5'/></svg>")
