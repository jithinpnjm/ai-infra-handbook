# Voice rewrite ledger: R6 (part-04-automation 05, 06, 09, 10, 16, 17, 20, 21, plus 23 fix)

Gates: chain_gate 0.0 to 0.3 per 1000 words on all; checkpoint `<details>` count 20 in every chapter; no code blocks, tables of existing content, headings (except noted) or Sources sections removed. language_audit warns (2) only on 09 and 21 for code-formatted term density (spans100 10.4 and 9.3); not reduced further.

## 05 inventory
Rewrote: Why-this-matters opening, connection-variable paragraph (split), plugin-settings paragraph (now a table), Common mistakes (bullets), interview wording, Exercises (6 stacked items became 12 single-situation items), "untested here" leak.
Confirmed/corrected: none needed. Not checked: nothing new.

## 06 playbooks
Rewrote: intro, outcomes, second webservers-tls pattern, kernel/system module paragraph (rest moved into a table), info/control-flow modules (table), platform collections paragraph, lab exercise 2 (14 modules cut to 9), "untested here" leak, Exercises (6 dense items became 12).
Confirmed: nothing factual changed.

## 09 real playbook
Rewrote: opening, outcomes, heading (removed the abbreviation "AUR", now the full book title), production paragraphs, lessons 3 to 5 split, systemd hardening paragraph (one option explained, was 3 names), idempotency culprit list, interview list wording, Exercises (6 became 13; the five-option hardening sentence became one option).
Added wording: NoNewPrivileges explanation ("stops gaining privileges, for example through a setuid binary") is standard systemd meaning, not from the chapter source; flag for the fact-checker.

## 10 debugging
Rewrote: outcomes, ansible.cfg settings (now an ini block plus prose), stat field dump (now the common fields plus a pointer to checkpoint 5), slow-run causes (bullets), lab paragraph, "untested here" leak, Exercises (6 became 13).

## 16 containers/cloud/network
Rewrote: outcomes, Docker module list (table), Packer paragraph (split), Kubernetes module paragraph, Windows module list, two headings (abbreviations "AUR", "NPA" replaced by full titles), Common mistakes (bullets), "untested here" leak, Exercises (nested (a)(b) removed, 6 became 14).
RFC check: 2.16 and its sources show RFC 7938 is the eBGP-in-the-data-center design and BGP unnumbered uses RFC 5549 (now RFC 8950). Corrected the prose cite (section 3 NVIDIA paragraph, exercise 10, checkpoint 11). Not fixed: a code comment inside the NVUE YAML block still says "BGP unnumbered, RFC 7938 style" (code blocks left alone).

## 17 GPU nodes
Rewrote: opening stack paragraph, "deterministic" slogan, outcomes, GPU tuning paragraph (150 words of flags became a table of setting, command, when needed; the "When you need it" cells are paraphrase and should be checked), Common mistakes (grouped bullets), "untested here" leak, Sources abbreviations (ASP, AUR replaced with full titles), Exercises (6 became 15).

## 20 modules
Rewrote: outcomes, the 12-item rule list (now themed paragraphs), the three module gotchas (path.module, inline versus separate rules told as short stories, locals), "untested here" leak, Exercises (6 became 14).

## 21 loops/lifecycle
Rewrote: heading (abbreviation "TUR" removed), splat/functions paragraph, 20-item gotcha list (now a trap / what happens / way out table, same content), "untested here" leak, Exercises (6 became 13), Sources abbreviation "TUR".
Corrected: checkpoint 15 said terraform_data was "Built into ansible-core / Terraform 1.4+"; ansible-core is irrelevant here, now "Built into Terraform 1.4 and later".

## 23 (neighbour, fixed on request)
"15-25 minutes (795.63s)": the Terraform: Up and Running 3rd edition chunk shows 795.63s is the printed runtime of the hello-world app stage integration test (about 13 minutes), and the book gives no 15 to 25 minute figure. Replaced with the sourced figure.

## Not done / noticed
- Exercise and checkpoint text not otherwise touched; most Sections other than those listed were left as they were (term-stack density remains in 17 section 3.2 kernel parameter paragraphs, 16 section 3 Nornir paragraph, 09 mezzanine lessons).
- Interview-angle bullets with semicolon-style fragments only lightly edited.
