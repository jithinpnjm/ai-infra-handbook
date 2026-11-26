import re

# Canvas: width=1600, height=1200
# Margins: left=40, right=40, top=100, bottom=30
# Col 1: x = 40, w = 440 (ends at 480)
# Gap 1: 480 to 520 (w = 40)
# Col 2: x = 520, w = 500 (ends at 1020)
# Gap 2: 1020 to 1060 (w = 40)
# Col 3: x = 1060, w = 500 (ends at 1560)

# Let's inspect the vertical contents of each column:

# ==================== COLUMN 1 ====================
# Box 1: vLLM pod exposes vllm:num_requests_waiting
# Lines:
# 'vLLM pod exposes' (230px)
# 'vllm:num_requests_waiting' (360px)
# Box dimensions: x=40, y=110, w=440, h=150

# Box 6: kafka_consumergroup_lag topic embed
# Lines:
# 'kafka_consumergroup_lag' (331px)
# 'topic embed' (158px)
# Box dimensions: x=40, y=860, w=440, h=140

# ==================== COLUMN 2 ====================
# Box 2: Prometheus scrapes it
# Lines:
# 'Prometheus scrapes it' (302px)
# Box dimensions: x=520, y=110, w=500, h=90

# Arrow 2: (x=770, y=200) -> (x=770, y=240) [down arrow, len=40]

# Box 3: prometheus-adapter rule: seriesQuery vllm:num_requests_waiting with namespace and pod labels; resources overrides map namespace and pod; name as vllm_requests_waiting; metricsQuery sum by group
# Lines (fs=24):
# 1. 'prometheus-adapter rule:' (345.6px)
# 2. 'seriesQuery' (158.4px)
# 3. 'vllm:num_requests_waiting' (360.0px)
# 4. 'with namespace and pod labels;' (432.0px)
# 5. 'resources overrides map' (331.2px)
# 6. 'namespace and pod;' (259.2px)
# 7. 'name as vllm_requests_waiting;' (432.0px)
# 8. 'metricsQuery sum by group' (360.0px)
# 8 lines * 34px = 272px + 50px padding = 330px height.
# Box dimensions: x=520, y=240, w=500, h=330 (ends at y=570)

# Box 7: rule name kafka_lag
# Lines:
# 'rule name kafka_lag' (273.6px)
# Box dimensions: x=520, y=860, w=500, h=90

# ==================== COLUMN 3 ====================
# Box 4: custom.metrics.k8s.io API
# Lines:
# 'custom.metrics.k8s.io API' (360px)
# Box dimensions: x=1060, y=240, w=500, h=85

# Box 9: cmd_custom
# 'kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/serving/pods/*/vllm_requests_waiting'
# Lines (fs=24 mono):
# 1. 'kubectl get --raw' (253px)
# 2. '/apis/custom.metrics.k8s.io/' (416.6px)
# 3. 'v1beta1/namespaces/serving/' (401.8px)
# 4. 'pods/*/vllm_requests_waiting' (416.6px)
# 4 lines * 32px = 128px + 30px = 160px height.
# Box dimensions: x=1060, y=335, w=500, h=160 (ends at y=495)

# Arrow 4: from custom API to HPA
# Box 5: HPA reads it and decides
# Lines:
# 'HPA reads it and decides' (345.6px)
# Box dimensions: x=1060, y=525, w=500, h=85

# Box 11: cmd_hpa
# 'kubectl describe hpa vllm -n serving'
# Lines (fs=24 mono):
# 1. 'kubectl describe hpa' (297.6px)
# 2. 'vllm -n serving' (223.2px)
# 2 lines * 32px = 64px + 30px = 95px height.
# Box dimensions: x=1060, y=620, w=500, h=95 (ends at y=715)

# Conditions box:
# 'AbleToScale: can the HPA change the count at all'
# 'ScalingActive: can it read the metrics'
# 'ScalingLimited: has a minimum or maximum capped the result'
# Box dimensions: x=1060, y=720, w=500, h=190 (ends at y=910)
# Wait! Where does External API go if Conditions ends at 910?
# External API: y = 920, h = 80 (ends at 1000)
# Cmd ext: y = 1010, h = 90? Wait, 1010 to 1100?
# Let's check!
