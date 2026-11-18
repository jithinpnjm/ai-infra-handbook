# Part 1 image ledger (Gemini "4 Hydrogen", infographic style per planning/IMAGE_STYLE_GUIDE.md)

Capture: direct read from the Gemini page (no download prompts), native 1376x768 (the 1.1.1 office image was an earlier 2752x1536 button download, resized to 1600). Sources in ~/Downloads/handbook-images/originals, finals in final/, repo copies in docs/part-01-linux/img/.

## Chapter 1.1 (5 figures, each validated by viewing the final file against the chapter text)
| Figure | File | Validation |
|---|---|---|
| 1.1.1 | ch01-fig1-office-building | Analogy matches section 1; 7 labels exact; top floor slightly cropped. |
| 1.1.2 | ch01-fig2-kernel-user-mode | Rings, 4 steps, user-space crash vs kernel panic cards; all labels exact, once. |
| 1.1.3 | ch01-fig3-virtual-memory | Two page tables, one MMU, shared page, page fault, 4 steps; all labels exact. |
| 1.1.4 | ch01-fig4-everything-is-a-file | /dev/nvidia0, nvme0n1, null through Kernel and Device driver; steps and /proc,/sys,sockets strip exact. |
| 1.1.5 | ch01-fig5-system-calls | Your program, glibc/libc.so.6, dashed boundary, 5 syscall categories with listed calls (from chapter table), strace strip. |
Removed after owner review: plain box versions (rings, MMU boxes, devices, syscall stack), distro lineage (not a core concept), module-mismatch (under "How it fails").
Guard: 0 hard failures, 0 new or lost numbers. Site build not run (owner builds).

## Chapter 1.2 (5 figures, each validated by viewing the final file)
| Figure | File | Validation |
|---|---|---|
| 1.2.1 | ch02-fig1-quoting | Unquoted splits to 3 args, quoted stays 2; labels exact. |
| 1.2.2 | ch02-fig2-streams | stdout to file/pipe, stderr bypasses file (v2 after v1 misled). |
| 1.2.3 | ch02-fig3-exit-status | Pipeline stage statuses; labels exact. |
| 1.2.4 | ch02-fig4-environment | Parent to child copy of environment; labels exact. |
| 1.2.5 | ch02-fig5-startup-files | Login vs non-login startup files; labels exact. |
Guard: 0 hard failures; "new number 1.2" is only the figure label text (accepted).

## Chapter 1.3 (4 figures inserted, validated by viewing)
| Figure | File | Validation |
|---|---|---|
| 1.3.1 | ch03-fig4-paths | Absolute vs relative, rooms, ./.. chips; labels exact. |
| 1.3.2 | ch03-fig1-inode | Directory table, inode card (5 fields), data blocks, 4 steps; exact. |
| 1.3.3 | ch03-fig2-links | Hard link vs symlink lanes, badges, 3 chips; exact. |
| 1.3.4 | ch03-fig3-atomic-latest | v2 after v1 had duplicated Stage labels; exact. |
Guard: 0 hard failures (new number "1.3" is the figure label only).

## Chapter 1.4 (generated, NOT inserted yet; held in ~/Downloads/handbook-images/final/)
- ch04-fig3-xargs: accepted (slightly busy, accurate).
- ch04-fig1-pipeline: held, caption typo "sit sit"; needs regeneration.
- ch04-fig2-awk: held, stray closing brace in rule box, empty output boxes; needs regeneration.
- Prompts for ch1.5 (SSH key pairs, local port forward) were sent but Gemini hit its usage limit (resets 5:43 PM 2026-11-17); no images captured, tmux figure not started.

## Mermaid replacement via Luna SVGs (2026-11-17)
All 76 Part 1 Mermaid diagrams replaced by SVGs generated with `opencode run -m allex-ai/gpt-6-luna` (prompts in planning/luna_prompts/, rules in planning/luna_rules.md), then a second self-repair pass where Luna sees its own render. Files: docs/part-01-linux/img/chNN-dK-luna.svg; originals/first drafts in ~/Downloads/luna-svgs/ (orig/ = first drafts). Figures renumbered per chapter.
Known weak: ch22-d2 (troubleshooting flow, arrows cluttered), ch07-d4, ch06-d2, ch18-d4 (minor overlaps). Captions are bare diagram titles; richer captions and EPUB SVG check still to do. Site build and Mermaid check not run.

## Gemini pass, chapters 1.4-1.30 (2026-11-17, evening)
One to three Gemini infographics per chapter on core mechanisms, inserted next to the Luna SVGs; guard clean (only Mermaid removals + figure labels). Source JPEGs in ~/Downloads/handbook-images/final/.
- 1.4 pipeline count-by-key, awk fields, xargs fan-out. 1.5 SSH key pairs, -L tunnel, tmux, jump host. 1.6 permission bits, special bits+umask, sudo gates.
- 1.7 package layers, source install. 1.8 process states. 1.9 strict mode+trap. 1.10 udev, /dev /sys /proc. 1.11 syscall boundary, shared libs.
- 1.12 mount. 1.13 RAID levels, lvextend online. 1.14 BIOS/MBR vs UEFI/GPT. 1.15 Wants vs After. 1.16 cron line. 1.17 OOM. 1.18 cgroup v2 tree. 1.19 namespace types.
- 1.21 capabilities. 1.22 NVIDIA stack. 1.23 60-second checklist. 1.24 flame graph. 1.25 benchmark loop. 1.26 VFIO passthrough. 1.28 NUMA placement. 1.30 rsync slash.
- Not done: 1.8 fork/exec (two drafts rejected: confusing), 1.20 (lab), 1.27, 1.29 own figure.
