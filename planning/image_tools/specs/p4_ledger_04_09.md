# docs/part-04-automation/09-a-real-playbook-end-to-end-deploying-an-application.md
- ## Why this matters for AI infrastructure | 215 | NO FIGURE NEEDED high-level introduction to deployment automation
- ## Prerequisites and outcomes | 135 | NO FIGURE NEEDED bulleted list of reader goals
- ## 1. Target architecture | 240 | COVERED(p2-0409-architecture, m4-09-1)
- ### Why production deployment is harder than `runserver` (*Ansible: Up and Running*, Chapters 6 and 7, `mezzanine.yml`) | 760 | NEEDS FIGURE comparison across laptop runserver vs multi-tier production stack
- ## 2. Project layout | 220 | COVERED(a09-site-order)
- ## 3. Variables | 220 | NO FIGURE NEEDED variable listing and vault references
- ## 4. The baseline and database plays | 490 | COVERED(p4-0409-three-db-limits)
- ## 5. The application play: release directories and an atomic switch | 920 | COVERED(p4-0409-expand-contract, p4-0409-app-play-stages, a09-release-switch)
- ## 6. The web tier: nginx, TLS and rate limiting | 530 | NEEDS FIGURE request flow through nginx TLS, rate limiting, and upstream pool
- ## 7. Verification play | 210 | COVERED(a09-verify-paths)
- ## 8. Idempotency and safety checks | 230 | COVERED(p4-0409-safety-run-ladder)
- ## 9. A container-based variant | 340 | COVERED(p4-0409-venv-vs-container)
- ## 10. Troubleshooting a failed deploy | 230 | COVERED(p4-0409-deploy-troubleshoot)
- ## 11. Lab | 250 | NO FIGURE NEEDED step-by-step hands-on instructions
- ## 12. Common mistakes | 190 | NO FIGURE NEEDED bulleted list of pitfalls
- ## 13. Interview angles | 120 | NO FIGURE NEEDED sample interview questions
- ## Exercises | 240 | NO FIGURE NEEDED practice exercises
- ## Checkpoint questions (20) | 1700 | NO FIGURE NEEDED review questions and answers
- ## Sources and review notes | 280 | NO FIGURE NEEDED bibliographic attribution

Specs kept 2, dropped 0: []
