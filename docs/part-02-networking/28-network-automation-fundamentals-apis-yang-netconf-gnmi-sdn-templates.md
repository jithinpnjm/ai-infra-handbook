---
id: "c02-28"
title: "2.28 Network automation fundamentals: data models, templates, APIs, NETCONF, gNMI and SDN"
sidebar_label: "2.28 Network automation fundamentals: data models, templates, APIs, NETCONF, gNMI and SDN"
sidebar_position: 28
description: "Why and how to automate networks: structured data, YANG, Jinja templates, REST/NETCONF/RESTCONF/gNMI, telemetry, SDN and centralized control planes"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 2.28 Network automation fundamentals: data models, templates, APIs, NETCONF, gNMI and SDN

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Linux VM with Python 3, containerlab/FRR (chapter 2.27), optional SONiC/Arista cEOS images |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

An AI fabric has thousands of ports, hundreds of switches and tens of thousands of cables, and its configuration must be exactly right: a wrong DSCP-to-queue map, a missing PFC priority, one MTU of 1500 among nine thousands, or a leaf with the wrong ASN can degrade a 10,000-GPU job without a single alarm. Humans typing CLI commands cannot keep that consistent. Network automation replaces hand-typed configuration with **data (inventory and intent), templates and models that turn data into configuration, and APIs that deliver and verify it**, all under version control and tested before deployment. This chapter teaches the foundations: why and what to automate, the evolution of management interfaces (SNMP → CLI scraping → NETCONF/RESTCONF → gNMI), structured data formats and data models (YAML, JSON, XML, Protocol Buffers, YANG, JSON Schema), templating (Jinja2 and others), how to work with network APIs from Python, streaming telemetry, and the software-defined networking idea (centralised control planes) in its several forms. Chapter 2.29 covers the tools (Ansible, Nornir, CI/CD, controllers, VNFs) and architectures.

## Prerequisites and outcomes

You should be comfortable with basic Python (Part 3) and Git, and have the routing/switching background of chapters 2.4 to 2.18.

After this chapter you can:

- Explain the benefits and types of network automation (provisioning, data collection, migrations, configuration management, compliance, state validation, reporting, troubleshooting) and the lessons from automation outages.
- Trace the evolution of device interfaces and compare SNMP, CLI/SSH, NETCONF, RESTCONF, gNMI/gRPC, and vendor REST/eAPI.
- Use YAML, JSON and XML in Python; explain binary formats (Protocol Buffers) and when to use them; separate documents from data.
- Define data models with YANG, JSON Schema and XSD; validate data before use; explain OpenConfig and IETF models.
- Write Jinja2 templates with variables, conditionals, loops, filters, inheritance and macros; know when XSLT or Go templates fit.
- Call REST APIs with `requests`/cURL; use NETCONF with `ncclient`, RESTCONF, and gNMI with gNMIc/pygnmi; use Netmiko/Scrapli/NAPALM for CLI-only devices; consume streaming telemetry.
- Design safe automation: idempotency, dry run/diff, validation, staged rollout, rollback, secrets, concurrency.
- Explain SDN and centralised control planes: southbound/northbound interfaces, distributed vs augmented vs hybrid vs replace models, BGP/PCEP/OpenFlow/Fibbing/I2RS examples, subsidiarity and the CAP trade-offs.

## 1. Why automate, and what

### Benefits

- **Simplified architectures and operations**: one tested workflow replaces many hand procedures; operators stop being the integration layer between systems.
- **Deterministic outcomes**: the same input produces the same configuration every time, on every device, so snowflake configs disappear.
- **Business agility**: new racks, tenants, VLANs or BGP peers are provisioned in minutes through a pipeline instead of weeks through tickets.
- **Security and risk reduction**: configuration compliance is checked continuously, access is audited, changes are reviewed, and secrets are handled centrally.
- **Scale**: operations that scale with the number of devices (O(n) typing) become operations that scale with the size of the data model.

A caution from network history: **automating a complex or bad process does not make it simpler; it relocates the complexity** (from human-to-device into human-to-automation-to-device) and can make failures faster and wider. Simplify and standardise first (regular topologies, a few device roles, a small number of templates), then automate.

### Types of automation

| Type | What it does | Examples |
|---|---|---|
| **Device provisioning** | Day-0/day-1 bring-up: base config, management access, loopbacks, routing | ZTP/ONIE/PXE, templated configs, Ansible, `nvue` |
| **Data collection and enrichment** | Gather inventory, state, counters; add metadata (site, role, tenant) | `show` parsing (TextFSM/ntc-templates), NETCONF/gNMI get, SNMP, NetBox sync |
| **Migrations** | Move from one platform/design to another with verification | Config translation, canary rollouts, pre/post state diffs |
| **Configuration management** | Keep devices matching intended config; push changes | Templates → push → verify → commit |
| **Configuration compliance** | Compare running config with policy/golden config; report or remediate | Batfish, custom diff, `napalm compare_config`, CIS-style rules |
| **State validation** | Check operational state matches intent (BGP up, ECMP width, LLDP neighbours, MTU, optics levels) | pyATS, Suzieq, custom assertions, test suites |
| **Reporting** | Inventory, capacity, compliance dashboards | HTML reports, Grafana, CMDB |
| **Troubleshooting** | Automated data gathering on alarm; guided diagnosis | ChatOps, runbooks as code, packet capture triggers |

### Lessons learned from a network automation outage

Typical failure pattern: an automation job with a mistake in data or logic is applied to all devices at once; every device accepts it; connectivity to management is lost; recovery requires console access everywhere. Remedies: **canary and staged rollouts** (one device, one rack, one pod, then everything), **pre-checks** (is the device healthy? is this change safe?), **post-checks with automatic rollback**, **commit-confirmed / candidate configurations** where the platform supports them, **blast-radius limits** (maximum percentage of devices per batch, per-failure-domain batching), **out-of-band management** that does not depend on the production network, **change windows and freeze rules**, code review of both templates and data, and **tests in a lab/emulation** (chapter 2.27). Treat the automation system itself as production software.

## 2. The evolution of device management interfaces

| Era | Interface | Strengths | Weaknesses |
|---|---|---|---|
| 1990s | **SNMP** (v1/v2c/v3; MIBs; UDP 161/162 polling and traps) | Ubiquitous for monitoring; standard MIBs | Poor for configuration; polling overhead; numeric OIDs; v2c has weak security; vendor MIB sprawl |
| 1990s to now | **SSH/Telnet and the CLI** ("screen scraping") | Works on everything; what humans use | Unstructured text output; version-dependent; fragile parsing; no transactions |
| 2006+ | **NETCONF** (RFC 6241; XML over SSH, port 830) | Structured, transactional (datastores, candidate, commit, lock, rollback), model-driven (YANG) | XML verbosity; uneven vendor support; stateful sessions |
| 2017+ | **RESTCONF** (RFC 8040; HTTP/HTTPS + JSON/XML on YANG models) | Uses familiar HTTP tooling; easy for developers | Single-target, single-shot (no network-wide transactions, no locking) |
| 2016+ | **gRPC/gNMI** (OpenConfig; HTTP/2 + Protocol Buffers) | Efficient binary encoding, streaming telemetry, multiplexed calls, strong typing | Needs protobuf/gRPC tooling; model support varies |
| now | **Vendor REST APIs and eAPI/NX-API/Meraki/Cumulus NVUE** | Easy and device-specific | Not portable; vary by vendor/version |
| now | **Open networking/Linux NOS** (SONiC, Cumulus, FRR) | Standard Linux tooling (ssh, systemd, files, netlink); Ansible/Python native; Redis-based config DB in SONiC | Different operational model; feature gaps |

Why APIs instead of the CLI: the CLI is designed for human eyes; output formats change between releases; parsing requires brittle regexes; there is no atomic way to apply a multi-line change or to roll back. Model-driven APIs return and accept **structured data conforming to a schema**, so the same code can talk to many devices.

**Impact of open networking.** When the network operating system is Linux (SONiC, Cumulus, ONIE-installed images on white-box switches), automation reuses server practices: package management, systemd, configuration files, Git, Ansible, and eBPF/netlink observability. The management plane converges with infrastructure-as-code (Part 4).

## 3. Structured data formats

### Why structured data

Automation needs data that is **structured** (machine-parsable with known fields and types), **supported** (libraries exist in every language), and **portable** (readable across tools and systems). Compare `show interface` text with the same facts as data:

```json
{ "name": "Ethernet1", "admin_state": "up", "oper_state": "up", "mtu": 9214, "speed_gbps": 400,
  "ipv4": [ { "address": "10.0.1.1", "prefix": 31 } ], "counters": { "in_octets": 123456789, "in_errors": 0 } }
```

Distinguish **documents** (human-oriented text/reports: free layout, meant to be read) from **data** (typed fields that can be queried, validated and combined). Categories of data formats: **text-based** (human-readable and diffable: YAML, JSON, XML, TOML, INI, CSV) and **binary** (compact and fast: Protocol Buffers, Apache Thrift, FlatBuffers, BSON, MessagePack, CBOR, Python pickle). Working with them means **deserialising** (decoding text/binary into native objects in memory) and **serialising** (encoding objects back to text/binary).

### YAML

Human-friendly, indentation-based, supports comments (`#`), anchors/aliases, multi-document files; the default format for **inventory, variables and intent** (Ansible, Kubernetes, NetBox exports, cloud-init).

```yaml
# group_vars/leaf.yml
role: leaf
bgp: { asn: 65101, router_id: 10.255.0.11 }
interfaces:
  - { name: Ethernet1, description: to-spine1, mtu: 9214, ipv4: 10.0.1.1/31 }
  - { name: Ethernet2, description: to-spine2, mtu: 9214, ipv4: 10.0.2.1/31 }
vlans: [ 100, 200 ]
```

```python
import yaml                                   # pip install pyyaml
data = yaml.safe_load(open("group_vars/leaf.yml"))     # always safe_load, never load() on untrusted input
print(data["bgp"]["asn"], [i["name"] for i in data["interfaces"]])
yaml.safe_dump(data, open("out.yml", "w"), sort_keys=False)
```

Pitfalls: significant whitespace (tabs are errors), implicit typing (the "Norway problem": `no`/`NO` parsed as boolean false; `010` as octal; `1.10` as a float): quote strings that could be misread; indentation errors; anchors hiding duplication. Use `yamllint` in CI.

### XML

Verbose, tag-based, supports attributes, namespaces and schemas; the native encoding of NETCONF and many older APIs.

```xml
<interface xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
  <name>Ethernet1</name><enabled>true</enabled><mtu>9214</mtu>
</interface>
```

```python
import xml.etree.ElementTree as ET
root = ET.fromstring(xml_text)
ns = {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"}
for i in root.findall(".//if:interface", ns): print(i.find("if:name", ns).text)
# or lxml / xmltodict for convenience: xmltodict.parse(xml_text) -> dict
```

XPath and **XSLT** (W3C stylesheets that transform XML into other XML/text) are the XML-native query and templating tools; useful for transforming NETCONF replies.

### JSON

Lightweight, ubiquitous on the web; types: object, array, string, number, boolean, null; **no comments**, no trailing commas. The default for REST APIs, RESTCONF (alongside XML), OpenConfig JSON encodings and `ip -j` output.

```python
import json, requests
doc = json.loads(text); print(json.dumps(doc, indent=2, sort_keys=True))
r = requests.get("https://sw1/restconf/data/ietf-interfaces:interfaces", auth=("u", "p"), headers={"Accept": "application/yang-data+json"}, verify="/etc/ssl/ca.pem", timeout=10)
r.raise_for_status(); ifaces = r.json()["ietf-interfaces:interfaces"]["interface"]
```

Tools: `jq` (filtering/transforming on the CLI), `jsonpath`, `jmespath` (used by Ansible/AWS CLI), `json.tool`.

### Binary formats: Protocol Buffers

**Protocol Buffers (protobuf)** define a schema in `.proto` files, compile to code for many languages, and encode compactly with numeric field tags (forward/backward compatible). They are the encoding of gRPC and gNMI.

```proto
syntax = "proto3";
message Interface { string name = 1; bool enabled = 2; uint32 mtu = 3; repeated string addresses = 4; }
```

```bash
protoc --python_out=. interface.proto        # generate interface_pb2.py
```

```python
import interface_pb2
i = interface_pb2.Interface(name="Ethernet1", enabled=True, mtu=9214, addresses=["10.0.1.1/31"])
blob = i.SerializeToString(); j = interface_pb2.Interface(); j.ParseFromString(blob)
```

Binary formats win on size and speed (telemetry at high rates), typed schemas and cross-language code generation; they lose on human readability and ad hoc debugging (use `protoc --decode`, `grpcurl`, or JSON mappings). Others: **Thrift** (RPC + serialisation), **FlatBuffers** (zero-copy access), **BSON** (MongoDB), **Pickle** (Python-only and unsafe on untrusted input: never unpickle network data). Choose by need: human/Git/config → YAML/JSON; web APIs → JSON; streaming telemetry/RPC → protobuf.

## 4. Data modelling

A **data model** is a formal description of what data may exist: names, types, ranges, relationships, constraints. It lets tools validate inputs before they reach a device, generate code and documentation, and keep different systems consistent.

### YANG

**YANG** (RFC 7950) is the modelling language for network configuration and state. A YANG module defines a **tree** of containers, lists, leaves and leaf-lists with types, constraints (ranges, patterns, `must`/`when`, keys), RPCs and notifications. The same model is encoded as XML (NETCONF) or JSON (RESTCONF) and referenced by gNMI paths.

```yang
module example-interfaces {
  namespace "urn:example:interfaces"; prefix ex;
  container interfaces {
    list interface {
      key "name";
      leaf name    { type string; }
      leaf enabled { type boolean; default true; }
      leaf mtu     { type uint16 { range "68..9216"; } }
      leaf-list ipv4-address { type string; }
    }
  }
}
```

Model families: **IETF** (standards-track, e.g. `ietf-interfaces`, `ietf-ip`, `ietf-routing`), **OpenConfig** (operator-driven, vendor-neutral, `openconfig-interfaces`, `openconfig-bgp`, `openconfig-network-instance`, with gNMI telemetry focus), and **native vendor models** (Cisco-IOS-XE-native, Junos, Arista EOS). Tools: `pyang` (validate, tree view `pyang -f tree`, generate XML skeletons and JSON schemas), `yanglint`, `pyangbind` (Python classes from YANG), `ygot` (Go), the YANG catalog and OpenConfig GitHub repository.

### JSON Schema and XSD

For custom data (your inventory and intent, not device models) **JSON Schema** (usable with YAML data too) validates structure and values:

```json
{ "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object", "required": ["hostname", "vlans"],
  "properties": {
    "hostname": { "type": "string", "pattern": "^[a-z0-9-]+$" },
    "dns_servers": { "type": "array", "items": { "type": "string", "format": "ipv4" } },
    "vlans": { "type": "array", "items": { "type": "integer", "minimum": 1, "maximum": 4094 } } } }
```

```python
from jsonschema import validate, ValidationError   # pip install jsonschema
validate(instance=data, schema=schema)              # raises ValidationError with a path to the bad value
```

**XSD** (XML Schema Definition) is the XML equivalent. **Protobuf** definitions are themselves a schema (and tooling like `buf` lints/breaks-checks them). Validate *at the pipeline edge* (CI) and again before pushing; reject on error. Pydantic, `cerberus`, and `voluptuous` are Python-native alternatives (Part 3).

## 5. Templates

Templates combine **static text with placeholders and logic** to render configuration from data. Web development popularised them (Jinja, Django templates, Handlebars); network automation uses them to generate device configs, reports and API payloads. Value: one template per role (leaf, spine, border), data per device, consistent output, review of templates once instead of every config.

### Jinja2

```python
from jinja2 import Environment, FileSystemLoader, StrictUndefined
env = Environment(loader=FileSystemLoader("templates"), undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
print(env.get_template("leaf.j2").render(**data))
```

```jinja
{# templates/leaf.j2 #}
hostname {{ hostname | lower }}
!
{% for i in interfaces %}
interface {{ i.name }}
 description {{ i.description | default("unused") }}
 mtu {{ i.mtu | default(9214) }}
 {% if i.ipv4 is defined %}
 ip address {{ i.ipv4 }}
 {% else %}
 switchport mode access
 {% endif %}
 {{ "shutdown" if not i.get("enabled", true) else "no shutdown" }}
!
{% endfor %}
router bgp {{ bgp.asn }}
 router-id {{ bgp.router_id }}
{% for n in bgp.neighbors | default([]) %}
 neighbor {{ n.ip }} remote-as {{ n.asn }}
{% endfor %}
```

Key features:

- **Variables** `{{ x.y }}`, **comments** `{# ... #}`, **statements** `{% ... %}`.
- **Conditionals** (`if/elif/else`), **loops** (`for`, `loop.index`, `loop.first`, `else` for empty), iteration over dicts (`.items()`), nested data; **tests** (`is defined`, `is none`, `is iterable`).
- **Filters**: built-ins (`upper`, `lower`, `default`, `join`, `sort`, `unique`, `map`, `selectattr`, `tojson`, `ipaddr`-like via plug-ins) with chaining; **custom filters** in Python (`env.filters["cidr_to_mask"] = fn`) for network logic (netmask conversion, address arithmetic with `ipaddress`); Ansible adds `ipaddr`/`ansible.utils.ipaddr`, `ipmath`.
- **Template inheritance** (`{% extends "base.j2" %}` with `{% block %}`) and **includes/macros** (`{% macro bgp_neighbor(n) %}`) for reuse; **import** shared macros.
- **Whitespace control** (`trim_blocks`, `lstrip_blocks`, `-` markers) matters because configs are whitespace-sensitive.
- **Safety**: use `StrictUndefined` so missing variables raise errors instead of rendering blanks; autoescape is for HTML, not configs; never render untrusted templates (sandbox: `jinja2.sandbox.SandboxedEnvironment`).

### Other template languages

**XSLT** transforms XML (NETCONF replies, XML configs) with declarative rules (`xsl:template match`, `xsl:for-each`, `xsl:if`, `xsl:sort`) and is built into Junos commit scripts and many XML toolchains; **Go `text/template`** renders structs/maps for Go tools (e.g. gNMIc, Terraform providers in Go, Helm charts use Go templates for Kubernetes manifests); **Mako/Cheetah/Tera/Handlebars** appear in specific tools. Template pitfalls: logic in templates grows unmaintainable; keep complex logic in Python (data preparation), keep templates declarative; always render to a file and **diff** against the running config; unit-test templates with fixtures and expected outputs.

### Source of truth and the data pipeline

A durable design: **source of truth** (NetBox, Nautobot, a Git repository of YAML) → **intent/validated data** (schemas) → **templates** → **rendered artefacts** → **delivery** (API/CLI/Ansible) → **verification** (state assertions, telemetry). Keep inventory (devices, interfaces, IP/VLAN assignments, cables) separate from policy (BGP design, QoS) and from secrets (Vault, SOPS). Data enrichment (e.g. derive the P2P /31 addresses, loopbacks, ASNs, VNIs from role + index using a deterministic allocation function) removes manual addressing errors.

## 6. Working with network APIs

### REST fundamentals

REST (representational state transfer) is a style of HTTP API: **client-server**, **stateless** requests (each carries all needed context), a **uniform interface** (resources identified by URLs, manipulated through standard methods), cacheable, layered. Methods: `GET` (read configuration or state), `PUT` (create or replace a resource, idempotent), `PATCH` (partial update/merge), `POST` (create a child resource or invoke an action; not idempotent), `DELETE`. Response classes: 1xx informational, 2xx success (200 OK, 201 Created, 204 No Content), 3xx redirect, 4xx client error (400 bad request, 401 unauthenticated, 403 forbidden, 404 not found, 409 conflict, 422 unprocessable, 429 rate limited), 5xx server error. Many "REST" network APIs are not strictly RESTful (RPC-style endpoints, custom verbs); treat each vendor's documentation as authoritative.

```bash
curl -sk -u admin:$PW -H 'Accept: application/yang-data+json' https://sw1/restconf/data/ietf-interfaces:interfaces/interface=Ethernet1 | jq .
curl -sk -u admin:$PW -X PATCH -H 'Content-Type: application/yang-data+json' https://sw1/restconf/data/ietf-interfaces:interfaces/interface=Ethernet1 \
     -d '{"ietf-interfaces:interface": {"name": "Ethernet1", "enabled": true, "description": "uplink"}}'
curl -v ... ; curl --cacert ca.pem ... ; curl -w '%{http_code}\n' -o /dev/null -s ...
```

Authentication: HTTP basic over TLS, bearer tokens/API keys, session cookies, OAuth2/mTLS for modern controllers; never disable TLS verification in production (chapter 2.10).

### NETCONF

**NETCONF** (RFC 6241) is a layered protocol:

| Layer | Content |
|---|---|
| Content | Configuration and state data, modelled by YANG (encoded as XML) |
| Operations | `get`, `get-config`, `edit-config`, `copy-config`, `delete-config`, `lock`/`unlock`, `commit`, `discard-changes`, `validate`, `close-session`, `kill-session`, plus RPCs defined by YANG |
| Messages | `<rpc>`, `<rpc-reply>`, `<notification>` (framing with message IDs) |
| Transport | SSH (subsystem `netconf`, default port 830; also TLS, historically BEEP/SOAP) |

Concepts: **datastores** (`running`, `candidate`, `startup`): changes are made to `candidate`, validated, then `commit`ed atomically, optionally with a `confirmed-commit` that auto-rolls back unless confirmed; **locks** prevent concurrent editors; **capabilities** exchanged in the hello message (`:candidate`, `:validate`, `:confirmed-commit`, `:rollback-on-error`, `:xpath`, `:notification`, YANG library); **edit operations** per node (`merge`, `replace`, `create`, `delete`, `remove`).

```python
from ncclient import manager                 # pip install ncclient
cfg = """<config><interfaces xmlns="http://openconfig.net/yang/interfaces"><interface>
  <name>Ethernet1</name><config><name>Ethernet1</name><mtu>9214</mtu><description>to-spine1</description></config>
</interface></interfaces></config>"""
with manager.connect(host="sw1", port=830, username="admin", password=PW, hostkey_verify=True, timeout=30) as m:
    print([c for c in m.server_capabilities if "candidate" in c])
    with m.locked("candidate"):
        m.edit_config(target="candidate", config=cfg, default_operation="merge")
        m.validate(source="candidate")
        print(m.compare_config() if hasattr(m, "compare_config") else "")
        m.commit(confirmed=True, timeout="120")       # auto-rollback in 120 s unless confirmed
        # ...verify state; then:
        m.commit()                                    # confirming commit
```

Vendor notes: Junos supports NETCONF natively (candidate + commit confirmed + `compare` rollback diff); Cisco IOS XE, NX-OS, IOS XR, Arista EOS and Nokia SR OS support NETCONF with native and/or OpenConfig models (capabilities differ); always read the device's advertised capabilities and YANG library.

### RESTCONF

**RESTCONF** (RFC 8040) maps NETCONF datastore operations onto HTTP for YANG-modelled data: `GET /restconf/data/<module>:<container>/<list>=<key>`, `PUT/POST/PATCH/DELETE`, with media types `application/yang-data+json|xml`, and `/restconf/operations` for RPCs. It is **single-target, single-shot**: no network-wide transactions, no locking or candidate datastore (changes apply directly to running), but familiar tooling (curl, requests). **YANG PATCH** (RFC 8072) is a media type (`application/yang-patch+json`) carrying multiple edits in one request with edit IDs, operations and targets. Discover supported modules at `/restconf/data/ietf-yang-library:modules-state` (or `yang-library`). Cisco IOS XE exposes the full native model plus IETF/OpenConfig; Arista and others have RESTCONF in some releases.

### gRPC and gNMI

**gRPC** (Google RPC) uses HTTP/2 and Protocol Buffers: high performance, payload-agnostic, multiple communication patterns (unary, server streaming, client streaming, bidirectional streaming), language independence via code generation, TLS/mTLS built in. **gNMI** (gRPC Network Management Interface, OpenConfig) defines a small service: `Capabilities` (supported models, encodings, gNMI version), `Get`, `Set` (update/replace/delete with transactional semantics for the request), and `Subscribe` (streaming telemetry: `STREAM`, `ONCE`, `POLL`; sampled or on-change). Paths are YANG-based (`/interfaces/interface[name=Ethernet1]/state/counters`), encodings include JSON, JSON_IETF, PROTO, ASCII. Related: **gNOI** (operations: reboot, OS install, file, cert), **gNSI** (security), **gRIBI** (RIB injection), **P4Runtime**.

```bash
# gNMIc (openconfig/gnmic): capabilities, get, set, subscribe
gnmic -a sw1:6030 -u admin -p $PW --skip-verify capabilities
gnmic -a sw1:6030 -u admin -p $PW --skip-verify get --path /interfaces/interface[name=Ethernet1]/state/oper-status
gnmic -a sw1:6030 -u admin -p $PW --skip-verify set --update-path /interfaces/interface[name=Ethernet1]/config/mtu --update-value 9214
gnmic -a sw1:6030 -u admin -p $PW --skip-verify subscribe --path /interfaces/interface/state/counters --stream-mode sample --sample-interval 10s
gnmic ... --encoding json_ietf ... ; gnmic ... -e proto
```

```python
from pygnmi.client import gNMIclient          # pip install pygnmi
with gNMIclient(target=("sw1", 6030), username="admin", password=PW, insecure=False, path_cert="ca.pem") as gc:
    print(gc.capabilities()["supported_models"][:3])
    r = gc.get(path=["/interfaces/interface[name=Ethernet1]/state"])
    gc.set(update=[("/interfaces/interface[name=Ethernet1]/config/mtu", 9214)])
```

### Comparing the model-driven protocols

| | NETCONF | RESTCONF | gNMI |
|---|---|---|---|
| Encoding | XML | JSON or XML | JSON/JSON_IETF/PROTO (protobuf) |
| Transport | SSH (TLS) | HTTP(S) | gRPC over HTTP/2 + TLS |
| Transaction scope | Network-wide capable per session (lock, candidate, commit) | Single target, single shot | Single target, single request (Set is atomic per request), sequenced |
| Streaming telemetry | Notifications (limited) | SSE/notifications (limited) | Native Subscribe (sample/on-change) |
| Model use | YANG | YANG | YANG paths (OpenConfig focus) |
| Tooling | ncclient, Ansible netconf, Netconf-console | curl, requests, Ansible httpapi | gNMIc, pygnmi, Telegraf, vendor SDKs |
| Best for | Configuration with transactions | Simple CRUD, web developers | High-rate telemetry and modern config |

**Network interface development lifecycle:** IETF models are standards-track but slow; OpenConfig models are operator-driven and fast moving with vendor deviations; native models expose everything but are not portable. Pragmatic automation uses OpenConfig/IETF where the platform supports it well and native/CLI where it doesn't, hidden behind a thin abstraction layer.

### Streaming (model-driven) telemetry

Instead of polling SNMP every minute, devices **push** counters and state at high resolution: **dial-in** (collector connects with gNMI Subscribe) or **dial-out** (device connects to a collector, vendor-specific over gRPC or UDP/TCP). Data goes to collectors (gNMIc, Telegraf `gnmi` input, Cisco Pipeline, Juniper JTI + Telegraf/OpenNTI) and time-series stores (Prometheus via exporters, InfluxDB, VictoriaMetrics), then dashboards/alerts (chapter 2.31). Benefits: 1 to 10 s granularity (microburst-adjacent visibility needs more), on-change events (link flaps, BGP state), less device CPU than polling at scale, typed data. Costs: volume (cardinality), collector scaling, model/path differences across vendors, clock sync.

### Python (and Go) libraries

| Task | Libraries |
|---|---|
| HTTP/REST | `requests`, `httpx`; Go `net/http` |
| NETCONF | `ncclient`; Go `scrapligo`/`go-netconf` |
| gNMI | `pygnmi`, `grpcio` + generated stubs; Go `gnmic` library / `openconfig/gnmi` |
| CLI over SSH | `netmiko` (multi-vendor), `scrapli` (fast, async), `paramiko` (low level), `pexpect` |
| Multi-vendor abstraction | `napalm` (get_facts, get_bgp_neighbors, compare_config/commit/rollback), `nornir` (tasks and inventory, chapter 2.29) |
| Parsing | `textfsm` + `ntc-templates`, `genie`/`pyATS` parsers, `ttp` |
| Data/modelling | `pyyaml`, `ruamel.yaml`, `jsonschema`, `pydantic`, `pyang`, `pyangbind`, `ipaddress`, `netaddr` |
| Templating | `jinja2` |
| Testing/validation | `pytest`, `batfish` (pybatfish), `suzieq`, `pyATS`, `scapy` |

Example, safe CLI fallback with Netmiko:

```python
from netmiko import ConnectHandler
dev = {"device_type": "arista_eos", "host": "sw1", "username": "admin", "password": PW, "fast_cli": True}
with ConnectHandler(**dev) as c:
    before = c.send_command("show running-config | section router bgp")
    out = c.send_config_set(["router bgp 65101", "neighbor 10.0.1.0 maximum-routes 1000"])
    c.save_config()
    print(c.send_command("show ip bgp summary", use_textfsm=True))     # structured output via ntc-templates
```

Rules for safe scripts: timeouts and retries with backoff; per-device error isolation (one failure must not abort the batch silently); idempotency (compute desired vs current and change only the difference); `--dry-run`/diff mode by default; commit-confirmed or backup+restore; logging every change with a ticket/commit ID; secrets from environment/Vault (not code); concurrency limits (threads/asyncio, per-failure-domain batches); verification after change; and unit tests with mocked devices.

## 7. Software-defined networking and centralised control planes

Network designs have swung between fully distributed and centralised control planes more than once. "SDN" is often presented as either/or (distributed protocols versus a controller), but every routing protocol is "software"; the useful definition is: **SDN moves some part of the control plane's functionality off the individual forwarding devices into a logically centralised component** ("centralised" meaning not carried hop by hop and not computed independently by every device, rather than a single "god box").

### Interfaces

- **Southbound interface**: between the controller and network devices (BGP, NETCONF/gNMI, PCEP, OpenFlow, P4Runtime, OVSDB, vendor APIs, I2RS).
- **Northbound interface**: between the controller and applications/business logic (REST/gRPC APIs, intent languages, GitOps).

### Four models of interaction

| Model | Description | Examples |
|---|---|---|
| **Distributed** | Control plane runs on the forwarding devices (possibly disaggregated software, but still on the device) | OSPF/IS-IS/BGP everywhere |
| **Augmented** | Distributed control plane remains; off-box processes influence the paths installed in the RIB | PCE, BGP controllers injecting routes, Fibbing, I2RS |
| **Hybrid** | A centralised control plane runs in parallel with the distributed one; each appears to the other as just another control plane | Controller speaking BGP/OpenFlow alongside OSPF |
| **Replace** | No distributed control plane; the controller programs the FIB directly | Classic OpenFlow, P4Runtime fabrics |

### Division of labour

A control plane supplies **topology**, **reachability** and **policy**. Topology and reachability are entangled (RIP and EIGRP combine them; in IS-IS reachability hangs off the shortest-path tree as leaves). **Policy**, however, only *modifies* what topology and reachability computed, so it separates naturally into an upper layer. Hence a common pattern: keep a distributed lower layer (topology + reachability) for resilience and speed, and add centralised policy for traffic engineering, segmentation and intent. Questions to ask of any SDN design: which functions are centralised, what happens when the controller (or its connectivity) fails, how fast can it react, how does it scale, and what is the complexity cost?

### Examples

- **BGP as an SDN**: with BGP already running fabric-wide, a controller joins as an iBGP/eBGP speaker, reads the topology, and *injects* better-metric paths hop by hop to pin a flow to a chosen path (the augmented model, where the same protocol carries topology/reachability and policy). Simple to deploy; but automating a complicated process doesn't remove its complexity, it relocates it.
- **Fibbing**: with link-state protocols, tags are never used for traffic engineering because all routers must hold the same database. Fibbing has a controller join the IGP and inject **fake nodes and links** (OSPF external LSAs that can carry a third-party next hop) so that the unmodified shortest-path computation produces the desired path; for example, a chain of fake nodes with lowered costs and specific forwarding addresses steers A to H along a longer but desired route. No protocol changes; limited to what external routes can express; watch for scale of injected LSAs.
- **PCEP** (Path Computation Element Protocol): a central PCE computes paths for MPLS/SR LSPs and tells headends (PCC) via PCEP; headends signal or encode them (augmented model; SR policies).
- **I2RS** (Interface to the Routing System): a standardised programmatic interface for off-box applications to read and write routing state (RIB), with ephemeral state and fast, event-driven interaction.
- **OpenFlow**: a southbound protocol for controllers to install match-action flow entries directly in switches' flow tables (replace model); powerful but suffered scaling, table-size and failure-handling issues; its ideas live on in P4/P4Runtime and in virtual switches (OVS, OVN).
- **Controller-based fabrics and overlays**: EVPN route servers, cloud SDN (VPC controllers), Kubernetes CNI control planes, OVN, SD-WAN controllers.

### CAP and subsidiarity

A centralised control plane is a distributed database problem: during a partition you cannot have both consistency and availability (the **CAP theorem**, with network partitions inevitable). Hence the **subsidiarity principle**: decisions should be made at the lowest level able to make them correctly, centralising only what truly needs a global view. In practice: keep fast, local, safety-critical reactions (failure detection, ECMP rerouting, fast reroute) in the distributed layer; centralise slow-changing, global-optimisation policy (traffic engineering, intent, segmentation); and make sure the network keeps forwarding if the controller disappears (fail static or fail back to the distributed control plane).

## 8. Putting it together: a minimal automation pipeline

```mermaid
flowchart LR
  SoT["Source of truth\n(Git YAML / NetBox)"] --> V["Validate\n(JSON Schema, pydantic)"]
  V --> R["Render\n(Jinja2 templates)"]
  R --> T["Test\n(emulation: containerlab, Batfish, unit tests)"]
  T --> D["Deliver\n(NETCONF/gNMI/REST/CLI, staged)"]
  D --> C["Verify\n(state assertions, telemetry)"]
  C -->|fail| RB["Rollback / alert"]
  C -->|pass| M["Monitor and detect drift"]
  M --> SoT
```

Example mini-project (the lab below): generate FRR/SONiC-style configs for the leaf-spine fabric from a YAML inventory, validate with JSON Schema, render with Jinja2, apply to the containerlab nodes via `docker exec`/vtysh or NETCONF-capable images, and assert BGP/ECMP state with a validation script (chapter 2.27, lab 7).

## 9. Lab: data, templates and APIs (untested)

1. **Formats**: represent one switch's interface table in YAML, JSON and XML; convert among them with `yq`, `jq`, `xmltodict`; round-trip through Python; observe type differences (the YAML Norway problem; JSON no comments).
2. **Schema validation**: write a JSON Schema for the fabric inventory (VLAN range, ASN range, hostnames, IPv4 prefixes); write failing and passing examples; add a pytest that validates all files in `inventory/`.
3. **Jinja2**: write a leaf template with loops and conditionals, a custom filter converting a CIDR to netmask, a macro for BGP neighbours, an `extends` base; render with `StrictUndefined`; show the error for a missing variable; build a golden-file test.
4. **REST**: stand up a mock device API (FastAPI/Flask returning interface JSON) and write a client with `requests` (timeouts, retries, TLS), plus a `curl` session exercising GET/PUT/PATCH/DELETE and error codes.
5. **YANG**: write the small module above; validate with `pyang`; print the tree; generate a JSON schema; build sample data and validate it against the model (`yanglint`).
6. **NETCONF**: run a NETCONF-capable device (an Arista cEOS or Nokia SR Linux container in containerlab, or a Junos vMX/cRPD lab if licensed); use `ncclient` to read capabilities, `get-config`, `edit-config` to candidate, `commit confirmed`, and observe rollback by not confirming.
7. **gNMI**: use `gnmic` against SR Linux or cEOS: `capabilities`, `get`, `set`, and a `subscribe` stream into Prometheus (gNMIc `output prometheus`) with a Grafana panel of interface counters.
8. **CLI fallback**: use Netmiko/Scrapli against an FRR container (`vtysh`) or a Linux switch to parse `show bgp summary json`; write an idempotent function that ensures a neighbour exists.
9. **Safe rollout**: write a script that applies a change to leaves one by one with post-checks (ECMP width, BGP sessions), halts on failure and rolls back; test with an injected bad change.
10. **Fibbing/controller toy**: using FRR containers, write a small Python program that injects a more-preferred route via a BGP session (ExaBGP or `vtysh`) to pin a path; verify with traceroute; discuss limits.
11. **Clean up.**

Mark tested only after execution.

## 10. Common mistakes

- Parsing CLI output with regexes in production when structured APIs exist; assuming CLI formats never change.
- Treating YAML as always safe (implicit typing, `yaml.load` on untrusted data).
- Unvalidated data flowing into templates; missing-variable renders; secrets in repositories.
- Pushing to all devices at once; no canary, no rollback, no out-of-band access.
- One monolithic template full of logic; no tests or golden files.
- Believing NETCONF-capable means portable: models and capabilities differ per vendor and version.
- Over-centralising (controller as a single point of failure) or under-specifying failure behaviour.
- Automating undocumented, inconsistent networks before simplifying them.

## 11. Interview angles

- "Why NETCONF/gNMI instead of SSH and screen scraping? Differences among NETCONF, RESTCONF and gNMI?"
- "What is YANG? What are IETF vs OpenConfig vs native models?"
- "Design an automation pipeline for a leaf-spine fabric. Where do tests and rollbacks happen?"
- "How would you roll out a global MTU or QoS change safely to 500 switches?"
- "What is idempotency and why does it matter for network automation?"
- "When would you use YAML vs JSON vs protobuf?"
- "What is SDN? Explain augmented vs hybrid vs replace controller models. What happens if the controller fails?"
- "How does streaming telemetry differ from SNMP polling?"
- "How do you validate that the network matches intent?"

## 12. Checkpoint questions (40)

1. Name five types of network automation. **A:** Provisioning, data collection, migration, configuration management, compliance, validation, reporting, troubleshooting.
2. Why can automation make failures worse? **A:** It applies mistakes fast and wide; complexity is relocated, not removed.
3. Name two safeguards. **A:** Canary/staged rollout; commit-confirmed/rollback; pre/post checks.
4. Why is SNMP weak for configuration? **A:** MIB sprawl, polling, limited write semantics, security.
5. Port for NETCONF over SSH? **A:** 830.
6. What datastores does NETCONF define? **A:** running, candidate, startup.
7. Purpose of `commit confirmed`? **A:** Auto-rollback unless confirmed.
8. RESTCONF media types? **A:** `application/yang-data+json|xml`.
9. YANG PATCH is a method or media type? **A:** Media type.
10. gNMI RPCs? **A:** Capabilities, Get, Set, Subscribe.
11. gNMI transport/encoding? **A:** gRPC over HTTP/2 with protobuf (JSON also).
12. What is dial-out telemetry? **A:** Device connects to the collector and pushes data.
13. What is YAML best for? **A:** Human-edited inventory/intent.
14. YAML pitfall? **A:** Implicit typing and indentation (e.g. `no` becomes false).
15. Which loader is safe? **A:** `yaml.safe_load`.
16. JSON lacks what? **A:** Comments (and trailing commas).
17. What are XML namespaces for? **A:** Disambiguate element names across models.
18. Protocol Buffers advantage? **A:** Compact typed binary with code generation and compatibility.
19. Why never unpickle untrusted data? **A:** Arbitrary code execution.
20. What is a data model? **A:** Formal definition of data structure, types and constraints.
21. What does YANG define? **A:** Containers, lists, leaves, types, constraints, RPCs, notifications.
22. IETF vs OpenConfig? **A:** Standards-track vs operator-driven vendor-neutral models.
23. What is JSON Schema used for? **A:** Validating JSON/YAML data.
24. Jinja delimiters? **A:** `{{ }}` expressions, `{% %}` statements, `{# #}` comments.
25. Why `StrictUndefined`? **A:** Fail on missing variables.
26. What is template inheritance? **A:** Child templates extend a base and override blocks.
27. Custom filter example? **A:** CIDR to netmask conversion.
28. When XSLT? **A:** Transforming XML (NETCONF replies, XML config).
29. What is Netmiko? **A:** Multi-vendor SSH CLI library.
30. What is NAPALM? **A:** Multi-vendor abstraction with config compare/commit/rollback.
31. What is idempotency? **A:** Applying twice yields the same state as once.
32. What is a dry run? **A:** Show the diff without applying.
33. Southbound vs northbound? **A:** Controller-to-device vs controller-to-application.
34. Four SDN models? **A:** Distributed, augmented, hybrid, replace.
35. What is Fibbing? **A:** Injecting fake nodes/LSAs into an IGP to steer paths.
36. What does PCEP do? **A:** PCE tells headends computed paths.
37. What is OpenFlow? **A:** Protocol for controllers to program flow tables.
38. CAP theorem in one line? **A:** Under partition choose consistency or availability.
39. Subsidiarity principle? **A:** Decide at the lowest level that can decide correctly.
40. What should happen if the controller fails? **A:** Network keeps forwarding (fail static / distributed fallback).

## 13. Sources and review notes

**Written in original words.** Principal sources:

- Christian Adell, Scott S. Lowe, Jason Edelman and Matt Oswalt, *Network Programmability and Automation*, 2nd ed.: chapter 2 (network automation: types, benefits, lessons from an outage, evolution from SNMP to APIs, open networking, SDN era), chapter 8 (data formats and models: structured data, YAML/XML/JSON, binary formats and protobuf, YANG, JSON Schema, XSD), chapter 9 (templates: Jinja, filters, inheritance, XSLT, Go templates), chapter 10 (working with network APIs: REST, NETCONF, RESTCONF, gRPC and gNMI, comparison, telemetry, Python and Go clients).
- Russ White and Jeff Tantsura (with co-authors), *Computer Networking Problems and Solutions*, chapter 18 (centralised control planes: definition of software defined, taxonomy of interfaces, division of labour, BGP as an SDN, Fibbing, I2RS, PCEP, OpenFlow, CAP theorem and subsidiarity).
- Example code and tables are the author's constructions; protocol details follow RFCs 6241, 8040, 8072, 7950, the OpenConfig/gNMI specification and library documentation.

**Flagged for verification before publishing:** library APIs and versions (ncclient, pygnmi, netmiko, napalm), vendor NETCONF/gNMI support and port numbers, gNMIc flag names, YANG tooling syntax, and every command and code listing; all labs are **untested**.
