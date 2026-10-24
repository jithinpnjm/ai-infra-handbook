# Part 8 labs (BCM): models of the rules stated in the BCM 11 manuals

Stdlib Python only. Each lab prints PASS/FAIL lines and a final count. They test **our reading of the manuals**, not BCM itself.

| Chapter | Model | Lab | Checks |
|---|---|---|---|
| 8.1 | bcm_model.py | bcm_model_lab.py | 30 |
| 8.2 | bcm_plan.py, license_check.py, burn_config.py | install_lab.py | 32 |
| 8.3 | bcm_netconf.py | netconf_lab.py | 54 |
| 8.4 | bcm_provision.py | provision_lab.py | 72 |
| 8.5 | cmsh_sim.py | cmsh_lab.py | 55 |
| 8.6 | bcm_security.py | security_lab.py | 51 |
| 8.7 | bcm_hardware.py | hardware_lab.py | 45 |
| 8.8 | bcm_slurm.py | slurm_lab.py | 50 |
| 8.9 | bcm_k8s.py | k8s_lab.py | 48 |
| 8.10 | bcm_containers.py | containers_lab.py | 35 |
| 8.11 | bcm_monitor.py | monitoring_lab.py | 36 |
| 8.12 | bcm_ha.py | ha_lab.py | 42 |
| 8.13 | bcm_ops.py | ops_lab.py | 40 |
| 8.14 | bcm_airgap.py | airgap_lab.py | 28 |
| 8.15 | superpod_calc.py | superpod_lab.py | 29 |
| 8.16 | bcm_mission_control.py | mission_control_lab.py | 31 |

Run all: `for f in *_lab.py; do python3 $f | tail -1; done`
