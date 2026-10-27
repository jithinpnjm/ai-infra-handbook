# Phase 2 Ledger: How Linux Works, 3rd Edition

- **Corpus folder name:** `how-linux-works-3rd-edition`
- **Source code:** `HLW`
- **Date:** 2026-10-26

| Book chapter | Handbook chapter and section | What was added (one line) | Date |
|---|---|---|---|
| Chapter 1: The Big Picture | 1.1 `## Why this matters`, `## 2. The three layers`–`## 4. Processes, users, and who starts what` | Added `exec()` C library family (`execl()`, `execv()`, `execvp()`) + `execve()`, component overview framing, and Silberschatz *Operating System Concepts* 10th ed. / Love *Linux Kernel Development* 3rd ed. references (`book_passages.py`: `0%` missing). | 2026-10-27 |
| Chapter 13: User Environments | 1.2 `## 8. Environment variables, PATH and startup files` & 1.6 `## 6. Shell startup files: the user environment` | Added full startup file guidelines, `/etc/profile` and first-of `.bash_profile`/`.bash_login`/`.profile` rule, `. $HOME/.bashrc` sourcing, `case $- in *i*)`, `tcsh` `.tcshrc`/`.cshrc` sample, `.exrc` `set showmatch`, and the 6 startup pitfalls (`book_passages.py`: `0%` missing). | 2026-10-27 |
