# docs/part-04-automation/10-debugging-ansible-playbooks.md
- ## Why this matters for AI infrastructure | 230 | NO FIGURE NEEDED introductory motivation comparing playbook troubleshooting to medical triage
- ## Prerequisites and outcomes | 120 | NO FIGURE NEEDED bullet list of prerequisites and learning outcomes
- ## 1. A layered method | 420 | COVERED(p4-0410-four-questions-case, p2-0410-layer-flow, m4-10-1)
- ## 2. Verbosity and output | 350 | COVERED(p4-0410-verbosity-zoom)
- ## 3. The `debug` and `assert` modules | 440 | NEEDS FIGURE flow of pairing stat with assert preflight checks versus downstream cascade failure
- ## 4. Controlling the run while investigating | 350 | COVERED(p4-0410-investigation-flags)
- ### The interactive debugger | 240 | COVERED(a10-debugger-paths)
- ## 5. Classifying common failures | 180 | NO FIGURE NEEDED conceptual introduction to error signatures and layering
- ### Parse and templating errors before execution | 170 | NO FIGURE NEEDED reference table pairs YAML and Jinja syntax errors with causes and fixes
- ### Connection layer (UNREACHABLE) | 680 | COVERED(p4-0410-ssh-key-hygiene, p4-0410-ssh-step-chain, a10-agent-forwarding)
- ### Privilege and module layer | 180 | COVERED(p4-0410-privilege-module-table)
- ### Application layer | 200 | NEEDS FIGURE manual reproduction triage comparing interactive login shell with Ansible non-login execution environment
- ## 6. Reproducing a module run by hand | 330 | COVERED(a10-module-by-hand)
- ## 7. Debugging variables and templates | 340 | COVERED(p4-0410-which-value-wins)
- ## 8. Performance debugging | 380 | COVERED(p4-0410-slow-run-causes)
- ## 9. Debugging at scale and in CI | 380 | COVERED(a10-group-failures)
- ## 10. Prevention habits | 210 | NO FIGURE NEEDED numbered operational checklist
- ## 11. Lab | 380 | NO FIGURE NEEDED lab walkthrough and exercise instructions
- ## 12. Common mistakes | 310 | NO FIGURE NEEDED bullet list of common anti-patterns
- ## 13. Interview angles | 230 | NO FIGURE NEEDED interview questions and speaking points
- ## Exercises | 280 | NO FIGURE NEEDED numbered practice exercises
- ## Checkpoint questions (20) | 1400 | NO FIGURE NEEDED detailed self-study questions and answers
- ## Sources and review notes | 260 | NO FIGURE NEEDED source citations and test verification notes

Specs kept 2, dropped 0: []
