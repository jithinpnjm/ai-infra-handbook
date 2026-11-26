import re
import xml.etree.ElementTree as ET

title = "Restarting eight replicas at once leaves a zero-capacity gap"
label1 = "70 billion parameters x 2 bytes = 140 GB; shared source 14 GB per second"
label2 = "all eight restart together: 8 x 140 / 14 = 80 s each under the equal-share model, endpoint has no capacity during that window; retries in the gap make the first minute after recovery worse"
label3 = "small groups, at least X+1 replicas keep serving; weights staged on local disk so the source stops being the shared bottleneck; one replica alone needs 10 s"
label4 = "measure the load time in the startup log and use that number in your answer; saying you will measure first is more credible than a number you cannot defend; the gap is the window to plan for, not the steady state"

print("All labels loaded.")
