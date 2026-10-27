"""Chapter 4.21 model: `count` index-shift churn vs `for_each` key stability
when removing an element from the middle of a list (`["neo", "trinity",
"morpheus"]`, `TUR` Ch. 5), `one(concat(...))` safe conditional output selector,
and nested `(team, namespace)` map flattening (`Section 9`).

Sources modeled:
- Yevgeniy Brikman, Terraform: Up and Running, 3rd ed. (terraform-up-and-running-
  3rd-edition, TUR), Chapter 5 ("Terraform Tips and Tricks: Loops, If-Statements,
  Deployment, and Gotchas"):
  * Four looping constructs: `count`, `for_each` (over resources, modules, and
    `dynamic` blocks, plus `provider "aws" { default_tags { ... } }`), `for`
    list/map expressions, and string directives (`%{~ for i, name in var.names ~}`
    + `%{ if ... }`).
  * `count` index-shift trap on `["neo", "trinity", "morpheus"]` when `"trinity"`
    is removed vs `for_each = toset(var.user_names)`.
  * Conditionals with `count = cond ? 1 : 0` and if-else with
    `one(concat(full[*].policy_arn, read_only[*].policy_arn))` avoiding `[0]`
    index-out-of-range errors.
  * Zero-downtime ASG deployments: `create_before_destroy` + `min_elb_capacity`
    vs native `instance_refresh` (`strategy = "Rolling"`,
    `min_healthy_percentage = 50`).
- volume-10/05-terraform-for-infrastructure-as-code.md.
"""
from typing import Any, Dict, List, Mapping, Sequence


def simulate_count_vs_for_each_removal(
    before_names: Sequence[str],
    after_names: Sequence[str],
) -> Dict[str, List[str]]:
    """Compare Terraform plan actions when removing an item from `before_names`
    under `count = length(var.names)` (indexed `0..N-1`) vs `for_each = toset(var.names)`
    (keyed by string name).
    """
    # 1. count: state maps index -> name
    count_state = {idx: name for idx, name in enumerate(before_names)}
    count_desired = {idx: name for idx, name in enumerate(after_names)}
    count_actions: List[str] = []
    for idx in sorted(set(count_state.keys()) | set(count_desired.keys())):
        if idx in count_state and idx not in count_desired:
            count_actions.append(f"destroy [{idx}] ({count_state[idx]})")
        elif idx in count_state and idx in count_desired and count_state[idx] != count_desired[idx]:
            count_actions.append(f"modify/replace [{idx}] ({count_state[idx]} -> {count_desired[idx]})")

    # 2. for_each: state maps name -> name
    fe_state = set(before_names)
    fe_desired = set(after_names)
    fe_actions: List[str] = [f"destroy [{name!r}]" for name in sorted(fe_state - fe_desired)]

    return {
        "count_actions": count_actions,
        "for_each_actions": fe_actions,
    }


def evaluate_one_concat_conditional(give_full_access: bool, full_arn: str, read_only_arn: str) -> str | None:
    """Model TUR Ch. 5 `one(concat(full_access[*].policy_arn, read_only[*].policy_arn))`."""
    full_list = [full_arn] if give_full_access else []
    ro_list = [] if give_full_access else [read_only_arn]
    combined = full_list + ro_list
    if not combined:
        return None
    if len(combined) == 1:
        return combined[0]
    raise ValueError(f"one() expected at most 1 element, got {len(combined)}")


def flatten_team_namespaces(teams: Mapping[str, Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Model Section 9 `merge([for team, cfg in var.teams : { for ns in cfg.namespaces : ... }]...)`."""
    flat: Dict[str, Dict[str, Any]] = {}
    for team, cfg in sorted(teams.items()):
        quota = int(cfg["gpu_quota"])
        for ns in cfg.get("namespaces", ()):
            flat[f"{team}/{ns}"] = {"team": team, "ns": ns, "quota": quota}
    return flat
