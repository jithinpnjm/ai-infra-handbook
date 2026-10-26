# Phase 2 Ledger: How Linux Works, 3rd Edition

- **Corpus folder name:** `how-linux-works-3rd-edition`
- **Source code:** `HLW`
- **Date:** 2026-10-26

| Book chapter | Handbook chapter and section | What was added (one line) | Date |
|---|---|---|---|
| Chapter 1: The Big Picture | 1.1 `## 3. What the kernel does: four jobs` (`### Job 4: system calls and the services around them`) & `## 4. Processes, users, and who starts what` | Added explicit `exec()` C library family notation (`execl()`, `execv()`, `execvp()`) alongside `fork()` and `execve()`, explaining how `exec()` invokes the kernel's `execve()` system call to replace a child process's program while preserving its PID. | 2026-10-26 |
