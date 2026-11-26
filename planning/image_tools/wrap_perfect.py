def wrap_text(text, max_chars):
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        add_len = len(w) + (1 if cur else 0)
        if cur_len + add_len <= max_chars:
            cur.append(w)
            cur_len += add_len
        else:
            if cur:
                lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(' '.join(cur))
    return lines

items_col = {
    "rule1": ("print for program output, logging for diagnostics with levels, destinations and structure", 42),
    "rule2": ("levels DEBUG, INFO, WARNING, ERROR, CRITICAL, set through configuration or environment variables, not by editing code; setup_logging(verbosity): 0 gives WARNING, 1 gives INFO, anything higher DEBUG", 43),
    "rule3": ("use %s placeholders, not f-strings: arguments are formatted only when the record is emitted", 43),
    "rule4": ("one logger per module: log = logging.getLogger(__name__)", 35),
    "rule5": ("libraries get a logger and add logging.NullHandler(); applications configure handlers once at startup", 42),
    "rule6": ("log.error(..., exc_info=True) attaches the current traceback; log.exception() inside except does the same at ERROR level", 43),
    "rule7": ("do not log inside tight loops at INFO: log summaries and sampled details, include units", 43),
    "dest1": ("stderr is a good default, stdout stays clean for data; containers and systemd capture it into the journal", 43),
    "dest2": ("RotatingFileHandler, TimedRotatingFileHandler, SysLogHandler, SocketHandler, QueueHandler for non-blocking logging", 42),
    "dest3": ("logging.config.dictConfig for declarative setups", 42),
    "dest4": ("in containers log to stdout and stderr and let the platform ship them", 42),
    "format_ex": ("%(asctime)s %(levelname)-8s %(name)s: %(message)s", 30),
    "struct_text": ("JSON lines with fields such as host, job_id and duration_ms; structlog, python-json-logger or a custom Formatter; include a correlation or request id; redact secrets and personal data", 92)
}

for k, (txt, max_c) in items_col.items():
    res = wrap_text(txt, max_c)
    print(f"=== {k} (max {max_c}, {len(res)} lines) ===")
    for l in res:
        print(f"  [{len(l):2d} ch] {l}")
    # verify reconstitution
    reconstructed = " ".join(res)
    assert reconstructed == txt, f"Mismatch in {k}!"

print("\nAll reconstitutions match perfectly!")
