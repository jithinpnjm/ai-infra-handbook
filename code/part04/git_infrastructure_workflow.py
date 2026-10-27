"""Chapter 4.1 model: Git content-addressed object store (`blob`, `tree`,
`commit` SHA-1 hashing and Merkle DAG verification), CODEOWNERS last-matching-
pattern rule evaluation, and automated `git bisect run` binary search.

Sources modeled:
- Christian Adell, Scott Lowe, Matt Oswalt & Jason Edelman, Network
  Programmability and Automation, 2nd ed. (network-programmability-and-automation-
  2nd-edition, NPA):
  * Chapter 5 ("Network Developer Environments"): editors/LSP, Docker/Compose,
    `dyff between -b before.yaml after.yaml`, Vagrant (`Vagrantfile` 3-router
    `vyos/current` topology + Ansible provisioner), and Containerlab
    (`topology1.clab.yaml` Nokia SR Linux `ghcr.io/nokia/srlinux` `srl01`/`srl02`).
  * Chapter 11 ("Source Control with Git"): Linus Torvalds 2005 BitKeeper history,
    working directory vs index (`.git/index`) vs repository (`.git/objects`,
    `.git/refs/heads/`, 41-byte branch ref files), `git init`, `git add`,
    `git commit`, `--amend`, `.gitignore` (`credentials.yml` exclusion),
    lightweight vs annotated tags (`git tag -a v1.0`), branching & fast-forward
    vs three-way merges, conflict resolution (`<<<<<<<`, `=======`, `>>>>>>>`),
    `git stash` (`stash@{0}`), remotes (`origin`, `git clone --bare`),
    `git fetch` + `git diff main..origin/main` vs `git pull`, and forks/PRs.
- volume-10/17-git-for-infrastructure-and-operations.md.
"""
import hashlib
from typing import Callable, Dict, List, Optional, Sequence, Tuple


def git_hash_object(obj_type: str, content: bytes) -> str:
    """Compute the exact Git SHA-1 object ID for `<type> <size>\\0<content>`."""
    header = f"{obj_type} {len(content)}\x00".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def build_git_commit_dag() -> Dict[str, str]:
    """Build a 2-commit Merkle DAG and verify that renaming a file reuses the
    exact same blob SHA-1 while changing the tree and commit SHA-1s.
    """
    blob_bytes = b'provider "google" {}\n'
    blob_sha = git_hash_object("blob", blob_bytes)

    tree1_content = f"100644 main.tf\x00{blob_sha}".encode("ascii")
    tree1_sha = git_hash_object("tree", tree1_content)
    commit1_body = f"tree {tree1_sha}\nauthor Jane <jane@example.com>\n\nAdd provider stub\n".encode("utf-8")
    commit1_sha = git_hash_object("commit", commit1_body)

    # Renaming main.tf -> providers.tf keeps the exact same blob_sha!
    blob_renamed_sha = git_hash_object("blob", blob_bytes)
    tree2_content = f"100644 providers.tf\x00{blob_renamed_sha}".encode("ascii")
    tree2_sha = git_hash_object("tree", tree2_content)
    commit2_body = (
        f"tree {tree2_sha}\nparent {commit1_sha}\nauthor Jane <jane@example.com>\n\nRename to providers.tf\n"
    ).encode("utf-8")
    commit2_sha = git_hash_object("commit", commit2_body)

    return {
        "blob_sha": blob_sha,
        "blob_renamed_sha": blob_renamed_sha,
        "tree1_sha": tree1_sha,
        "tree2_sha": tree2_sha,
        "commit1_sha": commit1_sha,
        "commit2_sha": commit2_sha,
    }


def resolve_codeowners(rules: Sequence[Tuple[str, str]], path: str) -> str:
    """Evaluate .github/CODEOWNERS where the LAST matching pattern wins."""
    owner = ""
    for pattern, team in rules:
        if pattern == "*":
            owner = team
        elif pattern.endswith("/*") or pattern.endswith("_*"):
            prefix = pattern[:-1]
            if path.startswith(prefix):
                owner = team
        elif pattern.endswith("/"):
            if path.startswith(pattern):
                owner = team
        elif path == pattern:
            owner = team
    return owner


def simulate_git_bisect_run(
    num_commits: int,
    first_bad_commit: int,
) -> Tuple[int, List[int]]:
    """Simulate `git bisect run` binary search over commits `0..num_commits-1`
    where `0` is known good and `num_commits-1` is known bad.
    Returns `(found_bad_commit, tested_commits)`.
    """
    low = 0
    high = num_commits - 1
    tested: List[int] = []
    while low + 1 < high:
        mid = (low + high) // 2
        tested.append(mid)
        exit_code = 1 if mid >= first_bad_commit else 0
        if exit_code == 0:
            low = mid
        else:
            high = mid
    return high, tested
