#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.18: Terraform refresher: why, providers, resources and the workflow."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terraform_workflow_dag import (
    build_dependency_execution_waves,
    compute_terraform_plan_actions,
    matches_pessimistic_constraint,
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
    # 1. Section 1, 4, 5 & TUR Ch. 2: Plan actions (+, ~, -/+, +/-, -, and moved refactoring)
    state = {
        "aws_instance.web": {"ami": "ami-1", "tags": {"env": "stage"}},
        "aws_launch_configuration.asg": {"image_id": "ami-1", "instance_type": "t2.micro"},
        "google_compute_network.fabric": {"mtu": 8896},
        "aws_instance.obsolete": {"ami": "ami-1"},
    }
    desired = {
        "aws_instance.web": {"ami": "ami-1", "tags": {"env": "prod"}},  # mutable tag update (~)
        "aws_launch_configuration.asg": {"image_id": "ami-2", "instance_type": "t2.micro"},  # immutable image_id with CBD (+/-)
        "module.network.google_compute_network.this": {"mtu": 8896},  # moved without recreate
        "aws_instance.new_gpu": {"ami": "ami-gpu"},  # created (+)
    }
    plan = compute_terraform_plan_actions(
        state_resources=state,
        desired_resources=desired,
        immutable_attrs={"ami", "image_id", "zone"},
        create_before_destroy_addrs={"aws_launch_configuration.asg"},
        moved_blocks={"google_compute_network.fabric": "module.network.google_compute_network.this"},
    )
    check(
        "compute_terraform_plan_actions classifies +, ~, +/-, -, and moved_no_op accurately",
        plan["aws_instance.web"] == "update_in_place (~)"
        and plan["aws_launch_configuration.asg"] == "replace_create_first (+/-)"
        and plan["module.network.google_compute_network.this"] == "moved_no_op"
        and plan["aws_instance.new_gpu"] == "create (+)"
        and plan["aws_instance.obsolete"] == "destroy (-)",
    )

    # 2. Section 1, 2 & TUR Ch. 2: Dependency DAG execution waves
    dag = {
        "google_compute_network.fabric": [],
        "data.google_compute_image.ubuntu": [],
        "google_compute_subnetwork.compute": ["google_compute_network.fabric"],
        "google_compute_firewall.internal": ["google_compute_network.fabric"],
        "google_compute_instance.gpu": ["google_compute_subnetwork.compute", "data.google_compute_image.ubuntu"],
    }
    waves = build_dependency_execution_waves(dag)
    check(
        "build_dependency_execution_waves orders VPC+image in wave 1, subnet+firewall in wave 2, and GPU VM in wave 3",
        waves
        == [
            ["data.google_compute_image.ubuntu", "google_compute_network.fabric"],
            ["google_compute_firewall.internal", "google_compute_subnetwork.compute"],
            ["google_compute_instance.gpu"],
        ],
    )

    # 3. Section 3: Pessimistic version constraints (~> 5.30 vs ~> 5.30.1)
    check(
        "matches_pessimistic_constraint enforces '~> 5.30' (>=5.30.0, <6.0.0) and '~> 5.30.1' (>=5.30.1, <5.31.0)",
        matches_pessimistic_constraint("~> 5.30", "5.42.0") is True
        and matches_pessimistic_constraint("~> 5.30", "6.0.0") is False
        and matches_pessimistic_constraint("~> 5.30.1", "5.30.9") is True
        and matches_pessimistic_constraint("~> 5.30.1", "5.31.0") is False,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
