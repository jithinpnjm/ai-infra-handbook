from playwright.sync_api import sync_playwright

def test_card(name, box_w, box_h, font_size, dy_list, is_mono=False, is_center=False):
    # dy_list is list of dy offsets relative to previous line (first is 0)
    num_lines = len(dy_list)
    html = f"""
    <svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
      <rect id="box" x="50" y="50" width="{box_w}" height="{box_h}" />
      <text id="txt" x="{50 + (box_w/2 if is_center else 24)}" y="{50 + 38}" 
            font-family="{'monospace' if is_mono else 'sans-serif'}" 
            font-size="{font_size}" {'text-anchor="middle"' if is_center else ''}>
    """
    for i, dy in enumerate(dy_list):
        x_val = 50 + (box_w/2 if is_center else 24)
        html += f'<tspan x="{x_val}" dy="{dy}">Line {i+1} testing padding</tspan>'
    html += """
      </text>
    </svg>
    """
    return html

print("Ready to optimize coordinates.")
