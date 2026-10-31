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

Almost every control surface in this handbook is YAML, JSON or a template that produces one. That covers Ansible playbooks and inventories, Kubernetes manifests, Helm values and charts, Slurm and NCCL config generated from templates, GitHub Actions and GitLab CI pipelines, Prometheus rules, Docker Compose, cloud-init user data and Argo CD applications. When one of these files misbehaves, the cause is usually small. Most production incidents blamed on automation are really YAML mistakes, such as bad indentation, a type change like `no` becoming a boolean, or a tab character. The rest are template mistakes: an undefined variable, wrong whitespace or an unescaped brace. Learning YAML's data model and Jinja2's expression language removes a large class of these errors. It also makes you faster at everything that follows.

## Prerequisites and outcomes

You need only basic scripting familiarity to follow this chapter. By the end, you should be able to write correct YAML. That includes scalars, sequences, mappings, multi-line strings, anchors, aliases and merge keys, multi-document files and comments, all without falling into type-coercion traps. You should be able to move between YAML and JSON in your head. You should also check a file with `yamllint`, schemas and parsers.

On the template side, you will work with Jinja2 variables, expressions, filters, tests, conditionals, loops, macros, includes, inheritance, whitespace control and comments. You will know where Jinja2 ends and Ansible-specific behaviour begins. Finally, you will generate configuration files for Slurm, NCCL, chrony, netplan and Prometheus targets from data, and test those templates offline. You will also tell Helm (Go templates), Terraform (HCL interpolation) and Kustomize apart, so you can pick the right tool.

## 1. YAML essentials

A YAML file looks like plain text, but a parser turns each value into a typed object before any tool reads it. Those types are the source of several traps. YAML ("YAML Ain't Markup Language") is a human-friendly serialisation format, which means a way of writing data as text. In practice it is a superset of JSON, because JSON is valid YAML 1.2. So `{"a": 1}` works anywhere YAML does. Every YAML file is built from three structures, shown in the table below.

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

Notice that the example mixes block style, which uses indentation, with flow style, which uses brackets and braces.

### Rules that bite

Indentation is structure, so use spaces and never tabs. A tab character is a parse error. Use two spaces consistently. Sequences under a key may be indented or not, since `key:\n- a` and `key:\n  - a` are both valid. Pick one style.

A colon followed by a space separates a key from its value. A value that contains `: ` or ` #` must be quoted. A `#` that follows a space starts a comment.

Quoting matters because unquoted strings go through type inference. Single quotes are literal, and only `''` escapes a quote inside them. Double quotes support escapes such as `\n`, `\t` and `é`. When you are in doubt, quote the value.

Type coercion is one of the easiest traps to fall into. YAML 1.1 parsers such as PyYAML, which Ansible uses, read `yes`, `no`, `on`, `off`, `y` and `n` as booleans. This is the "Norway problem": the country code `NO` becomes `false`. The same parsers read `1.10` as the float 1.1, so a version number loses its zero. They can read `010` as octal, `1e3` as a float and `2024-01-15` as a date object. The values `~` and empty become null, and a leading `0x` is hex. Times such as `22:30` may parse as sexagesimal integers in YAML 1.1. Meanwhile `0.0.0.0` stays a string, but `1.2` is a float.

Quote versions, codes, IDs and file modes such as `mode: "0644"`. Ansible's guidance is to quote file modes, since `0644` is octal in YAML 1.1 while many tools expect a string. Quote anything else that must stay text.

A string that begins with an asterisk, ampersand, exclamation mark, percent sign, at sign, backtick, brace, bracket, pipe or greater-than sign must be quoted. In Ansible, a value that starts with a Jinja expression needs quotes as well. For example, `"{{ var }}"` must be quoted, because an opening brace would otherwise start a flow mapping.

Multi-line strings have their own style choices. `|` keeps every newline, which suits config files and scripts. `>` folds newlines into spaces. Chomping indicators control the end of the block: `|-` strips the final newline, and `|+` keeps all trailing newlines. An indentation indicator such as `|2` handles content that starts with spaces.

Duplicate keys are easy to miss. Most parsers silently keep the last one, which hides copy-paste bugs. `yamllint` flags them with the `key-duplicates` rule.

Several documents can share one file if you separate them with `---`. Kubernetes manifests and Helm output use this layout. A single parse call usually expects one document, unless you call `yaml.safe_load_all`.

Never call `yaml.load` on untrusted input, because it can instantiate arbitrary Python objects. Use `yaml.safe_load` instead. Anchors can also be abused for "billion laughs" expansion in untrusted documents.

### Anchors, aliases and merge keys

Anchors (`&name`) mark a node, and aliases (`*name`) reuse it. The merge key `<<` merges one mapping into another. It is a YAML 1.1 convention that PyYAML and Kubernetes tooling support. It is not part of the YAML 1.2 core, and not every parser honours it. The example below shows the idea.

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

Anchors work inside a single file only, not across files. Overused anchors make diffs harder to read. CI definitions, such as GitLab `extends` or GitHub Actions reusable workflows, give you higher-level reuse.

### JSON, YAML and other formats

You will often need to convert a file or query it from the command line. Run `python3 -c 'import sys,yaml,json; print(json.dumps(yaml.safe_load(sys.stdin), indent=2))' < file.yml` to convert it for inspection. The `yq` tool (mikefarah) and `jq` both process YAML and JSON. Examples are `yq '.nodes[].name' nodes.yml`, `yq -o=json` and in-place edits with `yq -i`. Kubernetes accepts either format.

Choose the format by asking who edits the file. JSON has no comments and is stricter, which suits machine exchange. YAML suits human-edited configuration. TOML (Python tooling), HCL (Terraform) and INI (ansible.cfg, systemd) are the alternatives.

YAML has no built-in schema enforcement. Validate it with JSON Schema through `check-jsonschema`, with `kubeconform` for Kubernetes, with `pydantic` models in Python, or with Ansible argument specs for roles. Lint the style with `yamllint`. Schema validation and data models are also covered in *Network Programmability and Automation*, chapter 8 (Data Formats and Models). That chapter places YAML among structured data formats, which beat fragile CLI screen scraping. Screen scraping means parsing human-oriented output such as `show interfaces em0`, which breaks whenever a vendor changes the spacing. Requesting structured output, such as XML from `show interfaces em0 | display xml` or JSON, avoids that problem.

The same chapter covers three ideas worth knowing. The first is the two phases of reading text off the wire. Markup languages like HTML annotate documents for rendering, while data serialization formats represent typed data structures across languages. When bytes arrive, you decode them into a UTF-8 string, such as `"{\"vendors\":[\"Cisco\",\"Juniper\",\"Arista\"]}"`. Then you deserialize that string into native structures with `json.loads()`, which gives you a Python `dict` and `list`. Sending reverses the flow: you serialize first and then encode.

The second is the split between text and binary formats. XML uses tags, attributes and `xmlns:` namespaces. You query it with **XPath**, for example `//device/model` or `//device[@name="leaf"]/model`, or with **XQuery**. You validate it with **XSD** (`xmlschema`). JSON is lighter, and you validate it with **JSON Schema**. A schema starts with `"$schema": "https://json-schema.org/draft/2020-12/schema"` and can check `minLength`, `maxLength`, `minimum: 1`, `maximum: 4094` and IPv4 `pattern` regexes through Python's `jsonschema.validate()`. For high-throughput RPCs, such as gRPC telemetry or distributed training control planes, binary **Protocol Buffers** and **FlatBuffers** remove the text-parsing overhead. Protocol Buffers use `.proto` files, compiled with `protoc` and validated with `protoc-gen-validate`. FlatBuffers lets you read fields straight from the byte buffer without unpacking it. Python's `pickle` works only with Python, and it is unsafe on untrusted bytes.

The third is YANG. YANG is a data-modeling language, not a wire serialization format. The language is defined in RFC 6020 and RFC 7950. NETCONF and RESTCONF serialize YANG-modeled data as XML or JSON on the wire. A YANG module, such as `module acme-switch`, declares a `namespace`, a `prefix` and an `import ietf-inet-types`. It defines reusable types like `typedef vlan-id { type uint16 { range "1..4094"; } }`. It also defines single-value `leaf` nodes, scalar lists such as `leaf-list name-server`, and keyed `container` and `list` hierarchies such as `container vlans { list vlan { key "id"; unique "name"; ... } }`. OpenConfig and IETF models use these ideas to standardize data across vendors.

Ansible module arguments follow the same thinking. In *Ansible: Up and Running*, chapter 3, the authors recommend passing module arguments as pure YAML dictionaries. You write `package:\n  name: nginx\n  update_cache: true` rather than legacy `key=value` string arguments such as `package: name=nginx update_cache=yes`. Pure YAML highlights properly in editors, avoids multi-line backslash escaping and converts numeric and boolean types cleanly.

The flow below shows how the pieces fit together. Data and templates feed a template engine, and the rendered output goes to a target validator.

```mermaid
flowchart LR
    Data["Structured Data Source<br/>(YAML / JSON / Inventory / YANG Model)<br/>Validated by yamllint & JSON Schema"] --> Engine["Template Engine<br/>(Jinja2 Environment, StrictUndefined,<br/>Custom Filters, Ansible template module)"]
    Tpl["Template File (.j2)<br/>({{ expr }}, {% for/if %}, {# comment #},<br/>trim_blocks & lstrip_blocks)"] --> Engine
    Engine --> Out["Rendered Config Artifact<br/>(nginx.conf, slurm.conf, switchport CLI)"]
    Out --> Val["Target Validator<br/>(nginx -t, visudo -cf %s, scontrol)"]
```

Store the lint rules in a `.yamllint` file, as in the example below. The comment on the `truthy` line says that it flags `yes`, `no`, `on` and `off`.

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

Writing a Slurm node list by hand for every machine invites mistakes. Jinja2 lets you write the pattern once and feed it data. It is a Python templating engine. A template mixes literal text with three kinds of delimiters, shown in the table below. Each kind does a different job, so learn to recognise them at a glance.

| Delimiter | Purpose |
|---|---|
| `{{ expression }}` | Output the value of an expression |
| `{% statement %}` | Control flow: `if`, `for`, `set`, `macro`, `include`, `block` |
| `{# comment #}` | Comment (not rendered) |

Rendering takes a template plus a context, which is the set of variables, and produces text. Ansible uses Jinja2 for variable interpolation in playbooks, conditionals and `template` files. Salt, Flask, dbt, Superset, Cookiecutter and many network-automation tools also use it. Helm and Terraform do not. Helm uses Go templates, and Terraform uses HCL.

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

Notice that the loop writes one line per node, with each GPU count filled in. The `StrictUndefined` setting turns a missing variable into an error instead of an empty string. That is the single most useful safety setting. Ansible's default also errors on undefined variables unless you provide a `default`.

### Expressions

Expressions are how you read values out of your data. Write `{{ cluster.name }}` to read an attribute, or `{{ cluster['name'] }}` for the item form. Lists work the same way: `{{ list[0] }}`, `{{ list[-1] }}` and slices such as `{{ list[1:3] }}`. Literals include strings, numbers, `true` and `false` (Python's `True` and `False` also work), `none`, lists such as `[1, 2]`, dicts such as `{'a': 1}`, and tuples.

The operators are arithmetic `+ - * / // % **`, comparison `== != < > <= >=`, logic `and or not`, and membership `in`. Use `~` to join strings, not `+`. The conditional expression `{{ 'a' if cond else 'b' }}` picks one value or the other. The `is` keyword applies a test, which the next section covers.

### Filters

A filter transforms a value, and you can chain filters together. The form is `{{ value | filter(args) }}`. The table groups the common filters by category, so use it as a lookup.

| Category | Filters |
|---|---|
| Strings | `upper`, `lower`, `title`, `trim`, `replace('a','b')`, `regex_replace` (Ansible), `split(',')`, `join(', ')`, `truncate`, `indent(4)`, `center`, `wordwrap`, `urlencode` |
| Defaults / safety | `default('x')`, `default('x', true)` (also for empty/falsy), `mandatory` (Ansible), `string`, `int`, `float`, `bool`, `abs`, `round` |
| Collections | `length`, `first`, `last`, `sort`, `unique`, `reverse`, `list`, `map(attribute='name')`, `select`, `reject`, `selectattr('gpus','gt',4)`, `rejectattr`, `groupby('rack')`, `sum`, `min`, `max`, `batch(3)`, `slice(3)` |
| Dict | `dictsort`, `items`, `dict2items`/`items2dict` (Ansible), `combine` (Ansible merge), `json_query` (JMESPath, Ansible) |
| Serialisation | `tojson`, `to_json`, `to_nice_json`, `to_yaml`, `to_nice_yaml`, `from_json`, `from_yaml` (Ansible), `b64encode`/`b64decode`, `hash('sha256')`, `password_hash` |
| Paths | `basename`, `dirname`, `expanduser`, `realpath`, `splitext` (Ansible) |
| Network (Ansible `ansible.utils`/`ansible.netcommon`) | `ipaddr`/`ansible.utils.ipaddr`, `ipv4`, `ipmath`, `cidr_merge`, `hwaddr`, `ansible.utils.next_nth_usable` |

Read the examples below as short pipelines. Each one takes the nodes list and returns a single answer, such as the names of the GPU nodes or their total.

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

A test asks a yes-or-no question about a value. You write it after `is`, usually inside an `if`. The core tests are `defined`, `undefined`, `none`, `string`, `number`, `integer`, `mapping`, `iterable`, `sequence`, `even`, `odd`, `divisibleby(3)`, `equalto`, `in`, `lower`, `upper` and `callable`. Ansible adds more, including `success`, `failed`, `changed`, `skipped`, `match`, `search`, `version('2.0', '>=')`, `subset`, `superset`, `contains`, `file`, `directory` and `exists`.

```jinja
{% if gpu_driver_version is version('550', '>=') %}...{% endif %}
{% if item is defined and item is not none %}...{% endif %}
{{ result is failed }}
```

Use `is version` when a version number matters, such as a GPU driver check. The other tests answer simpler questions about whether a value exists or what type it has.

### Control structures

Control structures let a template make decisions and repeat text. The `if` block below picks a line based on the node's role. The `for` loop groups nodes by rack, and its `else` branch covers an empty group.

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

Inside a loop, the `loop` variable tells you where you are. `index` is 1-based, and `index0` counts from 0. You also get `first`, `last`, `length`, `revindex`, `cycle('a','b')`, `previtem` and `nextitem`. A variable set inside a `for` stays inside that loop. When you need a value after the loop, use `namespace` to carry it out. The `{% for ... %}...{% else %}...{% endfor %}` form runs the `else` block when the sequence is empty.

### Whitespace control

Templates that produce config files must control blank lines and indentation, and a template can break them without any visible sign. Jinja2 gives you several tools. `{%-` and `-%}` strip whitespace before or after a tag. `trim_blocks=True` removes the first newline after a block tag. `lstrip_blocks=True` strips leading whitespace before a block tag. Ansible's `template` module sets `trim_blocks=True` by default. You can set `lstrip_blocks` through `jinja2_extensions` or a `# jinja2:` header. A common pattern is a first-line override, shown below.

```jinja
#jinja2: trim_blocks:True, lstrip_blocks:True
# {{ ansible_managed }}
```

Always render the template and read the output. Whitespace errors are invisible in the template itself, and they are fatal in whitespace-sensitive output such as YAML or Makefiles.

### Macros, includes, inheritance, raw blocks

A macro lets you reuse a stanza, and an include renders another template with the same context. The examples below show both, plus inheritance and raw blocks.

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

Prometheus alert annotations, Helm templates and Grafana are the usual cases where a template must output literal `{{ }}`. Wrap that text in `{% raw %}`, or write it with `{{ '{{' }}`.

## 3. Jinja2 in Ansible

Ansible adds its own variables, filters and tests on top of Jinja2. It evaluates templates on the control node, the machine you run Ansible from. You will meet Jinja2 in several places, and each place has its own quoting rules.

Jinja2 appears in task arguments, `vars`, `when`, `loop`, `failed_when`, `changed_when`, file contents rendered by the `template` module (such as `src: nccl.conf.j2`), and inventory variables. The `when` clause is already a Jinja expression. Write `when: ansible_distribution == 'Ubuntu'`, not `when: "{{ ... }}"`.

A YAML value that starts with `{{` must be quoted, for example `msg: "{{ var }}"`. Inside quotes you can mix literal text and expressions, as in `path: "/data/{{ project }}/{{ env }}"`.

Undefined variables cause an error by default. Use `{{ var | default('x') }}`, `{{ var | mandatory }}`, an `is defined` check, or `default(omit)` to drop an optional module parameter.

Ansible templating returns strings unless the value is a single native expression. A boolean from `{{ }}` can therefore arrive as the string `"True"`. Use `| bool`, `| int` and `when:` conditionals instead of string comparisons. The `jinja2_native` setting can change this behaviour, so test carefully.

Lookups and facts give you data from outside the template. Examples include `lookup('env', 'HOME')`, `lookup('file', 'x')`, `lookup('pipe', 'cmd')` (run on the control node), `query`, `hostvars['host']['ansible_default_ipv4']['address']`, `groups['gpu']`, `inventory_hostname`, `ansible_facts` and `play_hosts`.

The `ansible.builtin.template` module renders on the control node and copies the result to the target. Its options include `owner`, `group`, `mode`, `backup`, `variable_start_string` for different delimiters, and `validate: "visudo -cf %s"`. The `validate` option checks the file before it is installed, which is essential for sudoers, sshd and nginx. The `{{ ansible_managed }}` variable gives you a "do not edit" header.

The next example renders Slurm node definitions from inventory data.

```jinja
# {{ ansible_managed }}
{% for host in groups['gpu'] | sort %}
{% set h = hostvars[host] %}
NodeName={{ host }} NodeAddr={{ h.ansible_host }} CPUs={{ h.ansible_processor_vcpus }} RealMemory={{ (h.ansible_memtotal_mb * 0.95) | int }} Gres=gpu:{{ h.gpu_count | default(8) }} State=UNKNOWN
{% endfor %}
PartitionName=gpu Nodes={{ groups['gpu'] | join(',') }} Default=YES MaxTime=INFINITE State=UP
```

For example, a host without a `gpu_count` variable falls back to the default of 8, so its line reads `Gres=gpu:8`. If the host sets `gpu_count` to 4, the same line reads `Gres=gpu:4`. The rest of the line stays the same either way.

The NCCL environment comes from variables in the same way.

```jinja
# {{ ansible_managed }}
{% for k, v in (nccl_env | default({})) | dictsort %}
NCCL_{{ k | upper }}={{ v }}
{% endfor %}
```

Here the variables are `nccl_env: { debug: WARN, ib_hca: "mlx5_0,mlx5_1", socket_ifname: eth0 }`.

### Network switchport templates, custom Python filters (`get_interface_speed`), and NGINX TLS templates (`NPA` Ch. 9 & `AUR` Ch. 3)

Two classic walkthroughs from the Gem Books show how data and Jinja2 templates come together in practice. The code for both is modeled in `code/part04/yaml_jinja2_templates.py`.

The first walkthrough renders switchport configurations with loops, conditionals, filter chains and custom filters. It comes from *Network Programmability and Automation*, chapter 9, examples 9-4 to 9-10. The script starts from a `data.yml` list of switch interfaces. `GigabitEthernet0/1` has `uplink: true`, and `GigabitEthernet0/2..3` have `vlan: 10`. The script loads the template with `ENV = Environment(loader=FileSystemLoader('.')); template = ENV.get_template("template.jinja")`. It then registers a custom Python function, `def get_interface_speed(interface_name):`, with `ENV.filters['get_interface_speed'] = get_interface_speed`. That function returns `1000` for `gigabit`, `100` for `fast`, and `0` otherwise.

```jinja
{% for interface in interface_list %}
interface {{ interface.name }}
  description {{ interface.desc | upper | reverse }}
{% if interface.uplink %}
  switchport mode trunk
{% else %}
  switchport access vlan {{ interface.vlan }}
  switchport mode access
{% endif %}
  speed {{ interface.name | get_interface_speed }}
{% endfor %}
```

Notice that you can pass either a Python `dict` (`interface_dict`) or a custom Python class instance (`NetworkInterface("GigabitEthernet0/1", "Server Port", 10)`) into `template.render()`. Jinja2 resolves `interface.name` on both. The same chapter contrasts Jinja2 with **XSLT** XML transformations, which use `lxml.etree.XSLT`, and with **Go `text/template`**, which uses `{{range $i, $interface := .Interfaces}}` and `template.FuncMap{"ifparse": IfParse}`.

The second walkthrough templates `nginx.conf.j2` and `index.html.j2` in an Ansible playbook. It comes from *Ansible: Up and Running*, chapter 3, in the file `webservers-tls.yml`. That file defines play-level `vars:`: `tls_dir: /etc/nginx/ssl/`, `key_file: nginx.key`, `cert_file: nginx.crt`, `conf_file: /etc/nginx/sites-available/default` and `server_name: localhost`. The task `template: src=nginx.conf.j2 dest={{ conf_file }} mode='0644'` fills `{{ server_name }}` and `{{ tls_dir }}{{ cert_file }}` into the NGINX `server` block. A second task, `template: src=index.html.j2 dest=/usr/share/nginx/html/index.html`, uses the built-in `{{ inventory_hostname }}` variable. Whenever the rendered file changes, `notify: Restart nginx` restarts the service.

For any file that a broken config could lock you out of, such as sudoers or sshd, set `validate` before you trust the template.

## 4. Templating elsewhere (and how not to confuse them)

Several tools in this stack use templates, and their syntax looks alike even where the rules differ. The table shows which language each tool uses, so you can check before you edit a file.

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

A few habits keep templated configuration manageable. Separate data from templates by keeping variables in inventory or vars files, and keep the templates light on logic. Where you can, prefer declarative overlays such as Kustomize, or typed config. Avoid templating a templating language, such as Helm values rendered by Jinja and then rendered again by Terraform. Keep logic in code or modules rather than in 200-line Jinja files. Validate the generated YAML after rendering with `yamllint`, `kubeconform` or `kubectl --dry-run=server`.

Keep a template for the parts that really vary, and keep the data in a file you can read without rendering it.

## 5. Testing and debugging templates

A template can render without errors and still produce a broken file. You catch those problems by rendering offline, comparing the result with an expected file, and checking the output with the target's own tools.

You can render offline in three ways. Use the `jinja2` Python API with a fixtures file. Run a single task with `ansible localhost -m ansible.builtin.template -a "src=nccl.conf.j2 dest=/tmp/out" -e @vars.yml --diff`, or use a one-task playbook. To check a single expression, run `ansible -m debug -a "msg={{ ... }}"`.

Golden-file tests render representative data, including empty lists and missing optional keys, and compare the result with an expected file. See 3.9 for testing patterns. Snapshot tests catch accidental whitespace changes.

Validate the output with the target's own parser. Examples include `nginx -t`, `visudo -cf`, `sshd -t`, `slurmd -C` or `scontrol` checks, `kubeconform`, `promtool check rules`, and `python -c 'import yaml; yaml.safe_load(...)'`.

When something goes wrong, print the data. Use `{{ var | to_nice_json }}` in `debug` tasks, run `ansible-playbook -vvv`, or run `ansible-inventory --host name` to see merged variables. For an undefined-variable error, read the exact variable name and the precedence layer (4.7).

The table below matches common error messages to their usual causes.

| Message | What it usually means |
|---|---|
| `AnsibleUndefinedVariable: 'x' is undefined` | A variable is missing from the context |
| `template error while templating string: unexpected '}'` | Unbalanced braces, or confusion with a YAML flow mapping |
| `mapping values are not allowed here` | An unquoted string contains a YAML colon |
| `found character '\t' that cannot start any token` | A tab character in the file |
| `did not find expected key` | Indentation is wrong |
| `The task includes an option with an undefined variable` | An option refers to a variable that does not exist |

Heavy Jinja inside loops over thousands of hosts is slow. Precompute values with `set_fact` or filters, and avoid `lookup('pipe')` per host.

Before you ship a template, render it once against your edge-case fixtures and read the output.

## 6. Security considerations

Untrusted data is the main risk when templates are involved. Never render a user-provided string as a template, because that opens the door to server-side template injection. Ansible marks values from facts as "unsafe", which stops them from being templated again. Do not remove that `!unsafe` marking, and avoid `eval`-like constructs.

Secrets need extra care in rendered files. Set `mode: "0600"`, `owner` and `no_log: true` on any task that renders a secret. Set `diff: false` as well, so the secret stays out of `--diff` output. When you template values into shell commands, quote them with the `| quote` filter. Use `yaml.safe_load` for parsing, and pin and review your parsers as part of your tooling.

## 7. Lab

Start with the self-checking Python lab. Run it on your own machine to confirm the core ideas. When you run it, it checks the YAML 1.1 scalar type-coercion traps, through `classify_yaml11_unquoted_scalar` on `NO`, `1.10`, `010`, `0x1f`, `22:30` and `~`. It checks block chomping indicators through `apply_yaml_block_chomping` on `|`, `|-`, `|+` and `>-`. It renders the switchport template from *Network Programmability and Automation*, chapter 9, with its `upper | reverse` filter chain and custom `get_interface_speed` filter, through `render_switchport_template`. Finally, it renders Slurm node configuration with `StrictUndefined` validation, through `render_slurm_nodes_template`.

```bash
python3 code/part04/yaml_jinja2_templates_lab.py
```

Next, work through the exercises below on any machine with Python 3.10+ and `jinja2`, `pyyaml` and `yamllint` installed. You will find that every interactive shell step is marked `untested here`.

1. Read a file that contains `no`, `yes`, `1.10`, `010`, `22:30`, `2024-01-01`, `~`, `0x1f` and `"quoted"`. Parse it with PyYAML and print each Python type. Then quote each value correctly, and run `yamllint` with the `truthy` rule.
2. Build the node defaults file, then load it with PyYAML and with `yq`. Show a parser that ignores `<<`. Finally, refactor the file to use explicit inheritance in code.
3. Write `|`, `>`, `|-` and `>+` blocks, and print their `repr` to see the newlines. Then embed a script and a systemd unit in YAML.
4. Render the Slurm node template from a Python script with `StrictUndefined`. Remove a variable and watch the error. Then compare the behaviour without `StrictUndefined`.
5. From a nodes list, produce four results: (a) comma-joined names for nodes with 8 GPUs, (b) the total GPUs, (c) nodes grouped by rack, and (d) a YAML dump with `to_nice_yaml`.
6. Render the same loop with and without `trim_blocks`, `lstrip_blocks` and `{%-`. Diff the outputs. Then fix a template that emits blank lines in the middle of a config file.
7. Factor the repeated stanzas into macros and includes. Test `{% raw %}` by templating a Prometheus alert rule that contains Go template syntax.
8. Write `nccl.conf.j2` and render it with the `template` module. Use `--diff`, `--check`, and `validate:` with a custom validator command. Show `default(omit)` skipping an optional parameter, and reproduce the YAML error that an unquoted `{{ }}` value causes.
9. Demonstrate a boolean that arrives as the string `"False"`, then fix it with `| bool`. Compare `when: var` with `when: var | bool`.
10. Write the same service config three ways: as a Jinja2 template for Ansible, as a Helm template and as a Kustomize patch. List when each one is the better choice.
11. Add `yamllint`, `check-jsonschema` (or `kubeconform`) and a golden-file render test to pre-commit or CI.
12. Clean up.

## 8. Common mistakes

Tabs and uneven indentation are the first things you should check in YAML. Mixing list styles also makes a file harder for others to read. Unquoted values such as `NO`, `1.10`, `yes`, times and values with leading zeros get reinterpreted by YAML. An unquoted `{{ var }}` at the start of a value causes trouble too.

In templates, `when: "{{ var }}"` double-templates a condition, where `when: var` is correct. Relying on undefined variables that quietly render as empty strings is another trap. So are templates with heavy logic and nested loops that nobody can review, and templates that generate other templates. Whitespace bugs slip through when no one inspects the generated output. Forgetting `{% raw %}` breaks Go-template or Jinja-in-Jinja content.

Security mistakes matter too. Using `yaml.load` on untrusted data, or rendering untrusted strings as templates, is a mistake to avoid. Anchors across files are not supported, and overused merge keys can hide the effective configuration. Deploying rendered output that you never validated is a mistake of its own.

Inspect the rendered output on every template change. Whitespace bugs show up there, not in the template.

## 9. Interview angles

Use these questions to check what you have learned.

- "What are YAML's gotchas? Name values that change type, such as the Norway problem, versions and octal."
- "What is the difference between `|` and `>` block scalars?"
- "How do you reuse YAML sections? What are the limits of anchors?"
- "How do Jinja2 statements, expressions and comments differ? How does Ansible use them?"
- "How do you loop over inventory hosts to build a config file? How do you avoid blank lines?"
- "When do you use default, mandatory and omit?"
- "How do you test and validate templates?"
- "How do Helm, Jinja2, Kustomize and Terraform `templatefile()` differ? When would you choose each?"
- "Why is `yaml.load` dangerous?"

## Exercises

These exercises check whether you have understood the ideas. Each one points at a specific function or file, so you can see the behaviour yourself.

1. Start with the YAML type traps. Use `classify_yaml11_unquoted_scalar()` and `apply_yaml_block_chomping()` in `code/part04/yaml_jinja2_templates.py`. Explain how YAML 1.1 parsers coerce `NO`, `1.10`, `010`, `0x1f`, `22:30` and `~`, and why file modes such as `"0644"` and version strings must be quoted. Then state the exact newline difference between `|`, `|-`, `|+`, `>` and `>-`. Finally, explain how `&anchor`, `*alias` and `<<` work, and why pure YAML task dictionaries beat `key=value` inline strings in Ansible, as *Ansible: Up and Running*, chapter 3, explains.
2. Next, compare the data formats YAML, JSON, XML, Protobuf and FlatBuffers, as *Network Programmability and Automation*, chapter 8, does. Explain the two phases of reading and writing a text-based format on the wire, which are decoding and deserializing on input and serializing and encoding on output. Then explain why structured formats beat CLI screen scraping. After that, compare `JSON Schema` with `YANG`, using `container`, `list`, `leaf`, `leaf-list` and `typedef` (RFC 6020 and RFC 7950). Explain why YANG is a data-modeling language rather than a wire serialization format.
3. Work with the Jinja2 core, using `get_interface_speed()`, `render_switchport_template()` and `render_slurm_nodes_template()`, as *Network Programmability and Automation*, chapter 9, shows. Explain how `{{ }}`, `{% %}` and `{# #}` behave with `StrictUndefined`, `trim_blocks=True`, `lstrip_blocks=True` and `{%- -%}`. Then explain how `map(attribute=...)`, `selectattr`, `groupby`, `default('x', true)` and custom filters such as `ENV.filters['get_interface_speed']` transform collections. Finally, explain why a counter updated inside `{% for %}` needs `namespace(count=0)`.
4. Move on to Jinja2 in Ansible. You will need to explain why a YAML value that starts with `"{{ var }}"` must be quoted, while `when: ansible_distribution == 'Ubuntu'` must not wrap its expression in `{{ }}`. Then show how `ansible.builtin.template` uses `validate: "visudo -cf %s"` (or `nginx -t`), how `default(omit)` drops optional module parameters, and how `{% raw %}...{% endraw %}` escapes literal `{{ }}` for Prometheus or Helm rules.
5. Compare the templating tools across the stack. Look at how Ansible (Jinja2), Helm (Go `text/template` with Sprig, such as `{{ .Values.x | quote }}` and `{{-`), Terraform (HCL `${var.x}` and `templatefile()`), and Kustomize (template-free strategic-merge and JSON6902 patches) parameterize configuration. Then explain why templating a template, such as Jinja generating Helm templates, is an anti-pattern.
6. Design a CI step that renders `slurm.conf.j2` and `nccl.conf.j2` offline against test fixtures, using `StrictUndefined`. The step should diff the output against golden files and check syntax with `yamllint` and `check-jsonschema`. Then explain Server-Side Template Injection (`SSTI`), why `yaml.safe_load` is mandatory, and why tasks that render secret templates need `mode: "0600"`, `no_log: true` and `diff: false`.

## Checkpoint questions (20)

<details>
<summary>1. What are YAML's three fundamental data structures, why is JSON valid YAML, and why are tabs forbidden (*Ansible: Up and Running* chapter 3 and *Network Programmability and Automation* chapter 8)?</summary>

YAML builds every document from three primitives. Scalars are single values such as strings, numbers, booleans and `null`. Sequences are ordered lists, written with `- item` lines or `[a, b]` flow syntax. Mappings are key-value dictionaries, written as `key: value` lines or `{a: 1}` flow syntax. Because YAML 1.2 was designed as a strict superset of JSON, any valid JSON document is also valid YAML. YAML uses spaces for indentation and forbids tab characters there. A tab triggers the error `found character '\t' that cannot start any token`.
</details>

<details>
<summary>2. Explain six classic YAML type-coercion traps (`NO`, `1.10`, `010`, `0x1f`, `22:30`, `~`) and how to prevent them in `yamllint`.</summary>

In YAML 1.1 parsers, such as PyYAML used by Ansible, six traps catch people out. The first is the Norway problem. An unquoted `NO`, `off`, `yes`, `on`, `y` or `n` becomes a boolean. Here `NO` is Norway's ISO country code and parses as `False`, while `yes` and `on` parse as `True`. The second is `1.10`, which parses as the float 1.1 and loses its trailing zero. Third, leading zeros make octal numbers, so `010` becomes `8` and `0644` becomes `420`. That breaks tools that expect the four-character string `"0644"`. Fourth, `0x1f` parses as the integer `31`. Fifth, `22:30` parses as a base-60 number, 22 × 60 + 30 = 1350. Sixth, `~` or an empty value parses as `None`. Quote versions, country codes, file modes such as `mode: "0644"`, and any string that contains a colon. Then configure `yamllint` with `truthy: { allowed-values: ["true", "false"] }`.
</details>

<details>
<summary>3. Contrast YAML's literal (`|`) and folded (`>`) block scalars, and explain the chomping indicators (`|-`, `|+`, `|2`).</summary>

The literal style, `|`, keeps every newline inside the block. That makes it ideal for embedded shell scripts, certificates and multi-line config files such as `motd` or `visiting_address` in *Ansible: Up and Running*, chapter 3. The folded style, `>`, turns single newlines into spaces. Long paragraphs can wrap neatly in your source and still come out as one line. Chomping controls the newlines at the end. By default, `|` or `>` keeps one final newline. `|-` and `>-` strip all trailing newlines, while `|+` and `>+` keep every trailing blank line. A digit such as `|2` says the block is indented by 2 spaces, which you need when the first content line itself starts with spaces.
</details>

<details>
<summary>4. How do YAML anchors (`&`), aliases (`*`), and merge keys (`<<`) work, and what are their limitations?</summary>

An anchor, written `&node_defaults`, labels a YAML node. An alias, `*node_defaults`, points back to that node later in the same file. The merge key, `<<: *node_defaults`, copies all the keys from the anchored mapping into the current one. Local keys such as `gpus: 4` override the copied defaults. Anchors have limits. They cannot cross file boundaries, and the `<<` key is a YAML 1.1 extension that not every YAML 1.2 parser supports. Deep anchor chains also hide changes in diffs. On untrusted input, they can be abused for "billion laughs" memory amplification.
</details>

<details>
<summary>5. In *Network Programmability and Automation* Chapter 8, what are the two phases of reading text-based data off the wire, and why is YANG NOT a serialization format?</summary>

When your program receives bytes from an API or socket, it decodes them first. Decoding turns the raw bits into a UTF-8 string, for example with `bytes.decode('utf-8')`. Then it deserializes that string into native in-memory data, such as a Python `dict` or `list` from `json.loads` or `yaml.safe_load`. Sending reverses the process: you serialize the data first, and then encode it. YANG (RFC 6020 and RFC 7950) is a data-modeling and schema language, not a wire format. It defines the hierarchy, types such as `typedef vlan-id`, constraints such as `range "1..4094"`, `container` nodes, keyed `list` nodes and `leaf` nodes for a device's configuration and state. Protocols such as NETCONF, RESTCONF and gNMI then serialize that data on the wire as XML, JSON or Protobuf.
</details>

<details>
<summary>6. Compare Text-Based formats (`YAML`, `JSON`, `XML`) with Binary formats (`Protobuf`, `FlatBuffers`, `pickle`) (*Network Programmability and Automation* chapter 8).</summary>

Text-based formats such as YAML, JSON and XML are readable in any text editor. You validate JSON with JSON Schema and XML with XSD, and you query them with `jq`, `yq` or XPath. YAML suits configs and playbooks that people write by hand. JSON is stricter, with no comments and no type-coercion traps, which makes it a good fit for REST APIs. Binary formats such as Protobuf, FlatBuffers and `pickle` are compact and fast, which suits high-rate RPCs such as gRPC. Protobuf compiles `.proto` schemas with `protoc` into typed Go, Python or C++ classes. FlatBuffers lets you read fields straight from the serialized buffer without unpacking it. Python's `pickle` works only with Python, and it is unsafe on untrusted bytes. `yaml.load` carries the same risk of running arbitrary objects, so always use `yaml.safe_load`.
</details>

<details>
<summary>7. What are Jinja2's three delimiter pairs, what does `StrictUndefined` do, and why use `~` instead of `+` for string concatenation?</summary>

The three delimiter pairs are `{{ expression }}`, which evaluates and prints a value; `{% statement %}`, which runs control flow such as `if`, `for`, `set`, `macro`, `include`, `extends`, `block` and `raw`; and `{# comment #}`, which is removed from the output entirely. By default, a missing variable such as `{{ missing }}` renders as an empty string, which can silently break a config file. Passing `undefined=StrictUndefined` to `jinja2.Environment` makes a missing variable raise an `UndefinedError` right away, and Ansible's default behaviour is the same. The `~` operator converts both operands to strings and joins them, so `{{ "gpu" ~ 1 }}` gives `"gpu1"`. The `+` operator tries numeric addition and raises a `TypeError` when you mix `str` and `int`.
</details>

<details>
<summary>8. How do `default('x')`, `default('x', true)`, `mandatory`, and Ansible's `default(omit)` differ?</summary>

`{{ val | default('x') }}` returns `'x'` only when `val` is undefined. If `val` is defined but empty, `None` or `False`, it returns that falsy value instead. `{{ val | default('x', true) }}`, which you can also write with `boolean=True`, returns `'x'` when `val` is undefined or falsy, including `""`, `None`, `0`, `False` and `[]`. `{{ val | mandatory }}` fails at once with a clear message when `val` is undefined. In Ansible module arguments, `{{ val | default(omit) }}` drops the whole parameter key when `val` is undefined, so the module uses its own internal default.
</details>

<details>
<summary>9. How do Jinja2 collection filters (`map`, `selectattr`, `rejectattr`, `groupby`, `sum`, `dict2items`, `combine`, `json_query`) replace verbose loops?</summary>

Take a list of node dictionaries. `nodes | selectattr('gpus', 'ge', 8) | map(attribute='name') | join(',')` keeps the nodes with 8 or more GPUs, pulls out each name, and joins them into `"gpu01,gpu02"` in one pipeline. `nodes | sum(attribute='gpus')` adds up the GPU counts across all nodes, and `nodes | groupby('rack')` groups nodes by rack for two-level rendering. In Ansible, the `ansible.utils` and `community.general` collections provide `dict2items` and `items2dict`, which convert between a `{k: v}` mapping and a `[{'key': k, 'value': v}]` list. `combine(recursive=True)` deep-merges dictionaries, and `json_query` runs JMESPath queries.
</details>

<details>
<summary>10. How do you Register a Custom Python Filter in Jinja2 (`get_interface_speed` in *Network Programmability and Automation* chapter 9), and how do Jinja Tests (`is`) differ from Filters (`|`)?</summary>

Define a normal Python function, such as `def get_interface_speed(interface_name): ...`. Its first argument receives the piped value. Then register it on the Jinja2 environment with `ENV.filters['get_interface_speed'] = get_interface_speed`, and templates can call it as `{{ interface.name | get_interface_speed }}`. A filter, written with `|`, turns a value into a new value, as in `{{ x | upper }}`. A test, written with `is`, asks a yes-or-no question about a value, as in `{% if x is defined and v is version('550', '>=') %}`. Tests work inside `if`, `elif`, `select` and `selectattr`.
</details>

<details>
<summary>11. Why does `{% set count = count + 1 %}` inside a Jinja2 `{% for %}` loop fail to update `count` outside the loop, and how does `namespace()` fix it?</summary>

Loop bodies in Jinja2 are scoped. When you assign with `{% set count = ... %}` inside a `for` loop, you create a new local variable for that iteration, and the outer `count` stays unchanged. To carry state across iterations and read it after `{% endfor %}`, create a mutable `namespace` object before the loop:
`{% set ns = namespace(count=0) %}`
`{% for n in nodes %}{% set ns.count = ns.count + n.gpus %}{% endfor %}`
`Total: {{ ns.count }}`.
</details>

<details>
<summary>12. How do `trim_blocks`, `lstrip_blocks`, and `{%- -%}` control whitespace in generated configuration files?</summary>

Without whitespace control, each `{% if %}` and `{% for %}` line leaves a blank line and leading spaces behind in the rendered file. `trim_blocks=True` removes the first newline after a block tag, and it is on by default in Ansible. `lstrip_blocks=True` removes the leading spaces and tabs before a block tag. You can set both with `#jinja2: trim_blocks:True, lstrip_blocks:True` on line 1 of an Ansible template. `{%-` and `-%}`, or `{{-` and `-}}`, strip all whitespace, including newlines, next to that one tag.
</details>

<details>
<summary>13. Why must you quote `msg: "{{ var }}"` in an Ansible YAML file, and why must you NOT write `when: "{{ var }}"`?</summary>

An unquoted value that starts with `{` begins a flow mapping, which is a YAML dictionary. So `msg: {{ var }}` without quotes is a YAML syntax error, and you may see `template error` or `found unhashable key`. Always quote values that begin with `{{`, as in `msg: "{{ var }}"`. The `when:`, `failed_when:` and `changed_when:` clauses are already bare Jinja2 expressions. Writing `when: "{{ my_var }}"` causes double-templating warnings and string-truthiness bugs. Write `when: my_var | bool` or `when: ansible_distribution == 'Ubuntu'` instead.
</details>

<details>
<summary>14. Why can a Jinja2 expression in Ansible return the string `"False"` instead of a boolean, and how do you handle it safely?</summary>

Unless `ANSIBLE_JINJA2_NATIVE=true` is set, Ansible's template engine turns multi-part interpolated results into strings. In Python, any non-empty string is truthy, and that includes `"False"`. So when a boolean or integer from an expression feeds another task or conditional, pipe it through `| bool` or `| int` explicitly, for example `enabled: "{{ service_enabled | bool }}"`.
</details>

<details>
<summary>15. How do you output literal `{{ }}` braces inside an Ansible Jinja2 template when generating a Prometheus alert rule or Helm template?</summary>

Ansible's Jinja2 engine evaluates every `{{ ... }}` in a `.j2` template on the control node. So an unescaped Prometheus annotation such as `{{ $labels.instance }}` fails with `AnsibleUndefinedVariable: '$labels' is undefined`. Wrap the literal section in a `{% raw %}...{% endraw %}` block, or escape the delimiters as `{{ '{{' }} $labels.instance {{ '}}' }}`.
</details>

<details>
<summary>16. What does the `validate:` parameter on `ansible.builtin.template` do, and why is it essential for `/etc/sudoers`, `sshd_config`, and `nginx.conf`?</summary>

When you set `validate: "visudo -cf %s"` on `ansible.builtin.template`, Ansible first renders the template to a temporary file on the target host. It then runs the validation command against `%s`, and it overwrites the destination only after the check passes. Other examples are `validate: "sshd -t -f %s"` and `validate: "nginx -t -c %s"`. If the check exits non-zero, Ansible aborts the task and leaves the working `/etc/sudoers` or `sshd_config` untouched. That stops a template typo from locking administrators out of the fleet.
</details>

<details>
<summary>17. Compare Jinja2 (Ansible), Go `text/template` (Helm), HCL `templatefile()` (Terraform), and Kustomize (*Network Programmability and Automation* chapter 9).</summary>

- **Jinja2 (Ansible, Salt, Python):** Pythonic expression syntax, such as `{{ var | filter }}` and `{% for x in xs %}`.
- **Go `text/template` with Sprig (Helm, Prometheus, Consul-template):** Uses a cursor dot, `.`, as in `{{ .Values.image.tag | quote }}`, `{{- range $k, $v := .Values.env }}` and `{{ toYaml .Values.resources | nindent 8 }}`. You can also write custom `template.FuncMap` functions.
- **HCL `templatefile(path, vars)` (Terraform, OpenTofu, Packer):** Renders a file with HCL interpolation, such as `${var}` and `%{ for x in list ~} ... %{ endfor ~}`.
- **Kustomize (`kubectl apply -k`):** Uses no templating at all. It starts from valid base YAML manifests and applies declarative overlays, such as `strategicMergePatch`, `patchesJson6902`, `images` and `replicas`. Every file in Git stays valid YAML, so `kubeconform` and IDEs can parse it directly.
</details>

<details>
<summary>18. How do you render and test Jinja2 templates offline in CI without connecting to real servers?</summary>

Use two checks. First, write a pure Python unit test with `pytest`. Load the `.j2` file with `jinja2.Environment(loader=FileSystemLoader('templates'), undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)`. Render it against fixture dictionaries that include edge cases, such as 0 GPUs, missing optional variables and hosts spread across several racks. Compare the output with a reviewed golden file, and parse it with `yaml.safe_load`, `kubeconform` or a target config validator. Second, run a local Ansible dry run: `ansible localhost -m ansible.builtin.template -a "src=templates/slurm.conf.j2 dest=/tmp/slurm.conf" -e @tests/fixtures.yml --diff`.
</details>

<details>
<summary>19. What is Server-Side Template Injection (`SSTI`), and how does Ansible's `!unsafe` tag protect against re-templating?</summary>

Server-Side Template Injection, or `SSTI`, happens when untrusted input reaches `Template(user_input).render()`. An HTTP parameter, a pod annotation or remote command output can carry a string such as `{{ lookup('file', '/etc/shadow') }}`, and the attacker can then run lookups or Python methods on the control node. Never render untrusted strings as templates. Pass untrusted values only as context variables into a static template. Ansible tags facts and command output from remote hosts as `!unsafe` (`AnsibleUnsafeText`), so its template engine will not evaluate `{{ ... }}` expressions inside them.
</details>

<details>
<summary>20. How do you prevent secret values rendered by `ansible.builtin.template` from leaking into CI logs or world-readable files?</summary>

1. Set restrictive ownership and permissions on the `template` task: `owner: root`, `group: root` and `mode: "0600"`, or `"0640"` if the service group needs to read the file.
2. Set `no_log: true` and `diff: false` on the task, so a CI run with `--diff` or `-v` does not print the rendered secret plaintext into the build log or a PR comment.
</details>

## Sources and review notes

- **Sources read in full:**
  - `ansible-up-and-running-3rd-edition` — Bas Meijer, Lorin Hochstein & René Moser, *Ansible: Up and Running*, 3rd ed., **Chapter 3: Playbooks: A Beginning** (read in full: YAML start `---` and end `...` markers, comments `#`, strings, multiline `|` vs `>` and `|+` on `visiting_address`, booleans `true`/`false`/`yes`/`no`/`on`/`off`, inline vs block lists and dictionaries, pure YAML task dictionaries vs `key=value` string arguments, and evolving `webservers.yml` into `webservers-tls.yml` with `templates/nginx.conf.j2` and `templates/index.html.j2` using `{{ inventory_hostname }}`, `{{ server_name }}`, `{{ tls_dir }}{{ cert_file }}`, and `notify: Restart nginx`).
  - `network-programmability-and-automation-2nd-edition` — Christian Adell, Scott Lowe, Matt Oswalt & Jason Edelman, *Network Programmability and Automation*, 2nd ed., **Chapter 8: Data Formats and Models** (read in full: structured data vs fragile CLI screen scraping on `show interfaces em0`, markup vs data serialization, decoding/deserializing vs serializing/encoding, YAML syntax and PyYAML, XML/XSD/XPath/XQuery, JSON and JSON Schema `draft/2020-12`, binary Protobuf `.proto`/`protoc`/`protoc-gen-validate` and FlatBuffers vs `pickle`, and YANG RFC 6020 / 7950 `module`, `typedef`, `container`, `list`, `leaf`, `leaf-list`, and OpenConfig) and **Chapter 9: Templates** (read in full: web vs network templating, separating templates from data, Jinja2 `Environment(loader=FileSystemLoader('.'))`, dictionary vs `NetworkInterface` class rendering, switchport trunk/access conditionals and loops, filter chaining `| upper | reverse`, custom Python filter `get_interface_speed`, XSLT with `lxml.etree`, and Go `text/template` with `{{range}}`, pipelines, and `template.FuncMap{"ifparse": IfParse}`).
- **Run here:** `python3 code/part04/yaml_jinja2_templates_lab.py` (4 passed, 0 failed).
- **Explicitly labelled inferences:** The `classify_yaml11_unquoted_scalar`, `apply_yaml_block_chomping`, and `render_slurm_nodes_template` functions in `code/part04/yaml_jinja2_templates.py` and the Slurm/NCCL `.j2` templates are the author's constructions applying *Ansible: Up and Running* Chapter 3 and *Network Programmability and Automation* Chapters 8 & 9 to AI cluster configurations (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, and 35).
- **Not verified on live hardware:** Interactive `yq`, `yamllint`, `kubeconform`, and `ansible-playbook` commands (`1.10`, `010`, `22:30`, `0x1f`, `0644`, `0600`, `550`, `4094`, `1000`, `100`) are marked (`untested here`) where not executed by `yaml_jinja2_templates_lab.py`.
