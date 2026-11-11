#!/usr/bin/env bash
# Lab for 19.14: validate the bank, draw a mixed set, run a short scored quiz, run the tests.
# Run from the repository root. Needs Python 3 and pytest. No GPU, cluster or network access.
set -euo pipefail
cd code/part19
python3 c14_bank.py
python3 c14_walkthrough.py --n 6 --seed 14
printf '\n\n3\n\n1\nq\n' | python3 c14_score.py --state /tmp/c14_lab_state.json --n 2 --topic linux --seed 1
python3 c14_score.py --state /tmp/c14_lab_state.json --report
python3 -m pytest test_c14_bank.py test_c14_score.py test_c14_walkthrough.py -q
