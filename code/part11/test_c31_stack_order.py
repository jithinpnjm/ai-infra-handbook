from pathlib import Path

import pytest

import c31_stack_order as so

HERE = Path(__file__).parent


def test_sample_recipe_orders_and_passes_rules():
    graph = so.load_components(HERE / "c31_recipe_dynamo_inference.yaml")
    order = so.install_order(graph)
    assert set(order) == set(graph)
    for name, deps in graph.items():
        for dep in deps:
            assert order.index(dep) < order.index(name)
    assert order[-1] == "dynamo-platform"
    assert so.rule_violations(graph) == []


def test_missing_dependency_is_rejected():
    with pytest.raises(so.RecipeError, match="not in the recipe"):
        so.install_order({"grove": ["prometheus-operator-crds"]})


def test_cycle_is_rejected():
    with pytest.raises(so.RecipeError, match="cycle"):
        so.install_order({"a": ["b"], "b": ["a"], "c": []})


def test_rule_catches_dynamo_without_kai():
    graph = {
        "cert-manager": [],
        "gpu-operator": ["cert-manager"],
        "grove": [],
        "dynamo-platform": ["grove", "gpu-operator", "cert-manager"],
    }
    assert "dynamo-platform must come after kai-scheduler" in so.rule_violations(graph)


def test_rule_accepts_transitive_prior():
    graph = {
        "cert-manager": [],
        "gpu-operator": ["cert-manager"],
        "nvsentinel": ["gpu-operator"],
    }
    assert so.rule_violations(graph) == []


def test_duplicate_component_rejected(tmp_path):
    p = tmp_path / "r.yaml"
    p.write_text(
        "spec:\n  componentRefs:\n    - name: a\n    - name: a\n"
    )
    with pytest.raises(so.RecipeError, match="duplicate"):
        so.load_components(p)
