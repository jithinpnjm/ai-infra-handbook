# Part 7 code: Redfish and BMC labs

Everything here runs on a laptop with Python 3.12 and no hardware. Nothing was tested on a real BMC.

## The teaching Redfish service

`redfish_mock.py` (with `mock_update.py`, `mock_logs.py`, `mock_bios.py`, `mock_certs.py`) is a small Redfish service built only on the Python
standard library. It follows DSP0266 closely enough to practise on: sessions, roles, lockout, ETags, actions, tasks, events, server-sent events,
firmware inventory and update, logs, BIOS settings and registry, certificates, Secure Boot, fault injection. It is NOT a real BMC.

```bash
python3 redfish_mock.py --port 8443                      # plain HTTP, lab only
python3 tls_setup.py /tmp/pki && python3 redfish_mock.py --port 8443 --tls /tmp/pki/server.pem /tmp/pki/server.key
python3 redfish_mock.py --mockup /path/to/Redfish-Publications/mockups/public-rackmount1 --port 8443   # serve a DMTF example tree
```

Accounts: `admin/adminpass` (Administrator), `operator/operpass`, `viewer/viewpass` (ReadOnly), `factory/changeme1` (must change password).

## Self-checking labs (each prints PASS/FAIL and exits non-zero on failure)

| Lab | Chapter | Checks |
|---|---|---|
| `oob_sim.py`, `cred_audit.py` (demos) | 7.1 | |
| `protocol_lab.py` | 7.3 | 36 |
| `auth_lab.py` | 7.4 | 44 |
| `actions_lab.py` | 7.5 | 34 |
| `schema_lab.py` (needs DMTF clone + jsonschema) | 7.6 | 11 |
| `sensors_lab.py` | 7.8 | 13 |
| `hardware_lab.py` | 7.9 | 15 |
| `firmware_lab.py` | 7.10 | 46 |
| `logs_lab.py` | 7.11 | 23 |
| `fleet_lab.py` | 7.12 | 14 |
| `lifecycle_lab.py` | 7.14 | 24 |
| `hardening_lab.py` (needs openssl) | 7.15 | 29 |

Optional environment: `export REDFISH_PUBLICATIONS=<clone of github.com/DMTF/Redfish-Publications>` and `pip install jsonschema referencing`
to turn on the schema-validation checks and the DMTF example trees.

## Tools (all discover resources by following links, none hard-code addresses)

`redfish_crawl.py` (client and crawler), `rf_inventory.py`, `rf_model.py`, `rf_sensors.py`, `rf_hardware.py`, `rf_firmware.py`, `rf_logs.py`,
`rf_bios.py`, `rf_harden.py`, `rf_attest.py`, `rf_record.py`, `schema_tools.py`, `fleet_run.py`, `node_lifecycle.py`, `run_dmtf_validators.sh`.
Anything that changes a machine is a dry run unless you pass `--yes`.

`ansible/` and `go_gofish/` and `python_redfish_library_demo.py` are the chapter 7.12 examples (they expect an HTTPS mock and a CA file).
`profiles/` has the acceptance, hardening, BIOS and policy files.

Environment variables for the Python tools: `REDFISH_CA` (CA file to trust), `REDFISH_INSECURE=1` (skip certificate checks, prints a warning).
