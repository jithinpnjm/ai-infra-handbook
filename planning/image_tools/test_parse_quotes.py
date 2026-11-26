import re

spec = "Timeline of one streamed request. 'headers: HTTP 200 sent with the first token'; 'tokens stream'; 'server fails mid-stream: a data: error chunk and [DONE] under HTTP 200; the engine counts it as finished_reason error; a client disconnect is counted as abort'. Two measuring rows. Row 'status-code SLI: 200 means success, dashboard shows 100 percent while customers see replies stop in the middle'. Row 'stream SLI: good only if the stream ends with a normal finish; a mid-stream abort by the server counts as bad'. Fix list 'count a stream good only if it ends normally; add a gateway counter for streams that ended with a server-side abort; cross-check against vllm:request_success_total by finished_reason; do not alert on abort alone because client disconnects count as abort'. Footer 'how the gateway observes a mid-stream break depends on its design, so name the assumption you make; also count the outcome the customer sees, not each attempt, and track retries separately'. Text at least 24px."

quotes = re.findall(r"'([^']+)'", spec)
print(f"Extracted {len(quotes)} quoted strings:")
for i, q in enumerate(quotes, 1):
    print(f"{i}. '{q}'")
