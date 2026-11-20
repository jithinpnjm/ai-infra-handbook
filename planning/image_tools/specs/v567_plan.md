# Vol 5/6/7 figure plan - PARTIAL

Status: 2 of 105 chapters processed (v5 ch01, ch02). Not complete. Remaining: v5 ch03-35, all of v6 (31), all of v7 (15).

| Volume | Chapters | Done | SVG specs | Mermaid blocks (chapters done) | Raster candidates |
|---|---|---|---|---|---|
| Vol 5 part-05-kubernetes | 35 | 2 | 8 | 4 (ch01 3, ch02 1) | 0 |
| Vol 6 part-06-hpc-slurm | 31 | 0 | 0 | not counted yet | 0 |
| Vol 7 part-07-redfish-bmc | 15 | 0 | 0 | not counted yet | 0 |

Odd things:
- Chapter 01 is about 937 lines, and the read needs two Read calls because the first is truncated at about 25k tokens.
- Mermaid counts above come from grep of the fence lines. Chapters 07 (5 blocks) and 33 (3) need a look when processed.
- Full read of all 105 chapters is far more than one run's context budget. Split into batches of about 15 chapters per run.

## Batch update: v5 ch03 done (v5_03.json, 4 specs)
