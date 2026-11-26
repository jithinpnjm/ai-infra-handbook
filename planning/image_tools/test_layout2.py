def wrap_to_lines(text, max_chars):
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
            lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(' '.join(cur))
    return lines

# Let's test all labels:
raw_labels = {
    "title": "Logging rules: who configures, which level, which destination",
    "opening": "the useful line scrolled away and the next run overwrote the file",
    "rules_head": "Rules",
    "rule1": "print for program output, logging for diagnostics with levels, destinations and structure",
    "rule2": "levels DEBUG, INFO, WARNING, ERROR, CRITICAL, set through configuration or environment variables, not by editing code; setup_logging(verbosity): 0 gives WARNING, 1 gives INFO, anything higher DEBUG",
    "rule3": "use %s placeholders, not f-strings: arguments are formatted only when the record is emitted",
    "rule4": "one logger per module: log = logging.getLogger(__name__)",
    "rule5": "libraries get a logger and add logging.NullHandler(); applications configure handlers once at startup",
    "rule6": "log.error(..., exc_info=True) attaches the current traceback; log.exception() inside except does the same at ERROR level",
    "rule7": "do not log inside tight loops at INFO: log summaries and sampled details, include units",
    "dest_head": "Destinations",
    "dest1": "stderr is a good default, stdout stays clean for data; containers and systemd capture it into the journal",
    "dest2": "RotatingFileHandler, TimedRotatingFileHandler, SysLogHandler, SocketHandler, QueueHandler for non-blocking logging",
    "dest3": "logging.config.dictConfig for declarative setups",
    "dest4": "in containers log to stdout and stderr and let the platform ship them",
    "format_ex": "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    "struct_head": "Structured logging",
    "struct_text": "JSON lines with fields such as host, job_id and duration_ms; structlog, python-json-logger or a custom Formatter; include a correlation or request id; redact secrets and personal data",
    "bottom_bar": "Applications configure handlers once, libraries never do"
}

for k, v in raw_labels.items():
    print(f"=== {k} ===")
    if k in ["title", "opening", "rules_head", "dest_head", "struct_head", "bottom_bar"]:
        print("  Single line:", v)
    elif k == "struct_text":
        lines = wrap_to_lines(v, 90)
        for l in lines:
            print(f"  [{len(l)}] {l}")
    elif k == "format_ex":
        # Format example line
        print(f"  [{len(v)}] {v}")
    else:
        lines = wrap_to_lines(v, 44)
        for l in lines:
            print(f"  [{len(l)}] {l}")
