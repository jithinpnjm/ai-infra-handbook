# Figure plan: part-08-bcm, part-09-nvidia-systems, part-10-gpu-cuda

Scope: read-only pass over all chapters of the three volumes. No images generated, no docs/*.md edited. Per-chapter notes are in `v8910_notes.md`; specs are `v8_NN.json`, `v9_NN.json`, `v10_NN.json` in this folder.

## Counts per volume

| Volume | Chapters | Spec files | SVG specs | Existing mermaid blocks (kept) | Raster candidates |
|---|---|---|---|---|---|
| part-08-bcm | 16 | 16 | 34 | 24 | 0 |
| part-09-nvidia-systems | 14 | 14 | 33 | 34 | 0 |
| part-10-gpu-cuda | 22 | 22 | 49 | 56 | 0 |
| **Total** | **52** | **52** | **116** | **114** | **0** |

Each SVG spec has `part`, `ch`, `name`, `title`, `spec`, `anchor`, `alt`, `cap`. Every anchor was checked with `grep -c -x -F` and returns exactly one match in its chapter. Every spec file parses as JSON.

Chapters with 0 figures: none. Every chapter got at least one figure, so the 0-figure rule for thin chapters did not apply.

## Figure rules applied

- 1 to 4 figures per chapter, placed under the heading the figure explains.
- Figures explain a concept (ladders, timelines, budgets, bit layouts, sector counts, pipeline handoffs). They are not restatements of table rows.
- Mermaid blocks were kept by default. A figure was added only where the mermaid diagram did not already show the concept, or showed it poorly.
- Captions are one plain sentence with no curly braces. Alt text is short.

## Anomalies and decisions to review

1. **part-08-bcm ch16, five-role mermaid list.** Judged poor (a plain list of roles with no arrows). Recommend replacing it with a no-arrow spec. No spec was written for it in this pass, so the replacement is still open.
2. **part-08-bcm ch08 and part-10-gpu-cuda ch08, memory-lie mermaid.** part-10 ch08 section 2.3 uses an unconnected box diagram for the memory lie. Recommend replacing it with the stacked-bar spec `g08-memory-stack`. Both mermaid and spec are recorded in the notes.
3. **part-10 ch03 bank-conflict mermaid and ch13 bank-conflict mermaid.** Same concept shown in two chapters. Both are kept because each sits in its own chapter context. No new SVG was drawn for bank conflicts, to avoid a third copy.
4. **part-10 ch12 overlap gantt.** Kept as-is. The new `g12-engine-lanes` spec covers the same three-engine idea in lane form. Pick one when rendering; drawing both in the same chapter is not recommended.
5. **part-10 ch17 three-way overlap mermaid.** Same concept as `g12-engine-lanes`. Not re-drawn in ch17.
6. **Pipeline overlap concept repeated.** `g03-tma-pipeline` (part-10 ch03), `g13` (no TMA spec), `g16` (no TMA spec). Only ch03 has the ping-pong TMA figure. Keep it to one copy.
7. **dcgm-exporter 4.9.0 renames.** part-10 ch04, ch08 and ch21 carry a version note. Figures in those chapters use the 4.8.x names as the chapter text does. If the figures are rendered later, use the same field names as the surrounding text.
8. **Heavy mermaid chapters.** part-10 ch01 (7 mermaid) and part-10 ch02 (5 mermaid). Both still received 3 SVG specs each, placed under headings whose concept the mermaid diagrams do not cover (goodput, warp lanes, pinned staging; warp execution model and launch geometry). Re-check after rendering the mermaid output for overlap.
9. **Illustrative figures.** Many numbers come from sources marked illustrative (for example the bandwidth tables in part-10 ch03, ch11, ch12, and the timing breakdowns in ch17 and ch22). Figure captions use those numbers as stated in the text. A reviewer should confirm each figure keeps the chapter's own caveat.
10. **Nothing invented.** Specs quote numbers from the chapter text. Where a figure needed a value not in the text (for example the ch16 cluster diagram), the spec describes the structure only.

## Next steps (not done in this pass)

- Render the 116 SVG specs under the luna rules (1600 wide, text at least 24 px, single orange accent).
- Replace the part-08 ch16 mermaid with its no-arrow spec.
- Decide whether to swap the part-10 ch08 memory-lie mermaid for the stacked bar.
- Keep the figure-to-heading anchors unchanged if a heading is renamed, because the anchors are exact-match strings.
