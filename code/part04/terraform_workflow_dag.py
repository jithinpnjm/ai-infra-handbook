"""Chapter 4.18 model: Declarative `terraform plan` action classifier (`create`,
`update`, `replace -/+`, `replace +/- create_before_destroy`, `destroy`, and
`moved` refactoring), implicit/explicit dependency DAG wave builder, and
pessimistic version constraint (`~>`) evaluator.

Sources modeled:
- Yevgeniy Brikman, Terraform: Up and Running, 3rd ed. (terraform-up-and-running-
  3rd-edition, TUR), Chapters 1 & 2:
  * Chapter 1 ("Why Terraform"): 5 categories of IaC tools (ad-hoc scripts,
    configuration management, server templating, orchestration, provisioning),
    6 trade-off axes (configuration management vs provisioning, mutable vs
    immutable, procedural vs declarative `count = 10 -> 15 -> 5` EC2 example,
    GPL vs DSL, master vs masterless, agent vs agentless).
  * Chapter 2 ("Getting Started with Terraform"): `aws_instance` (`user_data`
    `<<-EOF`, `user_data_replace_on_change = true`), `aws_security_group`,
    `variable "server_port"` & `output`, `data "aws_vpc" "default"` &
    `data "aws_subnets" "default"`, `aws_launch_configuration` +
    `aws_autoscaling_group` requiring `lifecycle { create_before_destroy = true }`,
    and `aws_lb` + `aws_lb_listener` + `aws_lb_target_group` +
    `aws_lb_listener_rule` (`terraform graph` DOT DAG).
- volume-10/05-terraform-for-infrastructure-as-code.md.
"""
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


def compute_terraform_plan_actions(
    state_resources: Mapping[str, Mapping[str, Any]],
    desired_resources: Mapping[str, Mapping[str, Any]],
    immutable_attrs: Set[str],
    create_before_destroy_addrs: Set[str] | None = None,
    moved_blocks: Mapping[str, str] | None = None,
) -> Dict[str, str]:
    """Model Section 1, 4, 5 & TUR Ch. 2 `terraform plan` action symbols:
    - `+` ('create')
    - `~` ('update_in_place')
    - `-/+` ('replace_destroy_first')
    - `+/-` ('replace_create_first' when `create_before_destroy = true`)
    - `-` ('destroy')
    - 'moved_no_op' (when a `moved { from = old, to = new }` block rebinds state)
    """
    cbd = create_before_destroy_addrs or set()
    moves = moved_blocks or {}

    # Apply `moved` state address rebindings first
    effective_state: Dict[str, Mapping[str, Any]] = {}
    moved_targets: Set[str] = set()
    for addr, attrs in state_resources.items():
        if addr in moves:
            new_addr = moves[addr]
            effective_state[new_addr] = attrs
            moved_targets.add(new_addr)
        else:
            effective_state[addr] = attrs

    plan: Dict[str, str] = {}
    all_addrs = sorted(set(effective_state.keys()) | set(desired_resources.keys()))
    for addr in all_addrs:
        in_state = addr in effective_state
        in_desired = addr in desired_resources
        if not in_state and in_desired:
            plan[addr] = "create (+)"
        elif in_state and not in_desired:
            plan[addr] = "destroy (-)"
        else:
            old_a = effective_state[addr]
            new_a = desired_resources[addr]
            if old_a == new_a:
                plan[addr] = "moved_no_op" if addr in moved_targets else "no_op"
            else:
                changed_keys = {k for k in (set(old_a.keys()) | set(new_a.keys())) if old_a.get(k) != new_a.get(k)}
                if changed_keys & immutable_attrs:
                    plan[addr] = "replace_create_first (+/-)" if addr in cbd else "replace_destroy_first (-/+)"
                else:
                    plan[addr] = "update_in_place (~)"
    return plan


def build_dependency_execution_waves(deps: Mapping[str, Sequence[str]]) -> List[List[str]]:
    """Compute parallel execution waves from a Terraform resource dependency DAG
    (`node -> list of nodes it depends on`). Raises ValueError on dependency cycles.
    """
    remaining: Dict[str, Set[str]] = {node: set(d) for node, d in deps.items()}
    waves: List[List[str]] = []
    while remaining:
        ready = sorted(n for n, d in remaining.items() if not d)
        if not ready:
            raise ValueError(f"dependency cycle detected among {sorted(remaining.keys())}")
        waves.append(ready)
        for r in ready:
            del remaining[r]
        for d in remaining.values():
            d.difference_update(ready)
    return waves


def matches_pessimistic_constraint(constraint: str, version: str) -> bool:
    """Model Section 3 `~>` pessimistic version constraint:
    - `~> 5.30` allows `>= 5.30.0, < 6.0.0`
    - `~> 5.30.1` allows `>= 5.30.1, < 5.31.0`
    """
    if not constraint.startswith("~>"):
        raise ValueError(f"expected '~>' constraint, got {constraint!r}")
    c_parts = [int(x) for x in constraint[2:].strip().split(".")]
    v_parts = [int(x) for x in version.strip().split(".")]
    while len(v_parts) < 3:
        v_parts.append(0)
    if len(c_parts) == 2:
        min_v = (c_parts[0], c_parts[1], 0)
        max_v = (c_parts[0] + 1, 0, 0)
    elif len(c_parts) == 3:
        min_v = (c_parts[0], c_parts[1], c_parts[2])
        max_v = (c_parts[0], c_parts[1] + 1, 0)
    else:
        raise ValueError(f"invalid constraint {constraint!r}")
    vt = (v_parts[0], v_parts[1], v_parts[2])
    return min_v <= vt < max_v
