import xml.etree.ElementTree as ET
import re

labels = [
    "Four limits, four different fences",
    "Requests per second: protects gateway, tokenizer, scheduler; unit requests; missing: connection floods",
    "Tokens per second: protects GPU compute and KV cache; unit prompt plus output tokens; missing: one tenant starves the rest",
    "Concurrent streams: protects open connections and decode slots; unit streams; missing: decode queues overrun",
    "Daily or monthly quota: protects the bill and the contract; unit tokens; missing: surprise cost",
    "token bucket: a jar that starts full, is spent per request, refills slowly, and allows bursts up to bucket size; charge prompt tokens plus max output tokens at admission, refund the unused at the end; reject at once what can never fit; a refused request must not burn a request slot; distributed choice: shared store such as Redis is exact but adds a hop and a dependency, local buckets are fast and slightly loose",
    "ten requests with 8,000 prompt tokens and a large max output made every other tenant TTFT double while a requests-per-minute limit saw nothing wrong"
]

print("Total labels:", len(labels))
for i, l in enumerate(labels):
    print(f"{i+1}: len={len(l)} '{l}'")
