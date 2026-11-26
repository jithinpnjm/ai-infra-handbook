import re

with open("test_generated.svg") as f:
    content = f.read()

# Replace cmd-external-api text with 4 tspans:
old_cmd_ext = '<tspan x="1080" dy="0">kubectl get --raw </tspan><tspan x="1080" dy="33">/apis/external.metrics.k8s.io/</tspan><tspan x="1080" dy="33">v1beta1/namespaces/serving/kafka_lag</tspan>'
new_cmd_ext = '<tspan x="1075" dy="0">kubectl get --raw </tspan><tspan x="1075" dy="33">/apis/external.metrics.k8s.io/</tspan><tspan x="1075" dy="33">v1beta1/namespaces/serving/</tspan><tspan x="1075" dy="33">kafka_lag</tspan>'

content = content.replace(old_cmd_ext, new_cmd_ext)

# Also adjust rect width of Column 3 to 500 (x=1050 to 1550)
content = content.replace('rect x="1060" y="970" width="480" height="115"', 'rect x="1050" y="960" width="500" height="135"')
content = content.replace('rect x="1060" y="840" width="480" height="120"', 'rect x="1050" y="840" width="500" height="110"')
content = content.replace('text x="1085" y="938"', 'text x="1075" y="925"')
content = content.replace('translate(1085, 855)', 'translate(1075, 850)')
content = content.replace('line x1="1030" y1="890" x2="1060" y2="890"', 'line x1="1030" y1="890" x2="1050" y2="890"')

with open("test_generated.svg", "w") as f:
    f.write(content)

print("Updated test_generated.svg.")
