llm_lines = [
    "LLM prefix cache:",
    "consistent hashing on a",
    "session ID or prompt-prefix",
    "hash, with bounded loads",
    "that spill to the next",
    "replica when one exceeds",
    "its share"
]
from test_optimal_wrap import test_wrap
llm_label = "LLM prefix cache: consistent hashing on a session ID or prompt-prefix hash, with bounded loads that spill to the next replica when one exceeds its share"
test_wrap(llm_label, llm_lines, 24, 500, 20)
