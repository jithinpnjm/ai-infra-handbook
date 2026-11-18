# Image style guide for handbook figures (owner direction, 2026-11-17)

## What deserves an image
Only a core TECHNICAL CONCEPT that is hard to picture from text: a mechanism, a flow, a relationship between parts, a before/after. Examples: how virtual memory is translated, why kernel mode and user mode exist, how a system call crosses into the kernel, how a container is built from namespaces.
NOT images: command output (ls, ps), lookup lists, family trees or lineages, tables, anything already clear as text or Mermaid. Not in labs, exercises, checkpoints or "How it fails". Fewer, stronger images per chapter beats many plain ones.

## Style
- Infographic, not a flat box diagram. A visual metaphor or a small story scene (the office building was the best so far), plus numbered steps showing the mechanism, plus a short "why it matters" strip along the bottom.
- Rich but ordered: one main scene, 3 to 5 numbered callouts, 8 to 14 short labels in total. Large readable text (it must stay legible at phone and e-reader width).
- Consistent palette: white or very light background, dark grey, one green accent, one orange highlight for the thing that goes wrong or is checked.
- Labels come from the chapter's own words. No invented facts or numbers.

## Prompt template
"Create an image: a polished educational infographic, 16:9, light background, dark-grey and green palette with one orange highlight, flat vector style, large readable text. Title: <title>. Main scene: <metaphor scene>. Numbered steps 1 to N in order: <step 1: text>, <step 2: text> ... Bottom strip labelled Why it matters: <one sentence>. TEXT RULES: use only these words, each exactly once, spelled exactly, no other text: <list>."

## Validation (every image)
View the final file at full size. Each label spelled exactly and once, steps in the right order, every claim present in the chapter text, nothing misleading. Regenerate rather than accept.
