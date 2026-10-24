---
id: "c07-06"
title: "7.6 The Redfish schema: reading CSDL, JSON Schema and the Resource Guide"
sidebar_label: "7.6 The Redfish schema: reading CSDL, JSON Schema and the Resource Guide"
sidebar_position: 6
description: "How Redfish describes every resource, how to read the schema files and the Resource Guide, what versions and annotations mean, what message registries are, and how to use DMTF's official schemas to test a service, with a lab that found real mistakes in my own mock"
status: "drafted"
tier: "1b"
level: "I"
lab_venue: "GCP / GKE"
---

# 7.6 The Redfish schema: reading CSDL, JSON Schema and the Resource Guide

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted (`schema_lab.py`: 11 checks pass; **untested** on live BMC) |

## Why this matters for AI infrastructure

Every Redfish answer follows a published contract. If you can read the contract you never need a vendor manual to ask "what does this property mean, can I write it, is it new or old?" You can also test any tool or BMC against the contract, which catches mistakes before they reach production. This chapter shows how.

## Prerequisites and outcomes

You need chapters 7.2 and 7.3. After this chapter you can:

- explain the three schema formats and which one to use
- read an `@odata.type` and find its schema file
- explain Redfish versioning and why clients must tolerate new properties
- read a property table in the Resource Guide
- explain message registries and message IDs
- validate any Redfish payload against the official schema
- read DMTF's example trees as a free reference

## 1. One model, three file formats

Redfish describes its data model in the **schema**. The spec says the same model is published in three formats:

| Format | What it is | Who uses it |
|---|---|---|
| **CSDL** (OData Common Schema Definition Language) | XML | OData tools, the `$metadata` document |
| **JSON Schema** | JSON | validators and programmers (the easiest to use in Python or Go) |
| **OpenAPI YAML** | YAML | API tools and code generators (supported from Redfish protocol 1.6.0) |

They say the same thing in different languages. The spec calls itself "schema-language agnostic" and says the protocol and the data model are versioned separately.

There is also a human-readable guide: the **Redfish Resource and Schema Guide (DSP2046)**. It lists every standard resource with its properties, actions and an example. If you only read one document about the data model, read that one. The **Data Model Specification (DSP0268)** is the formal text behind it.

All of these are published together by DMTF, and the GitHub repository `DMTF/Redfish-Publications` holds the folders `csdl`, `json-schema`, `openapi`, `registries`, `profiles`, `dictionaries` and `mockups`. I used it for the lab.

## 2. From `@odata.type` to the schema file

Every answer has an `@odata.type` such as `#ComputerSystem.v1_17_0.ComputerSystem`. Read it in three parts:

| Part | Meaning |
|---|---|
| `ComputerSystem` | the resource type (the namespace) |
| `v1_17_0` | the version: major 1, minor 17, errata 0 |
| `ComputerSystem` | the type name inside that version |

The files are named by simple rules from the spec:

| Format | Versioned file | Unversioned file |
|---|---|---|
| JSON Schema | `ComputerSystem.v1_17_0.json` | `ComputerSystem.json` |
| CSDL | one file per **major** version: `ComputerSystem_v1.xml`, holding every minor version as a separate namespace such as `ComputerSystem.v1_17_0` | the namespace `ComputerSystem` inside that file |

**Why versioned and unversioned?** The spec explains: references from other resources use the **unversioned** definition so nothing depends on a version. The unversioned one has no property details, only the list of versions, the allowed URIs (such as `/redfish/v1/Systems/{ComputerSystemId}`) and the capabilities (can you create, update, delete). The **versioned** one holds the actual properties and actions of that version.

You can see this in the tool I wrote:

```text
$ python3 schema_tools.py explain Chassis.v1_23_0
Chassis v1_23_0: The Chassis schema represents the physical components of a system. ...
URIs: /redfish/v1/Chassis/{ChassisId}
capabilities: insertable=False updatable=True deletable=True
```

`insertable=False` means you cannot `POST` to create a chassis. `deletable=True` is a property of the schema. A service "may implement a subset" of what the schema allows.

## 3. Versioning: what a client must do

The version has three numbers:

- **Major**: a break in compatibility. Rare.
- **Minor**: new things were added, nothing was removed. For example, a new property means a new minor version.
- **Errata**: a fix to the earlier version, such as a corrected description.

Rules that matter to you:

1. **Newer minor versions only add.** So a client built for 1.4 can still read a 1.17 answer.
2. **A payload must follow the version it claims.** A `v1_0_0` payload cannot carry a property added in v1_5_0. My lab proves this with the official schema.
3. **Ignore what you do not know.** The spec says clients "should not fail reading the resource due to unrecognized annotations", and enumeration values can be added later, so do not crash on an unknown value.
4. **Step backwards to find a definition.** For a structured property the spec says to step the version back (1.4.0, 1.3.0, 1.2.0 ...) until you find where it is defined.
5. **Deprecated is not removed.** A deprecated property is marked with the version it was deprecated in and the preferred replacement. The spec says services may still implement it and new code should move on. Removal can only happen in the next major version.

A real example you will meet: older BMCs report power and heat through `Chassis/<id>/Power` and `Chassis/<id>/Thermal`. Newer ones use `PowerSubsystem`, `ThermalSubsystem` and `Sensors`. The old URIs are listed as deprecated in the schema (`Redfish.DeprecatedUris`). Chapter 7.8 handles both.

## 4. Reading the Resource Guide

Each resource in DSP2046 has the same layout:

1. its name, current version and description
2. release history (which DMTF bundle added each version)
3. the **URIs** where it can appear
4. a **property table**
5. its **actions**
6. an example JSON payload

The property table columns:

| Column | How to read it |
|---|---|
| Property | the exact, case-sensitive name. `(v1.13+)` means added in that version. `(deprecated v1.13)` means obsolete since then |
| Type | `string`, `number`, `boolean`, `object`, `array`. `(enum)` marks an enumeration, `(URI)` a link. Units are usually in the name (`SpeedRPM`) |
| Attributes | `read-only` or `read-write`, `required`, and `(null)` if the value can be null |
| Notes | the meaning |

The quick way to do the same from a script is the explain command. A shortened result for `Sensor`:

```text
property                           type           access     notes
Accuracy                           number,null    read-only  deprecated v1_8_0
AverageReading                     number,null    read-only  added v1_4_0
Id                                 Id             read-only  required
Manufacturer                       string,null    read-only  added v1_9_0
PeakReading                        number,null    read-only
...
```

and one property in full:

```text
$ python3 schema_tools.py explain ComputerSystem.v1_17_0 --prop PowerState
{ "anyOf": [ {"$ref": "#/definitions/PowerState"}, {"type": "null"} ],
  "description": "The current power state of the system.",
  "longDescription": "This property shall contain the power state of the system.",
  "readonly": true }
```

`readonly: true` explains why `PATCH PowerState` failed in chapter 7.5. The **long description** is the formal rule: when it says "shall", a conforming service must do it.

### The annotations on schema elements

The spec (9.13) defines these markers on properties and types. You will meet them when you read schemas:

| Annotation | Meaning |
|---|---|
| Description / Long description | text for people, and the normative rule |
| Permissions | read-only, read-write. A service may make a writable property read-only. A write-only property such as `Password` shall be `null` in responses |
| Required | the service must support it |
| Required on create | the client must send it when creating |
| Units of measure | the unit, written in UCUM style (`Cel`, `W`, `Mbit/s`) |
| Resource URI patterns | the allowed addresses, e.g. `/redfish/v1/Chassis/{ChassisId}`. The text in braces must equal the resource's `Id` |
| Resource capabilities | can it be inserted, updated, deleted |
| Additional properties | whether extra properties are allowed. Mostly not |
| Expanded resource | the service always expands this link in responses |
| Deprecated | since which version, and what to use instead |

## 5. Payload annotations you will see in answers

Beyond the schema, answers can carry annotations in the form `Property@Namespace.Term`. The spec limits them to the `odata`, `Redfish` and `Message` namespaces. The ones you already met:

| Annotation | Where | Meaning |
|---|---|---|
| `@odata.id`, `@odata.type`, `@odata.etag` | any resource | address, type, version label |
| `Members@odata.count`, `Members@odata.nextLink` | collections | total and next page |
| `ResetType@Redfish.AllowableValues` | actions | the values this action accepts now |
| `@Redfish.AllowablePattern`, `@Redfish.AllowableNumbers` | writable properties | a regular expression or numeric ranges that the value must follow. Example from the spec: `"AssetTag@Redfish.AllowablePattern": "^[\\w:-]{0,31}$"` |
| `@Message.ExtendedInfo` | answers and errors | extra messages (chapter 7.3) |
| `@Redfish.Settings` | settings-capable resources | where to write pending changes (BIOS, chapter 7.7 and 7.9) |
| `@Redfish.OperationApplyTime` | requests | when to apply (chapter 7.5) |

A client may ignore any annotation it does not understand, but must not fail because of one.

## 6. Message registries: how errors and events get their text

Error and event messages are not free text. Each has a **MessageId** that points into a **message registry**, a JSON file listing all messages of one group. The ID format is `<RegistryPrefix>.<major>.<minor>.<MessageName>`, for example `Base.1.17.PropertyNotWritable`.

A registry entry gives the message text with placeholders (`%1`, `%2`), the severity, the number and meaning of the arguments, and a suggested **resolution**. Real entry from the official Base registry:

```json
"PropertyNotWritable": {
  "Message": "The property '%1' is a read-only property and cannot be assigned a value.",
  "Severity": "Warning",
  "NumberOfArgs": 1,
  "Resolution": "Remove the property from the request body and resubmit the request if the operation failed."
}
```

The spec lists these kinds of registries:

| Registry | What it holds |
|---|---|
| **Message** | the text behind a `MessageId`, used in errors and events. The most common kind |
| **Attribute** | meaning, type and allowed values for BIOS-type settings, which differ per platform (so no fixed schema can exist). Chapter 7.7 and 7.9 |
| **Privilege** | which privileges are needed for which operation on which resource (chapter 7.4) |

The DMTF repository's `registries` folder holds the standard message registries (Base, ResourceEvent, Update, Power, Environmental and others). Using the latest `Base` registry I counted 125 messages in version 1.24.0. A BMC also publishes the registries it uses at `/redfish/v1/Registries`, so a client can fetch the exact text for its firmware. Note two practical points:

- The same MessageId can appear in logs, events and errors, so one lookup table serves all three.
- Vendors add OEM registries for their own messages. They must not change the standard ones.

## 7. OEM extensions

Not everything fits the standard. Vendors add their own properties and actions under `Oem`:

```json
"Oem": { "Contoso": { "Ping": "..." } }
```

Rules from the spec (9.4):

- Vendor data goes under `Oem`, grouped by vendor name. A client may ignore it.
- Vendors may define new resource types and actions, but these must follow the same schema and protocol rules.
- OEM action names look like `#Contoso.Ping`, bound to the `OemActions` part of the resource.
- OEM query parameters look like `OEM-<Vendor>-<Name>`.

Use OEM data only when no standard property exists. Scripts that depend on it only work on one vendor. NVIDIA's DGX and HGX systems expose their GPU and NVSwitch data partly through standard resources and partly through NVIDIA OEM extensions. I describe what the notes say about this in chapter 7.13. I have not checked it against NVIDIA documents.

## 8. The lab: use the schema to test a service

You need the DMTF repository and two Python packages:

```bash
git clone --depth 1 https://github.com/DMTF/Redfish-Publications.git
export REDFISH_PUBLICATIONS=$PWD/Redfish-Publications
python3 -m venv v && v/bin/pip install jsonschema referencing
cd code/part07
../../v/bin/python schema_lab.py
```

(The path to `python` depends on where you put the virtual environment.) The lab runs 11 checks:

```text
PASS  validator accepts all 271 resources of DMTF's public-rackmount1 example
PASS  an unknown property is rejected
PASS  a value outside the enumeration is rejected
PASS  the wrong JSON type is rejected
PASS  a missing required property (Id) is rejected
PASS  null is allowed where the schema says nullable (AssetTag)
PASS  annotations (Prop@Namespace.Term) and Oem extensions are allowed
PASS  a v1_0_0 payload cannot carry properties added later (versioning rule, 9.14)
PASS  the same data is valid under the version it really is (v1_29_0)
PASS  all 110 resources of our mock validate against the official schemas
PASS  every MessageId our mock returned (14 different ones) exists in the official Base registry
```

### What it found in my own mock

When I first ran the validator over the mock I wrote for chapters 7.2 to 7.5, **7 of its 30 resources were invalid** and two message IDs did not exist. All of these were my mistakes:

1. The service root had a property `TaskService`. The real property is **`Tasks`** (it links to the task service).
2. `AccountService` used an old version number but a property (`HTTPBasicAuth`) that was added later.
3. `ManagerAccount` was missing the required `AccountTypes`.
4. A fan sensor had `ReadingType: "Fan"`. The allowed value is **`Rotational`**.
5. Two error message IDs I had made up (`ActionParameterValueNotInList`, `QueryParameterUnsupported`) are not in the Base registry. I switched to registry messages (`PropertyValueNotInList`, `QueryNotSupported`).

After the fixes all 30 resources validated, and the mock has since grown to 110 resources (GPUs, NICs, drives, firmware) that all still validate. Those are the kind of errors a hand-written tool or a lazy BMC firmware makes, and a person reading JSON by eye would miss most of them.

### Validating a real service

The crawl command logs in, walks the whole service and validates every resource:

```bash
python3 schema_tools.py crawl https://<bmc-address> <user> <password>
```

I ran it on DMTF's example trees served by my mock's read-only mode (`redfish_mock.py --mockup <folder>`). Results:

| DMTF example | Resources | Valid by official schema |
|---|---|---|
| `public-rackmount1` | 270 | 270 |
| `public-liquid-cooled-server` | 241 | 241 |
| `public-cooling-unit` | 67 | 67 |
| `public-pdu` | 198 | 198 |
| `public-power-shelf` | 101 | 99 |

Even in DMTF's own power-shelf example, two resources fail: one `Status` condition uses a property name, `MessageSeverity`, that the schema does not list. That is useful to know. **The schema is the authority, and published examples can have errors too.**

Run the crawl against a real BMC only with permission, and expect real findings. Many BMCs have small deviations. Decide with your vendor which ones matter.

### Using the example trees

The `mockups` folder is a free library of realistic Redfish trees: rack servers, liquid-cooled servers, PDUs, power shelves, cooling units, storage, CXL, telemetry and more. You can serve any of them with the mock and practise scripts against it:

```bash
python3 redfish_mock.py --mockup $REDFISH_PUBLICATIONS/mockups/public-liquid-cooled-server --port 8443
python3 redfish_crawl.py http://127.0.0.1:8443 admin adminpass
```

In the mockup mode the data is read-only. The login accounts are the same fake ones as before. I use these trees in the next chapters.

## 9. Exercises

1. Run `schema_tools.py explain Chassis.v1_23_0`. Find three read-only properties and three read-write ones.
2. Use `--prop` to look at the definition of `Boot` in `ComputerSystem`. What do the `BootSourceOverrideTarget` allowed values look like?
3. Take the sample file `Systems/437XR1138R2/index.json` from the rackmount example, change `PowerState` to `"Maybe"`, and run `schema_tools.py check` on it. Read the message.
4. Look up `PropertyValueNotInList` in the Base registry. What are its arguments and what is the suggested resolution?
5. Serve `public-pdu` with the mock. Crawl it and list the resource types you find. Which would a data center team care about?
6. Find a property that is `deprecated` in the `Chassis` schema and the one that replaces it.
7. Write a Python function that, given a payload, returns the list of properties a client could set (`readonly` false) according to the schema.

## 10. Interview angles

- "How do you know what a Redfish property means?" The Resource Guide and the JSON Schema long description, found by `@odata.type`.
- "A new BMC firmware adds fields. Does your tool break?" It should not: ignore unknown properties and enumeration values.
- "How do you check a BMC follows the standard?" Validate payloads against the official JSON Schemas, and the interoperability profiles (DMTF publishes a profile format in the `profiles` folder).
- "What is a message registry and why does it exist?" A shared table of message IDs, text, severity and resolution, so errors and events are machine-readable and translatable.
- "When do you use Oem data?" Only when no standard property exists, and wrapped so one vendor's change does not break the rest.

## 11. Checkpoint questions (20)

1. Name the three formats of the Redfish schema.
2. Which format would you load in Python to validate?
3. What do the three parts of `#Chassis.v1_23_0.Chassis` mean?
4. What are the JSON Schema file names for versioned and unversioned definitions?
5. What does the unversioned definition contain?
6. What does a minor version change mean? An errata change?
7. Can a `v1_0_0` payload contain a `v1_5_0` property?
8. What should a client do with an unknown property?
9. What does `read-only` mean in the Resource Guide, and what does `required` mean?
10. What does `(v1.13+)` after a property name tell you?
11. What is a deprecated property and when can it be removed?
12. What does `@Redfish.AllowablePattern` do?
13. What is a MessageId and what is its format?
14. What is in a registry entry?
15. Name three kinds of registries.
16. Where do vendors put extra data?
17. What is the Resource Guide for?
18. What does `schema_tools.py crawl` do?
19. Name two real mistakes the validator found in the mock.
20. Why is the DMTF `mockups` folder useful?

## 12. Sources and review notes

- **Redfish Specification DSP0266 v1.21.0:** goals and design (5.1 to 5.4), data model, resources, OEM, types, naming and annotations (9.1 to 9.13), registries (9.12), versioning (9.14), schema definition languages and file naming (11.1 to 11.4), OData metadata and service document (8.4). I read these clauses.
- **Redfish Resource and Schema Guide DSP2046 (2024.4):** how to read the guide (section 2), common properties and objects (sections 3 and 4), and the Reference Guide property tables.
- **The `redfish-schema` book** in the study corpus is titled "Redfish Data Model Specification". By its chapter list it has the same structure as the Resource Guide (overview, common properties, common objects, collections, then one section per resource type). I looked at its chapter list and used the Resource Guide and the official JSON files for facts. I did not read it page by page.
- **Only mentioned, not taught:** OpenAPI and the Interoperability Profile format. I read their clauses only at heading level, so a later pass should cover profiles properly.
- **Official files used in the lab:** `json-schema`, `registries` and `mockups` from DMTF/Redfish-Publications at commit `fa6d23d9`.
- **Run here:** `schema_lab.py` (11 checks), `schema_tools.py` (explain, check, crawl), and crawls of five DMTF example trees through the read-only mock.
- **Not verified:** how any real BMC performs under validation. The statement about NVIDIA OEM extensions comes from the user's notes and is unchecked.
