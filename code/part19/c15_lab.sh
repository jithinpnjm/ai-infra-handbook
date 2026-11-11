#!/usr/bin/env bash
# Lab for chapter 19.15. Run from the repository root. No GPU, no network, no secrets.
set -euo pipefail

python3 -m pytest code/part19/test_c15_sheet.py code/part19/test_c15_numbers.py \
  code/part19/test_c15_simulate_interview.py code/part19/test_c15_walkthrough.py -q

python3 code/part19/c15_sheet_validator.py
python3 code/part19/c15_numbers.py
python3 code/part19/c15_walkthrough.py

python3 code/part19/c15_simulate_interview.py --rounds 3 --seed 3 --seconds 120 \
  --answers code/part19/c15_sample_answers.json --bank /nonexistent --log /tmp/c15_session_log.jsonl
