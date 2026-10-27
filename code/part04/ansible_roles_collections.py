"""Chapter 4.11 model: Ansible role `meta/argument_specs.yml` validator,
role file/template search path resolver (`AUR` Ch. 9), and role dependency
graph & deduplication order (`allow_duplicates: false` vs `true`).

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapters 9 & 15:
  * Chapter 9 ("Roles: Scaling Up Your Playbooks"): Structure of `database` and
    `mezzanine` roles (`tasks/`, `handlers/`, `defaults/`, `vars/`, `files/`,
    `templates/`, `meta/`), `defaults/main.yml` vs `vars/main.yml` (computed
    internal variables), `copy` / `script` / `template` relative path search
    order inside a role (`./roles/<role>/files/`, `./roles/<role>/`,
    `./roles/<role>/tasks/files/`, `./roles/<role>/tasks/`, `./files/`, `./`),
    `pre_tasks` and `post_tasks` around `roles:`, `ansible-galaxy init`,
    `ansible-galaxy install -r roles/requirements.yml` (`oefenweb.ntp` `v1.1.33`,
    `geerlingguy.docker`), and `meta/main.yml` `dependencies:`.
  * Chapter 15 ("Collections"): `namespace.collection.module` / `role` FQCNs,
    `requirements.yml` with both `roles:` and `collections:`, play-level
    `collections:` keyword, and `ansible-galaxy collection init` -> `build` ->
    `install -p ./collections` -> `publish`.
"""
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def validate_role_argument_spec(
    spec_options: Mapping[str, Mapping[str, Any]],
    provided_vars: Mapping[str, Any],
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Model Section 1 `meta/argument_specs.yml` runtime validation."""
    errors: List[str] = []
    effective: Dict[str, Any] = {}

    type_map = {"str": str, "int": int, "bool": bool, "list": list, "dict": dict}

    for opt_name, rules in spec_options.items():
        if opt_name in provided_vars:
            val = provided_vars[opt_name]
        elif "default" in rules:
            val = rules["default"]
        elif rules.get("required", False):
            errors.append(f"missing required argument: {opt_name}")
            continue
        else:
            continue

        expected_type_name = rules.get("type", "str")
        py_type = type_map.get(expected_type_name, object)
        # Note: in Python bool is a subclass of int, so exclude bool when checking int
        if expected_type_name == "int" and isinstance(val, bool):
            errors.append(f"{opt_name}: expected int, got bool")
            continue
        if not isinstance(val, py_type):
            errors.append(f"{opt_name}: expected {expected_type_name}, got {type(val).__name__}")
            continue

        choices = rules.get("choices")
        if choices is not None and val not in choices:
            errors.append(f"{opt_name}: value {val!r} not in choices {choices}")
            continue

        effective[opt_name] = val

    return (len(errors) == 0), errors, effective


def resolve_role_dependency_order(
    root_roles: Sequence[str],
    deps_map: Mapping[str, Sequence[str]],
    allow_duplicates: Mapping[str, bool] | None = None,
) -> List[str]:
    """Model Section 1 & AUR Ch. 9 `meta/main.yml` `dependencies:` execution order:
    dependencies run BEFORE the role that depends on them, and run only ONCE per
    play unless `allow_duplicates: true` is set on the dependency role.
    """
    allow_dups = allow_duplicates or {}
    order: List[str] = []

    def _visit(role: str) -> None:
        if role in order and not allow_dups.get(role, False):
            return
        for dep in deps_map.get(role, ()):
            _visit(dep)
        if role not in order or allow_dups.get(role, False):
            order.append(role)

    for r in root_roles:
        _visit(r)
    return order


def role_file_search_candidates(role_name: str, filename: str, module_subdir: str = "files") -> List[str]:
    """Model AUR Ch. 9 relative file search order when `copy` (`files`),
    `template` (`templates`), or `script` (`files`) is called inside a role.
    """
    return [
        f"./roles/{role_name}/{module_subdir}/{filename}",
        f"./roles/{role_name}/{filename}",
        f"./roles/{role_name}/tasks/{module_subdir}/{filename}",
        f"./roles/{role_name}/tasks/{filename}",
        f"./{module_subdir}/{filename}",
        f"./{filename}",
    ]
