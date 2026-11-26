import re
import xml.etree.ElementTree as ET

spec = """Two columns. Left column titled 'Service: built into core': a box 'Service' with a virtual IP icon labelled 'VIP' and an arrow to a kube-proxy box 'kube-proxy programs each host', then to two Pod boxes. A green note 'Works on a fresh cluster'. Right column titled 'Ingress: only a contract': a box 'Ingress object' with the note 'Creating it by itself does nothing', a dashed empty arrow with a question mark, then two alternative controller boxes: 'ingress-nginx: writes NGINX config for Pods' and 'Contour: programs Envoy'. Both controller boxes point at the same Pod boxes. An orange outline on the empty dashed arrow labelled 'No controller: the Ingress does nothing'. Bottom note: 'Many APIs take the plug-in route, such as Ingress and NetworkPolicy.'"""

title = "Service ships built in, Ingress needs a controller"

# Extract single quotes:
quotes = re.findall(r"'([^']+)'", spec)
print(f"Total quotes found: {len(quotes)}")
for i, q in enumerate(quotes, 1):
    print(f"  {i:2d}. {q}")

all_labels = [title] + quotes
print(f"\nTotal expected labels if title + quotes: {len(all_labels)}")
