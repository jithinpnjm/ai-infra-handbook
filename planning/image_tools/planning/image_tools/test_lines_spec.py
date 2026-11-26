import re
import xml.etree.ElementTree as ET

# Define the text content and line breaks
fence1_lines = [
    ("Requests", 30, True),
    ("per second:", 30, True),
    ("protects gateway,", 24, False),
    ("tokenizer, scheduler;", 24, False),
    ("unit requests;", 24, False),
    ("missing:", 24, False),
    ("connection floods", 24, False)
]

fence2_lines = [
    ("Tokens", 30, True),
    ("per second:", 30, True),
    ("protects GPU compute", 24, False),
    ("and KV cache;", 24, False),
    ("unit prompt plus", 24, False),
    ("output tokens;", 24, False),
    ("missing: one tenant", 24, False),
    ("starves the rest", 24, False)
]

fence3_lines = [
    ("Concurrent", 30, True),
    ("streams:", 30, True),
    ("protects open", 24, False),
    ("connections and", 24, False),
    ("decode slots;", 24, False),
    ("unit streams;", 24, False),
    ("missing: decode", 24, False),
    ("queues overrun", 24, False)
]

fence4_lines = [
    ("Daily or", 30, True),
    ("monthly quota:", 30, True),
    ("protects the bill", 24, False),
    ("and the contract;", 24, False),
    ("unit tokens;", 24, False),
    ("missing:", 24, False),
    ("surprise cost", 24, False)
]

mech_lines = [
    ("token bucket: a jar that starts full, is spent per request, refills slowly,", 24, False),
    ("and allows bursts up to bucket size; charge prompt tokens plus max output", 24, False),
    ("tokens at admission, refund the unused at the end; reject at once what can", 24, False),
    ("never fit; a refused request must not burn a request slot; distributed", 24, False),
    ("choice: shared store such as Redis is exact but adds a hop and a", 24, False),
    ("dependency, local buckets are fast and slightly loose", 24, False)
]

inc_lines = [
    ("ten requests with 8,000 prompt tokens and a large max output made every", 24, False),
    ("other tenant TTFT double while a requests-per-minute limit saw nothing wrong", 24, False)
]

expected = [
    "Four limits, four different fences",
    "Requests per second: protects gateway, tokenizer, scheduler; unit requests; missing: connection floods",
    "Tokens per second: protects GPU compute and KV cache; unit prompt plus output tokens; missing: one tenant starves the rest",
    "Concurrent streams: protects open connections and decode slots; unit streams; missing: decode queues overrun",
    "Daily or monthly quota: protects the bill and the contract; unit tokens; missing: surprise cost",
    "token bucket: a jar that starts full, is spent per request, refills slowly, and allows bursts up to bucket size; charge prompt tokens plus max output tokens at admission, refund the unused at the end; reject at once what can never fit; a refused request must not burn a request slot; distributed choice: shared store such as Redis is exact but adds a hop and a dependency, local buckets are fast and slightly loose",
    "ten requests with 8,000 prompt tokens and a large max output made every other tenant TTFT double while a requests-per-minute limit saw nothing wrong"
]

def check_reconstructed(lines, exp):
    reconstructed = " ".join(t[0] for t in lines)
    assert reconstructed == exp, f"Mismatch!\nReconstructed: '{reconstructed}'\nExpected:      '{exp}'"
    print(f"MATCH OK: '{exp[:40]}...'")

check_reconstructed(fence1_lines, expected[1])
check_reconstructed(fence2_lines, expected[2])
check_reconstructed(fence3_lines, expected[3])
check_reconstructed(fence4_lines, expected[4])
check_reconstructed(mech_lines, expected[5])
check_reconstructed(inc_lines, expected[6])
print("\nAll 6 composite texts reconstruct to exact expected strings!")
