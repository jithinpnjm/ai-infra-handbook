# Let's check each of the 5 nodes in Lane 1:
# Node 1: 'vLLM pod exposes vllm:num_requests_waiting'
# Can it be wrapped into:
# 'vLLM pod exposes' (16 chars * 14.4 = 230 px)
# 'vllm:' (5 chars = 72 px)
# 'num_requests_waiting' (20 chars = 288 px)
# Or:
# 'vLLM pod' (8 chars = 115 px)
# 'exposes' (7 chars = 100 px)
# 'vllm:num_requests_waiting' (25 chars * 14.4 = 360 px)
