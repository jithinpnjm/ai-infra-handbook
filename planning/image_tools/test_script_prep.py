import xml.etree.ElementTree as ET
import re
import asyncio
from playwright.async_api import async_playwright
import pathlib

# Let's write the test suite for p2-2001-reader-map
svg_filename = "candidate_reader_map.svg"

# Let's inspect what expected_labels should be
expected_labels = [
    "Which chapters serve which interview stage",
    "Recruiter call, CV",
    "20.1, 20.2",
    "Linux console and troubleshooting",
    "20.3, 20.4, 20.5, 20.6, 20.7",
    "Coding and algorithms",
    "20.8, 20.9, 20.10, 20.11",
    "System design",
    "20.12, 20.13, 20.14, 20.15, 20.16",
    "20.17 timed drills",
    "Stress interview, 30-minute incident",
    "20.26, 20.27",
    "Final hour, project deep dive",
    "20.28",
    "[official]",
    "[official] and [report]",
    "[report]",
    "[official]",
    "Start with Part B console and Part D design, because both appear in every report."
]

print("Total expected labels:", len(expected_labels))
print("Unique expected labels:", len(set(expected_labels)))
