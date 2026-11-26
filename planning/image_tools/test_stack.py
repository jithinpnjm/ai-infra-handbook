# Let's test the width of each box and text
font_size = 24
def sans_w(text, size=24):
    return len(text) * 0.6 * size

def mono_w(text, size=24):
    return len(text) * 0.62 * size

layer1 = "cli_args"
layer2 = "os.environ (MYOPS_ prefixed, lowercased)"
layer3 = "file_cfg (/etc/myops.json)"
layer4 = "defaults {retries: 3, timeout: 30}"
lookup = 'cfg["timeout"]'
wins = 'first mapping wins'

print(f"Layer 1 mono width: {mono_w(layer1):.1f}")
print(f"Layer 2 mono width: {mono_w(layer2):.1f}")
print(f"Layer 3 mono width: {mono_w(layer3):.1f}")
print(f"Layer 4 mono width: {mono_w(layer4):.1f}")
print(f"Lookup mono width: {mono_w(lookup):.1f}")
print(f"Wins sans width: {sans_w(wins):.1f}")
