# Let's test widths for 4 columns:
# Col 1 (Sources): vLLM pod / Kafka
# Col 2 (Rules): Prometheus & Adapter rule / kafka rule
# Col 3 (APIs): custom.metrics.k8s.io / external.metrics.k8s.io
# Col 4 (HPA): HPA reads it and decides

# Widths required:
# Col 1: vllm:num_requests_waiting needs 360 px + 32 = 392 px. Say 390 px.
# Col 2: with namespace and pod labels; needs 432 px + 32 = 464 px. Say 470 px.
# Col 3: custom.metrics.k8s.io needs 302 px + 32 = 334 px.
#        Wait, cmd_custom in 4 lines: widest line is 416.6 px + 32 = 448.6 px! Say 450 px.
# Col 4: HPA reads it and decides needs 345.6 px + 32 = 377.6 px.
#        Conditions box: widest line 42 chars = 604 px?
#        Wait, what if Conditions box is in Col 4?

print(f"Col 1 (390) + Col 2 (470) + Col 3 (450) = {390 + 470 + 450} px")
print(f"Remaining for Col 4: {1600 - (390 + 470 + 450)} = 290 px")
