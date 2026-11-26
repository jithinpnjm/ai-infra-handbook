import xml.etree.ElementTree as ET

# Let's inspect the cards:
# Card 1:
# Title: 'The counter does not exist'
# Looks: 'some resources expose only some of utilisation, saturation and errors'
# Counter: 'mark the empty cell as a known unknown and say so in the report; do not read an empty cell as healthy'

# Card 2:
# Title: 'The interval hides the problem'
# Looks: 'a one-minute average shows a device at 80% while one-second samples show bursts to 100% with queueing (Case 1)'
# Counter: 'shorten the interval before you move on'

# Card 3:
# Title: 'The measurement disturbs the system'
# Looks: 'profilers, tracers and heavy sampling use CPU and can turn a rare stall into a constant one on a GPU node'
# Counter: 'start with cheap counters; turn on heavy tools only for a short, announced window'

# Card 4:
# Title: 'The first explanation feels complete'
# Looks: 'you find a real fault, fix it, and stop, but it explains only a fraction of the slowdown'
# Counter: 'check the fix against the original problem statement; if step time did not return to baseline, the investigation is not finished'

print("Checking card texts...")
