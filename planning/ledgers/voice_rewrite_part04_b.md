# Voice rewrite Part 4 (chapters 14-27), agent B

## 14 Ansible at scale
- Rewritten in place. Words 6572 -> ~8900 (+34%).
- New numbers: 200,000 (100 loop items x 2,000 hosts, derived in text), 3,600 (async value, existing).
- Removed the phrase 'untested here' from Sources; replaced with 'marked as not run'. Kept status row and the 'not run on live hardware' sentence above the lab.
- Checkpoints and exercises kept verbatim. Guard: 0 hard failures; chain gate 0.0 per 1000.

## 16 (4.16 worklist item)
- Chapter already reads 'BGP unnumbered, uses RFC 5549 (2.16)' in the NVUE code comment; no code file in code/part04 carries 'RFC 7938 style'. RFC 7938 remains correctly tied to the eBGP design text.

## 15 Custom modules and AAP
- Rewritten in place. Words 7641 -> ~9500 (+24%, guard shows 9438 before the last span fix).
- New numbers, all in worked examples built from existing values: 700 W and eight GPUs (example), 500 forks (capacity example, 10 jobs x 50), 6000 W (validation example), 003/005/32 (filter walk-through of gpu[001-032] and gpu[001-003,005]).
- Removed 'untested here'; interactive steps now say 'were not run on live hardware'. Checkpoints and exercises kept verbatim.

## Status at stop
- Done: 14, 15 (rewritten, guard 0 hard failures, chain gate 0.0).
- Not started: 16 (read to line 618 of 739, not rewritten; file untouched), 17-27.
- 4.16 worklist item: chapter 16 NVUE comment already says RFC 5549 and text ties RFC 7938 to the eBGP design. No code file in code/part04 carries the 'RFC 7938 style' wording. No edit made to 16.
- 4.17 GPU tuning table: not checked (chapter 17 not read).
