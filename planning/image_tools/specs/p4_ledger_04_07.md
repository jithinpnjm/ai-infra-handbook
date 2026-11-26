# docs/part-04-automation/07-ansible-variables-facts-templates-and-filters.md
- ## Why this matters for AI infrastructure | 250 | COVERED(p4-0407-data-not-copies)
- ## Prerequisites and outcomes | 110 | NO FIGURE NEEDED outcomes list
- ## 1. Defining variables | 130 | NO FIGURE NEEDED introductory framing leading directly into subsections
- ### Where and how | 380 | COVERED(p4-0407-where-defined)
- ### Naming and types | 340 | COVERED(p4-0407-default-mandatory-assert, p4-0407-names-and-brackets)
- ### Scope and lifetime | 290 | COVERED(p4-0407-set-fact-and-lazy, p2-0407-scope-lifetime)
- ## 2. Registered results and set_fact | 380 | COVERED(p4-0407-register-anatomy, a07-register-set-fact)
- ## 3. Facts | 450 | COVERED(p4-0407-fact-gathering-cost, p4-0407-facts-commands)
- ### Custom (local) facts | 170 | COVERED(p4-0407-local-facts)
- ### Magic variables | 340 | COVERED(p4-0407-magic-table, a07-limit-hostvars, m4-07-1)
- ## 4. Lookups | 350 | COVERED(p4-0407-lookup-table, p4-0407-lookup-vs-query, a07-lookup-control-node)
- ## 5. Loops over data | 260 | COVERED(p4-0407-loop-patterns)
- ## 6. Filters for configuration generation | 290 | COVERED(p4-0407-filter-needs, a07-extract-pipeline)
- ## 7. Templates in practice | 210 | COVERED(p4-0407-template-module-options)
- ### Example 1: /etc/hosts for the cluster | 130 | COVERED(p4-0407-hosts-template-trace)
- ### Example 2: Slurm node and GRES configuration derived from data | 210 | COVERED(p4-0407-slurm-node-line)
- ### Example 3: Prometheus file_sd targets | 80 | COVERED(p4-0407-file-sd-and-yaml)
- ### Example 4: YAML output from data | 75 | COVERED(p4-0407-file-sd-and-yaml)
- ### Good template practice | 240 | COVERED(p4-0407-template-practice)
- ## 8. Variable precedence debugging toolkit | 280 | COVERED(p4-0407-detective-commands, p2-0407-precedence-detective)
- ## 9. Security of variables and templates | 270 | COVERED(p4-0407-secret-leak-paths)
- ## 10. Lab | 330 | NO FIGURE NEEDED lab walk-through steps and commands
- ## 11. Common mistakes | 270 | COVERED(p4-0407-mistake-groups)
- ## 12. Interview angles | 120 | NO FIGURE NEEDED interview questions list
- ## Exercises | 160 | NO FIGURE NEEDED practice questions
- ## Checkpoint questions (20) | 1800 | NO FIGURE NEEDED question and answer drill
- ## Sources and review notes | 230 | NO FIGURE NEEDED sources and verification notes

Specs kept 0, dropped 0: []
