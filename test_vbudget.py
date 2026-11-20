# Layout Option 1:
# Host container contains everything.
# y=0..90: Title
# y=95..1170: Host container (H=1075)
#   Inside Host:
#   y=115: Host title & icon (h=45)
#   y=175: Callout banner (h=70)
#   y=265: Two columns:
#     Left: 'red' namespace box (h=470)
#     Right: 'default' namespace box (h=470)
#       Inside each namespace box:
#         Header: icon + name (h=50)
#         7 items stacked: 7 * 50 = 350 + gaps 6 * 8 = 48 -> 398px
#         Total = 50 + 398 + padding = 470px
#     y=755: Below the namespace boxes:
#       Left side: Commands panel under 'red' (h=380)
#         Header: icon + monospace commands
#         Step 1: 'ip netns add red'
#         Step 2: 'ip netns exec red ip link'
#                 '(only a down loopback at first)'
#         Step 3: 'ip -n red link set lo up'
#       Right side: Orange note under 'default' (h=380)
#         Orange card with icon:
#         'nsenter -t <pid> -n ip addr enters a container namespace by PID'
# Total height = 1200.

print("Option 1 height fits in 1200!")
