import re

# Complete grid specification and validation script
grid = {
    "canvas": {"w": 1600, "h": 1200},
    "title": {"x": 800, "y": 56, "fs": 48},
    "left_col": {"x": 40, "w": 860},
    "gap": 40,
    "right_col": {"x": 940, "w": 620},
    
    # Layer 1: CLI
    "cli": {"y": 95, "h": 130},
    # Arrow 1: y=225 to y=275 (dy=50)
    
    # Layer 2: collect
    "collect": {"y": 275, "h": 140},
    # Arrow 2: y=415 to y=465 (dy=50)
    
    # Layer 3: parsers (pure)
    "parsers": {"y": 465, "h": 200},
    # Arrow 3: y=665 to y=715 (dy=50)
    
    # Layer 4: rules (pure)
    "rules": {"y": 715, "h": 140},
    
    # Right column items:
    # Exit codes table:
    "exit_codes": {"y": 95, "h": 220},
    # models.py:
    "models": {"y": 335, "h": 100},
    # Parser detail:
    "parser_detail": {"y": 465, "h": 260},
    # Rules detail:
    "rules_detail": {"y": 745, "h": 170},
    
    # Full width bottom items:
    # Test strip:
    "test_strip": {"x": 40, "y": 935, "w": 1520, "h": 130},
    # Bottom bar:
    "bottom_bar": {"x": 40, "y": 1095, "w": 1520, "h": 70}
}

print("Vertical breakdown:")
print(f"cli: y={grid['cli']['y']}..{grid['cli']['y']+grid['cli']['h']}")
print(f"arrow 1: y=225..275 (len=50)")
print(f"collect: y={grid['collect']['y']}..{grid['collect']['y']+grid['collect']['h']}")
print(f"arrow 2: y=415..465 (len=50)")
print(f"parsers: y={grid['parsers']['y']}..{grid['parsers']['y']+grid['parsers']['h']}")
print(f"arrow 3: y=665..715 (len=50)")
print(f"rules: y={grid['rules']['y']}..{grid['rules']['y']+grid['rules']['h']}")
print(f"test_strip: y={grid['test_strip']['y']}..{grid['test_strip']['y']+grid['test_strip']['h']}")
print(f"bottom_bar: y={grid['bottom_bar']['y']}..{grid['bottom_bar']['y']+grid['bottom_bar']['h']}")
print(f"margin bottom: {1200 - (grid['bottom_bar']['y']+grid['bottom_bar']['h'])}px")

