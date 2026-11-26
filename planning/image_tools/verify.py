import xml.etree.ElementTree as ET
import re

tree = ET.parse("output.svg")
root = tree.getroot()

# Check fonts, texts, widths
# 1. Verify every label from prompt:
expected_labels = [
    "Logging rules: who configures, which level, which destination",
    "the useful line scrolled away and the next run overwrote the file",
    "Rules",
    "print for program output, logging for diagnostics with levels, destinations and structure",
    "levels DEBUG, INFO, WARNING, ERROR, CRITICAL, set through configuration or environment variables, not by editing code; setup_logging(verbosity): 0 gives WARNING, 1 gives INFO, anything higher DEBUG",
    "use %s placeholders, not f-strings: arguments are formatted only when the record is emitted",
    "one logger per module: log = logging.getLogger(__name__)",
    "libraries get a logger and add logging.NullHandler(); applications configure handlers once at startup",
    "log.error(..., exc_info=True) attaches the current traceback; log.exception() inside except does the same at ERROR level",
    "do not log inside tight loops at INFO: log summaries and sampled details, include units",
    "Destinations",
    "stderr is a good default, stdout stays clean for data; containers and systemd capture it into the journal",
    "RotatingFileHandler, TimedRotatingFileHandler, SysLogHandler, SocketHandler, QueueHandler for non-blocking logging",
    "logging.config.dictConfig for declarative setups",
    "in containers log to stdout and stderr and let the platform ship them",
    "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    "Structured logging",
    "JSON lines with fields such as host, job_id and duration_ms; structlog, python-json-logger or a custom Formatter; include a correlation or request id; redact secrets and personal data",
    "Applications configure handlers once, libraries never do"
]

# Extract all text from SVG by text element
all_texts = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    # gather all text in this elem, including tspans
    full_str = "".join(elem.itertext())
    # normalize spaces
    normalized = " ".join(full_str.split())
    all_texts.append(normalized)

print(f"Found {len(all_texts)} text elements in SVG.")
for t in all_texts:
    print(" -", t[:60])

print("\n--- Verifying exact matches for all expected labels ---")
matched = []
for exp in expected_labels:
    # check if exp is in all_texts
    if exp in all_texts:
        matched.append(exp)
    else:
        print("FAILED TO MATCH EXACTLY:", exp)
        # find closest
        for t in all_texts:
            if exp[:20] in t:
                print("   Found close candidate:", t)

print(f"Matched {len(matched)} / {len(expected_labels)}")
assert len(matched) == len(expected_labels), "Some labels did not match!"

# Check no text is smaller than 24px
print("\n--- Checking font sizes ---")
# Check styles
style_text = root.find('.//{http://www.w3.org/2000/svg}style').text
for line in style_text.split('\n'):
    if 'font-size' in line:
        size = int(re.search(r'font-size:\s*(\d+)px', line).group(1))
        print(f"Style: {line.strip()} -> size {size}")
        assert size >= 24, f"Font size too small: {size}"

print("\nAll assertions passed!")
