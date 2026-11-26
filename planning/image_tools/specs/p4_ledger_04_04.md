# docs/part-04-automation/04-yaml-and-jinja2-for-infrastructure-code.md
- ## Why this matters for AI infrastructure | 180 words | NO FIGURE NEEDED introductory framing on YAML/Jinja2 role in AI cluster outages and Friday Slurm scenario
- ## Prerequisites and outcomes | 140 words | NO FIGURE NEEDED prerequisites and learning outcomes summary
- ## 1. YAML essentials | 300 words | COVERED(p4-0404-three-structures)
- ### Rules that bite | 650 words | COVERED(p4-0404-duplicates-multidoc-safe, p4-0404-block-scalars, p4-0404-coercion-list, p4-0404-quoting-rules, a04-yaml-coercion)
- ### Anchors, aliases and merge keys | 240 words | COVERED(p4-0404-merge-walkthrough, a04-anchor-merge)
- ### JSON, YAML and other formats | 650 words | COVERED(p4-0404-yamllint-config, p4-0404-yang-pure-yaml, p4-0404-decode-deserialize, p4-0404-inspect-as-json, m4-04-1)
- ## 2. Jinja2 essentials | 350 words | COVERED(p4-0404-strictundefined, p4-0404-render-model)
- ### Expressions | 140 words | COVERED(p4-0404-expressions-ops)
- ### Filters | 230 words | COVERED(p4-0404-filter-categories, p2-0404-filter-pipe)
- ### Tests | 140 words | COVERED(p4-0404-tests-vs-filters)
- ### Control structures | 230 words | COVERED(p4-0404-groupby-trace)
- ### Whitespace control | 180 words | COVERED(p2-0404-whitespace-trim)
- ### Macros, includes, inheritance, raw blocks | 170 words | COVERED(p4-0404-reuse-tools)
- ## 3. Jinja2 in Ansible | 450 words | COVERED(p4-0404-nccl-dictsort, p4-0404-slurm-nodes-walk, p4-0404-lookups-template-module, p4-0404-string-bool-trap, p4-0404-ansible-jinja-places, a04-validate-install)
- ### Network switchport templates, custom Python filters (`get_interface_speed`), and NGINX TLS templates (*Network Programmability and Automation* Ch. 9 & *Ansible: Up and Running* Ch. 3) | 350 words | COVERED(p4-0404-nginx-tls-and-validate, p4-0404-switchport-walk)
- ## 4. Templating elsewhere (and how not to confuse them) | 300 words | COVERED(p4-0404-template-engines-map)
- ## 5. Testing and debugging templates | 380 words | COVERED(p4-0404-error-messages, p4-0404-three-checks)
- ## 6. Security considerations | 190 words | COVERED(p4-0404-template-injection-secrets)
- ## 7. Lab | 250 words | NO FIGURE NEEDED hands-on CLI commands and step-by-step exercise tasks
- ## 8. Common mistakes | 190 words | COVERED(p4-0404-mistake-groups)
- ## 9. Interview angles | 80 words | NO FIGURE NEEDED list of interview drill questions
- ## Exercises | 380 words | NO FIGURE NEEDED exercise prompt scenarios
- ## Checkpoint questions (20) | 1100 words | NO FIGURE NEEDED self-test Q&A pairs with detailed explanations
- ## Sources and review notes | 280 words | NO FIGURE NEEDED bibliographical citations and review notes

Specs kept 0, dropped 0: []
