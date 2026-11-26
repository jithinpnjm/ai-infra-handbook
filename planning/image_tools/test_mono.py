#!/usr/bin/env python3
for fs in [24]:
    print("metadata.resourceVersion:", len("metadata.resourceVersion") * fs * 0.62)
    print("status.observedGeneration:", len("status.observedGeneration") * fs * 0.62)
    print("metadata.generation:", len("metadata.generation") * fs * 0.62)
