# Gem-book restoration plan

Goal: nothing from the gem books is missing from the handbook, in a human teaching voice.

- Queue: `tools/restore/manifest.py` -> `QUEUE.json` (114 units = book chapter -> handbook chapter(s); 15% or more missing).
- Work unit = one book chapter. A Haiku agent reads the book chapter in full, restores uncovered material into the target handbook chapter(s), in original wording.
- Concurrency rule: agents running at the same time must have disjoint target-file sets. Units on the same file run one after another.
- Gate (`tools/restore/gate.py Uxxx`): no technical terms/numbers lost, fences balanced, checkpoint questions kept, no escaped HTML, front matter unchanged, uncovered share drops by 20 points or reaches 10% or less, fewer than 25 verbatim 14-word overlaps with the book.
- Supervisor (Claude) backs up files before each wave, runs the gate after, spot-reads a sample, re-queues failures with the gate output, then runs lint, Mermaid and build once per wave and commits.
- Waves: pilot (3 units) -> Part 15 and 12 AI units -> Kubernetes (Production K8s, K8s Up & Running) -> Linux, HPC, AI Factory -> Learning Python (decide compression first) -> units under 15% -> the ~70 untriaged books (triage first).
- Backups: `planning/restore/backup/<unit>/` (git-ignored).
