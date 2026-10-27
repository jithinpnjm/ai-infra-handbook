#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.1: Git from scratch for infrastructure engineers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from git_infrastructure_workflow import (
    build_git_commit_dag,
    git_hash_object,
    resolve_codeowners,
    simulate_git_bisect_run,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Section 2 Git object model: blob SHA-1 reuse on rename and Merkle DAG parent chaining
    dag = build_git_commit_dag()
    check(
        "renaming main.tf to providers.tf reuses the exact same blob SHA-1 while producing new tree and commit SHA-1s",
        dag["blob_sha"] == dag["blob_renamed_sha"]
        and len(dag["blob_sha"]) == 40
        and dag["tree1_sha"] != dag["tree2_sha"]
        and dag["commit1_sha"] != dag["commit2_sha"],
    )

    # 2. Verify canonical Git blob SHA-1 header format (`blob <len>\0<content>`)
    hello_sha = git_hash_object("blob", b"hello\n")
    check(
        "git_hash_object('blob', b'hello\\n') matches Git's canonical SHA-1 ce013625030ba8dba906f756967f9e9ca394464a",
        hello_sha == "ce013625030ba8dba906f756967f9e9ca394464a",
    )

    # 3. Section 12 CODEOWNERS last-matching-pattern evaluation
    rules = [
        ("*", "@org/sre"),
        ("/terraform/network/", "@org/network-team"),
        ("/ansible/roles/gpu_*", "@org/hpc-team"),
        ("/k8s/", "@org/mlops"),
    ]
    check(
        "CODEOWNERS assigns @org/network-team to /terraform/network/vpc.tf, @org/hpc-team to gpu_driver, and @org/sre default",
        resolve_codeowners(rules, "/terraform/network/vpc.tf") == "@org/network-team"
        and resolve_codeowners(rules, "/ansible/roles/gpu_driver/tasks/main.yml") == "@org/hpc-team"
        and resolve_codeowners(rules, "/README.md") == "@org/sre",
    )

    # 4. Section 8 & 15 git bisect binary search (locating regression at commit 27 out of 40 in <= 6 steps)
    found, steps = simulate_git_bisect_run(num_commits=40, first_bad_commit=27)
    check(
        "git bisect binary search locates regression at commit 27 out of 40 in 5 steps (<= log2(40))",
        found == 27 and len(steps) <= 6,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
