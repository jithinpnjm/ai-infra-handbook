import xml.etree.ElementTree as ET
import re
import pathlib

# Let's verify our layout and label script
expected_labels = [
    "A long loop must look alive: the four UX tools and Ctrl+C",
    "Need",
    "Feature",
    "Long loop with no progress looks like a hang",
    "progress bar",
    "Waiting on something",
    "spinner",
    "Watch a changing state",
    "--watch polls and redraws the screen",
    "Stream new output",
    "--follow",
    "Operation that finishes asynchronously",
    "--wait and --timeout flags; poll the status endpoint with backoff like kubectl rollout status",
    "User presses Ctrl+C",
    "catch KeyboardInterrupt, clean up, return exit code 130",
    "start operation",
    "poll status with backoff",
    "done, or --timeout reached",
    "exit code",
    "progress and spinners go to stderr and only on a terminal",
    "Think of the person running your tool at 3 a.m."
]

print(f"Total expected labels: {len(expected_labels)}")
