with open("candidate_adapter_pipeline.svg") as f:
    s = f.read()

# 1. node-hpa
s = s.replace('rect x="1050" y="380" width="500" height="135"', 'rect x="1050" y="380" width="500" height="145"')
s = s.replace('rect x="1050" y="525" width="500" height="95"', 'rect x="1050" y="535" width="500" height="85"')
s = s.replace('text x="1070" y="567"', 'text x="1070" y="575"')
s = s.replace('dy="30">vllm -n serving', 'dy="28">vllm -n serving')

# 2. cmd-external-api
s = s.replace('rect x="1050" y="985" width="500" height="125"', 'rect x="1050" y="985" width="500" height="130"')
s = s.replace('text x="1070" y="1024"', 'text x="1070" y="1027"')
s = s.replace('dy="25">/apis/external.metrics.k8s.io/', 'dy="24">/apis/external.metrics.k8s.io/')
s = s.replace('dy="25">v1beta1/namespaces/serving/', 'dy="24">v1beta1/namespaces/serving/')
s = s.replace('dy="25">kafka_lag', 'dy="24">kafka_lag')

# 3. box-note
s = s.replace('rect x="40" y="1120" width="1510" height="65"', 'rect x="40" y="1125" width="1510" height="65"')
s = s.replace('text x="795" y="1161"', 'text x="795" y="1165"')

with open("candidate_adapter_pipeline.svg", "w") as f:
    f.write(s)

print("Updated candidate_adapter_pipeline.svg.")
