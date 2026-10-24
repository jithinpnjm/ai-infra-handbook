---
id: "c04-04"
title: "4.4 YAML and Jinja2 for infrastructure code"
sidebar_label: "4.4 YAML and Jinja2 for infrastructure code"
sidebar_position: 4
description: "YAML syntax, types, anchors and pitfalls; Jinja2 expressions, filters, tests, control structures, whitespace control and macros; how Ansible, Helm, Kubernetes and Terraform use templating; validation and linting"
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP / GKE"
---

# 4.4 YAML and Jinja2 for infrastructure code

| | |
|---|---|
| Level | Beginner |
| Priority tier | 0 |
| Lab venue | Python 3.10+, `pip install jinja2 pyyaml yamllint ansible-core` |
| Part | Part 4: Automation and infrastructure as code |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Nearly every control surface in this handbook is YAML, JSON or a template of one: Ansible playbooks and inventories, Kubernetes manifests, Helm values and charts, Slurm and NCCL config generated from templates, GitHub Actions and GitLab CI pipelines, Prometheus rules, Docker Compose, cloud-init user data, Argo CD applications. Most production incidents "caused by automation" are really YAML mistakes (indentation, type coercion such as `no` becoming a boolean, a tab character) or template mistakes (undefined variables, wrong whitespace, an unescaped brace). Mastering YAML's data model and Jinja2's expression language removes a large class of errors and makes you faster at everything that follows.

## Prerequisites and outcomes

Basic scripting familiarity. After this chapter you can:

- Write correct YAML: scalars, sequences, mappings, multi-line strings, anchors/aliases/merge keys, multi-document files, comments, and avoid type-coercion traps.
- Convert between YAML and JSON mentally; validate with `yamllint`, schemas, and parsers.
- Use Jinja2: variables, expressions, filters, tests, conditionals, loops, macros, includes/inheritance, whitespace control and comments; know the difference between Jinja2 and Ansible-specific behaviour.
- Generate configuration files (Slurm, NCCL, chrony, netplan, Prometheus targets) from data with templates, and test templates offline.
- Recognise how Helm (Go templates), Terraform (HCL interpolation) and Kustomize differ, and pick the right tool.

## 1. YAML essentials

YAML ("YAML Ain't Markup Language") is a human-friendly serialisation format. It is a superset of JSON in practice (JSON is valid YAML 1.2), so `{"a": 1}` works anywhere YAML does. Everything is built from three structures:

| Structure | Syntax | JSON/Python equivalent |
|---|---|---|
| Scalar | `42`, `3.14`, `true`, `null`, `hello`, `"quoted"` | number, bool, null, string |
| Sequence (list) | `- item` on separate lines, or `[a, b]` | array / list |
| Mapping (dict) | `key: value` pairs, or `{a: 1, b: 2}` | object / dict |

```yaml
---                                # optional document start marker
cluster:
  name: ai-prod-1                  # mapping inside mapping
  racks: [r1, r2, r3]              # flow-style sequence
  nodes:                           # block-style sequence of mappings
    - name: gpu01
      gpus: 8
      tags: [h100, nvlink]
    - name: gpu02
      gpus: 8
      tags:
        - h100
  motd: |                          # literal block: newlines preserved
    Authorised use only.
    Contact: ops@example.com
  description: >                   # folded block: newlines become spaces
    A long description that
    wraps across lines.
  enabled: true
  contact: null
...                                # optional document end marker
```

### Rules that bite

- **Indentation is structure.** Spaces only, never tabs (a tab character is a parse error). Use two spaces consistently; sequences under a key may be indented or not (`key:\n- a` and `key:\n  - a` are both valid; pick one style).
- **A colon followed by a space** separates key and value. Values containing `: ` or ` #` must be quoted. A `#` preceded by a space starts a comment.
- **Quoting**: unquoted strings are parsed by type inference. Single quotes are literal (only `''` escapes a quote); double quotes support escapes (`\n`, `\t`, `é`). Use quotes whenever in doubt.
- **Type coercion traps** (YAML 1.1 parsers such as PyYAML, which Ansible uses): `yes`, `no`, `on`, `off`, `y`, `n` become booleans (the "Norway problem": country code `NO` becomes `false`); `1.10` becomes the float 1.1 (a version number lost its zero); `010` may be octal; `1e3` a float; `2024-01-15` a date object; `~` and empty values are null; `0.0.0.0` is a string but `1.2` is a float; a leading `0x` is hex; `:` times like `22:30` may parse as sexagesimal integers in 1.1. Quote versions, codes, IDs, modes (`mode: "0644"` or `0644` is octal in YAML 1.1 but many tools want a string; Ansible's own guidance is to quote file modes), and anything that must stay textual.
- **Strings starting with special characters** (asterisk, ampersand, exclamation mark, percent, at sign, backtick, braces, brackets, pipe, greater-than) must be quoted: `"{{ var }}"` in Ansible values that begin with a Jinja expression needs quotes because an opening brace starts a flow mapping.
- **Multi-line strings**: `|` keeps newlines (config files, scripts); `>` folds newlines to spaces; chomping indicators: `|-` strips the final newline, `|+` keeps all trailing newlines; an indentation indicator (`|2`) handles content that starts with spaces.
- **Duplicate keys** in a mapping: most parsers silently keep the last one, which hides copy-paste bugs; `yamllint` flags it (`key-duplicates`).
- **Multiple documents** in one file are separated by `---` (Kubernetes manifests and Helm output use this); a single parse call usually expects one document unless you use `yaml.safe_load_all`.
- **Security**: never use `yaml.load` on untrusted input (it can instantiate arbitrary Python objects); use `yaml.safe_load`. Anchors can be abused for "billion laughs" expansion in untrusted documents.

### Anchors, aliases and merge keys

Anchors (`&name`) mark a node; aliases (`*name`) reuse it; the merge key `<<` merges a mapping into another (a YAML 1.1 convention supported by PyYAML and Kubernetes tooling, but not part of the YAML 1.2 core and not honoured by every parser).

```yaml
defaults: &node_defaults
  gpus: 8
  os: ubuntu-22.04
  tags: [h100]

nodes:
  - name: gpu01
    <<: *node_defaults           # copy defaults
  - name: gpu02
    <<: *node_defaults
    gpus: 4                      # override
```

Anchors work inside a single file only (not across files) and make diffs harder to read when overused; CI definitions (GitLab `extends`, GitHub Actions reusable workflows) provide higher-level reuse.

### JSON, YAML and other formats

- Convert for inspection: `python3 -c 'import sys,yaml,json; print(json.dumps(yaml.safe_load(sys.stdin), indent=2))' < file.yml`; `yq` (mikefarah) and `jq` process YAML/JSON on the command line (`yq '.nodes[].name' nodes.yml`; `yq -o=json`; in-place edits with `yq -i`). Kubernetes accepts either.
- JSON has no comments and is stricter (good for machine exchange); YAML is better for human-edited configuration; TOML (Python tooling), HCL (Terraform), INI (ansible.cfg, systemd) are alternatives. Choose based on who edits the file.
- **Schema validation**: YAML has no built-in types, so validate with JSON Schema (`check-jsonschema`, `kubeconform` for Kubernetes, `pydantic` models in Python, Ansible argument specs for roles) and lint style with `yamllint`.

```yaml
# .yamllint
extends: default
rules:
  line-length: { max: 140, level: warning }
  truthy: { allowed-values: ["true", "false"] }     # flag yes/no/on/off
  indentation: { spaces: 2, indent-sequences: true }
  comments: { min-spaces-from-content: 2 }
  document-start: { present: false }
```

## 2. Jinja2 essentials

Jinja2 is a Python templating engine. Templates mix literal text with three kinds of delimiters:

| Delimiter | Purpose |
|---|---|
| `{{ expression }}` | Output the value of an expression |
| `{% statement %}` | Control flow: `if`, `for`, `set`, `macro`, `include`, `block` |
| `{# comment #}` | Comment (not rendered) |

Rendering = template + context (variables) = text. Ansible uses Jinja2 for variable interpolation in playbooks, conditionals and `template` files; Salt, Flask, dbt, Superset, Cookiecutter and many network-automation tools also use it. (Helm and Terraform do **not**; they use Go templates and HCL respectively.)

```python
from jinja2 import Environment, StrictUndefined
env = Environment(undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
tpl = env.from_string("""
{% for n in nodes %}
NodeName={{ n.name }} Gres=gpu:{{ n.gpus }} State=UNKNOWN
{% endfor %}
""")
print(tpl.render(nodes=[{"name": "gpu01", "gpus": 8}, {"name": "gpu02", "gpus": 8}]))
```

`StrictUndefined` makes a missing variable an error instead of an empty string: the single most useful safety setting (Ansible's default also errors on undefined variables unless you provide a `default`).

### Expressions

Variables and attribute access: `{{ cluster.name }}` (attribute then item), `{{ cluster['name'] }}`, `{{ list[0] }}`, `{{ list[-1] }}`, slices `{{ list[1:3] }}`. Literals: strings, numbers, `true`/`false` (Python's `True`/`False` also work), `none`, lists `[1, 2]`, dicts `{'a': 1}`, tuples. Operators: arithmetic `+ - * / // % **`, comparison `== != < > <= >=`, logic `and or not`, membership `in`, string concatenation `~` (preferred over `+` for strings), conditional expression `{{ 'a' if cond else 'b' }}`, test syntax `is`.

### Filters

A filter transforms a value: `{{ value | filter(args) }}`, chainable.

| Category | Filters |
|---|---|
| Strings | `upper`, `lower`, `title`, `trim`, `replace('a','b')`, `regex_replace` (Ansible), `split(',')`, `join(', ')`, `truncate`, `indent(4)`, `center`, `wordwrap`, `urlencode` |
| Defaults / safety | `default('x')`, `default('x', true)` (also for empty/falsy), `mandatory` (Ansible), `string`, `int`, `float`, `bool`, `abs`, `round` |
| Collections | `length`, `first`, `last`, `sort`, `unique`, `reverse`, `list`, `map(attribute='name')`, `select`, `reject`, `selectattr('gpus','gt',4)`, `rejectattr`, `groupby('rack')`, `sum`, `min`, `max`, `batch(3)`, `slice(3)` |
| Dict | `dictsort`, `items`, `dict2items`/`items2dict` (Ansible), `combine` (Ansible merge), `json_query` (JMESPath, Ansible) |
| Serialisation | `tojson`, `to_json`, `to_nice_json`, `to_yaml`, `to_nice_yaml`, `from_json`, `from_yaml` (Ansible), `b64encode`/`b64decode`, `hash('sha256')`, `password_hash` |
| Paths | `basename`, `dirname`, `expanduser`, `realpath`, `splitext` (Ansible) |
| Network (Ansible `ansible.utils`/`ansible.netcommon`) | `ipaddr`/`ansible.utils.ipaddr`, `ipv4`, `ipmath`, `cidr_merge`, `hwaddr`, `ansible.utils.next_nth_usable` |

```jinja
{{ nodes | map(attribute='name') | list }}                       {# ['gpu01', 'gpu02'] #}
{{ nodes | selectattr('gpus', 'ge', 8) | map(attribute='name') | join(',') }}   {# gpu01,gpu02 #}
{{ nodes | sum(attribute='gpus') }}                              {# total GPUs #}
{{ cluster.timeout | default(30) | int }}
{{ users | groupby('team') }}
{{ ports | join(',') }}
{{ config | to_nice_yaml(indent=2) }}
```

### Tests

`{% if value is test %}`: `defined`, `undefined`, `none`, `string`, `number`, `integer`, `mapping`, `iterable`, `sequence`, `even`, `odd`, `divisibleby(3)`, `equalto`, `in`, `lower`, `upper`, `callable`; Ansible adds `success`, `failed`, `changed`, `skipped`, `match`, `search`, `version('2.0', '>=')`, `subset`, `superset`, `contains`, `file`, `directory`, `exists`.

```jinja
{% if gpu_driver_version is version('550', '>=') %}...{% endif %}
{% if item is defined and item is not none %}...{% endif %}
{{ result is failed }}
```

### Control structures

```jinja
{% if node.role == 'compute' and node.gpus > 0 %}
  Gres=gpu:{{ node.gpus }}
{% elif node.role == 'login' %}
  # login node
{% else %}
  # other
{% endif %}

{% for rack, members in nodes | groupby('rack') %}
# rack {{ rack }}
{% for n in members | sort(attribute='name') %}
{{ n.name }}   {{ loop.index }}/{{ loop.length }}{{ ' first' if loop.first }}{{ ' last' if loop.last }}
{% else %}
(no nodes)
{% endfor %}
{% endfor %}

{% set total = nodes | sum(attribute='gpus') %}
{% set ns = namespace(count=0) %}
{% for n in nodes %}{% set ns.count = ns.count + n.gpus %}{% endfor %}   {# variable scoping workaround #}
```

`loop` variables: `index` (1-based), `index0`, `first`, `last`, `length`, `revindex`, `cycle('a','b')`, `previtem`, `nextitem`. Variables set inside a `for` are scoped to that loop; use `namespace` to carry values out. `{% for ... %}...{% else %}...{% endfor %}` runs the else block when the sequence is empty.

### Whitespace control

Templates that produce config files must control blank lines and indentation. Options: `{%-` and `-%}` strip whitespace before/after a tag; `trim_blocks=True` removes the first newline after a block tag; `lstrip_blocks=True` strips leading whitespace before a block tag. Ansible's `template` module sets `trim_blocks=True` by default (and `lstrip_blocks` is configurable via `jinja2_extensions`/`# jinja2:` header). A common idiom is a first-line override:

```jinja
#jinja2: trim_blocks:True, lstrip_blocks:True
# {{ ansible_managed }}
```

Always render and read the output; whitespace errors are invisible in the template and fatal in whitespace-sensitive output (YAML, Makefiles).

### Macros, includes, inheritance, raw blocks

```jinja
{% macro node_line(n, default_gpus=8) -%}
NodeName={{ n.name }} CPUs={{ n.cpus }} Gres=gpu:{{ n.gpus | default(default_gpus) }}
{%- endmacro %}

{% for n in nodes %}{{ node_line(n) }}
{% endfor %}

{% include 'header.j2' %}                       {# render another template with the same context #}
{% import 'macros.j2' as m %}{{ m.node_line(n) }}

{# inheritance: base.j2 defines {% block body %}{% endblock %}; child: {% extends 'base.j2' %} {% block body %}...{% endblock %} #}

{% raw %}{{ this is output literally }}{% endraw %}      {# to emit braces, e.g. Prometheus/Go templates #}
```

When a template must output literal `{{ }}` (Prometheus alert annotations, Helm templates, Grafana), wrap in `{% raw %}` or use `{{ '{{' }}`.

## 3. Jinja2 in Ansible

Ansible adds variables, filters and tests on top of Jinja2 and evaluates templates on the **control node**.

- **Where it applies**: task arguments, `vars`, `when` (the `when` expression is already a Jinja expression: write `when: ansible_distribution == 'Ubuntu'`, not `when: "{{ ... }}"`), `loop`, `failed_when`, `changed_when`, file contents via the `template` module (`src: nccl.conf.j2`), and inventory variables.
- **Quoting**: a YAML value that **starts** with `{{` must be quoted: `msg: "{{ var }}"`. Inside quotes you can mix: `path: "/data/{{ project }}/{{ env }}"`.
- **Undefined variables** error by default; use `{{ var | default('x') }}`, `{{ var | mandatory }}`, `is defined` checks, and `default(omit)` to drop an optional module parameter.
- **Types**: Ansible templating returns strings unless the value is a single native expression; booleans from `{{ }}` can arrive as strings (`"True"`). Use `| bool`, `| int`, and `when:` conditionals rather than string compares. `jinja2_native` can change this behaviour; test carefully.
- **Lookups and facts**: `lookup('env', 'HOME')`, `lookup('file', 'x')`, `lookup('pipe', 'cmd')` (control node), `query`, `hostvars['host']['ansible_default_ipv4']['address']`, `groups['gpu']`, `inventory_hostname`, `ansible_facts`, `play_hosts`.
- **`template` module**: `ansible.builtin.template` renders on the control node and copies the result; options `owner`, `group`, `mode`, `backup`, `validate: "visudo -cf %s"` (validate before installing, essential for sudoers, sshd, nginx), `variable_start_string` if you need different delimiters, and `{{ ansible_managed }}` for a "do not edit" header.

Example template for Slurm node definitions from inventory data:

```jinja
# {{ ansible_managed }}
{% for host in groups['gpu'] | sort %}
{% set h = hostvars[host] %}
NodeName={{ host }} NodeAddr={{ h.ansible_host }} CPUs={{ h.ansible_processor_vcpus }} RealMemory={{ (h.ansible_memtotal_mb * 0.95) | int }} Gres=gpu:{{ h.gpu_count | default(8) }} State=UNKNOWN
{% endfor %}
PartitionName=gpu Nodes={{ groups['gpu'] | join(',') }} Default=YES MaxTime=INFINITE State=UP
```

and NCCL environment from variables:

```jinja
# {{ ansible_managed }}
{% for k, v in (nccl_env | default({})) | dictsort %}
NCCL_{{ k | upper }}={{ v }}
{% endfor %}
```

with `nccl_env: { debug: WARN, ib_hca: "mlx5_0,mlx5_1", socket_ifname: eth0 }`.

## 4. Templating elsewhere (and how not to confuse them)

| Tool | Language | Notes |
|---|---|---|
| Ansible, Salt, Cookiecutter, dbt | Jinja2 | `{{ }}`, `{% %}`, filters |
| Helm | Go `text/template` + Sprig functions | `{{ .Values.image.tag \| quote }}`, `{{- if .Values.gpu }}`, `{{ include "chart.fullname" . }}`, `toYaml \| nindent 4`; whitespace trimmed with `{{-` and `-}}` |
| Terraform/OpenTofu | HCL expressions and `templatefile()` | `"${var.name}"`, `for` expressions, `%{ if }` directives |
| Kustomize | No templating; overlays, patches (JSON6902, strategic merge) | Declarative patching rather than templating |
| GitHub Actions | `${{ expression }}` | Different expression syntax and contexts |
| Docker Compose | `${VAR:-default}` variable substitution | Shell-like |
| cloud-init | Jinja2 optional header `## template: jinja` | Renders `{{ v1.local_hostname }}` instance data |
| Packer | HCL2 | `templatefile`, locals |
| Prometheus/Alertmanager | Go templates | `{{ $labels.instance }}`; conflicts with Jinja in Ansible-templated rule files; use `{% raw %}` |

Design guidance: **separate data from templates** (variables in inventory/vars files, logic-light templates), prefer declarative overlays (Kustomize) or typed config where possible, avoid templating a templating language (Helm values rendered by Jinja rendered by Terraform), and keep logic in code or modules, not in 200-line Jinja files. Generated YAML should be validated after rendering (`yamllint`, `kubeconform`, `kubectl --dry-run=server`).

## 5. Testing and debugging templates

- **Render offline** with the `jinja2` Python API and a fixtures file, or with Ansible: `ansible localhost -m ansible.builtin.template -a "src=nccl.conf.j2 dest=/tmp/out" -e @vars.yml --diff`; or a one-task playbook; or `ansible -m debug -a "msg={{ ... }}"` for expressions.
- **Golden-file tests**: render with representative data (including empty lists and missing optional keys) and compare with an expected file (see 3.9 testing patterns); snapshot tests catch accidental whitespace changes.
- **Validate the output** with the target's own parser: `nginx -t`, `visudo -cf`, `sshd -t`, `slurmd -C`/`scontrol` checks, `kubeconform`, `promtool check rules`, `python -c 'import yaml; yaml.safe_load(...)'`.
- **Debug** with `{{ var | to_nice_json }}` in `debug` tasks, `ansible-playbook -vvv`, and `ansible-inventory --host name` to view merged variables. For undefined errors read the exact variable name and precedence layer (4.7).
- **Common failure messages**: `AnsibleUndefinedVariable: 'x' is undefined`, `template error while templating string: unexpected '}'` (unbalanced braces or YAML flow mapping confusion), `mapping values are not allowed here` (YAML colon in unquoted string), `found character '\t' that cannot start any token` (tab), `did not find expected key` (indentation), `The task includes an option with an undefined variable`.
- **Performance**: heavy Jinja in loops over thousands of hosts is slow; precompute with `set_fact` or filters, avoid `lookup('pipe')` per host in large loops, and keep templates simple.

## 6. Security considerations

- Untrusted data in templates: never render user-provided strings as templates (server-side template injection); Ansible marks values from facts as "unsafe" to prevent re-templating; avoid `!unsafe` removal and `eval`-like constructs.
- Secrets in rendered files: set `mode: "0600"`, `owner`, `no_log: true` on tasks that render secrets, and avoid putting secrets in `--diff` output (`diff: false`).
- Quote shell interpolation (`| quote` filter) when templating values into shell commands.
- Use `yaml.safe_load`; pin and review parsers in tooling.

## 7. Lab (untested)

1. **YAML traps**: parse a file containing `no`, `yes`, `1.10`, `010`, `22:30`, `2024-01-01`, `~`, `0x1f`, `"quoted"` with PyYAML and print Python types; then quote each correctly; run `yamllint` with the `truthy` rule.
2. **Anchors and merge**: build the node defaults file; load with PyYAML and with `yq`; show a parser that ignores `<<`; refactor to explicit inheritance in code.
3. **Multi-line strings**: write `|`, `>`, `|-`, `>+` blocks and print repr to see newlines; embed a script and a systemd unit in YAML.
4. **Jinja basics**: render the Slurm node template from a Python script using `StrictUndefined`; remove a variable and observe the error; compare behaviour without `StrictUndefined`.
5. **Filters**: from a nodes list produce (a) comma-joined names with 8 GPUs, (b) total GPUs, (c) nodes grouped by rack, (d) a YAML dump with `to_nice_yaml`.
6. **Whitespace**: render the same loop with and without `trim_blocks`, `lstrip_blocks` and `{%-`; diff the outputs; fix a template that emits blank lines in the middle of a config file.
7. **Macros and includes**: factor repeated stanzas; test `{% raw %}` by templating a Prometheus alert rule that contains Go template syntax.
8. **Ansible templating**: write `nccl.conf.j2`, render with the `template` module, `--diff`, `--check`, `validate:` using a custom validator command; show `default(omit)` skipping an optional parameter; reproduce the YAML error from an unquoted `{{ }}` value.
9. **Types in Ansible**: demonstrate a boolean arriving as the string `"False"` and fix with `| bool`; compare `when: var` versus `when: var | bool`.
10. **Cross-tool**: write the same service config as a Jinja2 template (Ansible), a Helm template and a Kustomize patch; list when each is preferable.
11. **Validation pipeline**: add `yamllint`, `check-jsonschema` (or `kubeconform`), and a golden-file render test to pre-commit/CI.
12. **Clean up.**

Mark tested only after execution.

## 8. Common mistakes

- Tabs in YAML; inconsistent indentation; mixing list styles that confuse readers.
- Unquoted values that YAML reinterprets (`NO`, `1.10`, `yes`, times, leading zeros); unquoted `{{ var }}` at the start of a value.
- `when: "{{ var }}"` (double templating) instead of `when: var`.
- Relying on undefined variables silently rendering as empty strings.
- Templates with extensive logic and nested loops that nobody can review; templating generated templates.
- Whitespace bugs in generated config because output was never inspected.
- Forgetting `{% raw %}` when templating Go-template or Jinja-in-Jinja content.
- Using `yaml.load` on untrusted data; rendering untrusted strings as templates.
- Anchors across files (unsupported) or overused merge keys that hide the effective configuration.
- No validation of rendered output before deployment.

## 9. Interview angles

- "What are YAML's gotchas? Give examples of values that change type." (Norway problem, versions, octal.)
- "Difference between `|` and `>` block scalars?" 
- "How do you reuse YAML sections? What are the limits of anchors?"
- "Explain Jinja2 statements, expressions and comments; how does Ansible use them?"
- "How do you iterate over inventory hosts to build a config file? How do you avoid blank lines?" 
- "`default`, `mandatory`, `omit`: when each?"
- "How do you test and validate templates?" 
- "Helm vs Jinja2 vs Kustomize vs Terraform templatefile: differences and when to choose each?"
- "Why is `yaml.load` dangerous?"

## 10. Checkpoint questions (35)

1. Is JSON valid YAML? **A:** Yes (YAML 1.2 superset in practice).
2. YAML's three basic structures? **A:** Scalars, sequences, mappings.
3. Can YAML use tabs for indentation? **A:** No.
4. Why quote `"1.10"`? **A:** Else parsed as float 1.1.
5. What is the Norway problem? **A:** `NO` parsed as boolean false.
6. `|` versus `>`? **A:** Preserve vs fold newlines.
7. What does `|-` do? **A:** Strips the final newline.
8. What is `&` / `*` / `<<`? **A:** Anchor, alias, merge key.
9. Do anchors work across files? **A:** No.
10. Why `safe_load`? **A:** `load` can construct arbitrary objects.
11. Tool to lint YAML? **A:** `yamllint`.
12. Tool to validate Kubernetes YAML against schemas? **A:** `kubeconform`.
13. Jinja2 expression delimiter? **A:** `{{ }}`.
14. Statement delimiter? **A:** `{% %}`.
15. Comment delimiter? **A:** `{# #}`.
16. What does `StrictUndefined` do? **A:** Errors on undefined variables.
17. String concatenation operator? **A:** `~`.
18. What does `{{ x | default('a', true) }}` add? **A:** Also replaces empty/falsy values.
19. Filter to extract an attribute list? **A:** `map(attribute='name')`.
20. Filter for conditional selection? **A:** `selectattr` / `select`.
21. What do `trim_blocks`/`lstrip_blocks` do? **A:** Remove newline/indent around block tags.
22. How to carry a counter out of a loop? **A:** `namespace`.
23. How to output literal braces? **A:** `{% raw %}` blocks.
24. Is `when:` templated with `{{ }}`? **A:** No; it is already an expression.
25. Why quote `"{{ var }}"` in YAML? **A:** `{` starts a flow mapping.
26. What does `default(omit)` do? **A:** Drops an optional module parameter.
27. What does the `template` module's `validate:` do? **A:** Checks the rendered file before installing.
28. Where does templating run in Ansible? **A:** On the control node.
29. What is `ansible_managed`? **A:** Header string marking generated files.
30. Helm's template language? **A:** Go templates with Sprig.
31. Terraform's templating function? **A:** `templatefile()`.
32. Tool that patches without templating? **A:** Kustomize.
33. How to see merged host variables? **A:** `ansible-inventory --host name`.
34. Risk of rendering user input as template? **A:** Template injection.
35. How to avoid secrets in diff output? **A:** `diff: false` / `no_log: true`.

## 11. Sources and review notes

**Written in original words.** Principal sources:

- Rene Moser and Lorin Hochstein, *Ansible: Up and Running*, 3rd edition (chapter 3 on inventory/YAML syntax and Jinja2 templating in playbooks, and templates in chapter 6).
- The YAML specification and PyYAML behaviour (YAML 1.1 type resolution), Jinja2 documentation (templates, filters, tests, whitespace control), Ansible templating documentation, Helm and Terraform template documentation.
- Examples are the author's constructions.

**Flagged for verification before publishing:** Ansible-specific filter and test names against the collection versions in use (several moved to `ansible.utils`/`community.general`), `jinja2_native` and default whitespace settings in the Ansible version used, `yamllint` rule names, and every code listing; all labs are **untested**.
