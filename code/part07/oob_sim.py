#!/usr/bin/env python3
"""Teach in-band versus out-of-band management with a tiny state machine.

A server has three parts that can fail separately:
  standby power -> the BMC (alive whenever the machine is plugged in)
  host power    -> the CPUs, GPUs and the operating system (OS)
  OS state      -> running, hung (kernel panic, frozen) or off

For each failure we ask: can I still reach the machine by SSH (in-band)?
Can I still reach the BMC on the management network (out-of-band)?
This is a model, not a real BMC. It only encodes the rules in chapter 7.1.
"""
import itertools

# (name, ac_power, host_power, os_state, mgmt_switch_up, prod_network_up)
SCENARIOS = [
    ("healthy server",                True,  True,  "running", True,  True),
    ("OS kernel panic",               True,  True,  "hung",    True,  True),
    ("host powered off",              True,  False, "off",     True,  True),
    ("production network down",       True,  True,  "running", True,  False),
    ("management switch down",        True,  True,  "running", False, True),
    ("rack lost AC power",            False, False, "off",     True,  True),
]


def reach(ac, host, os_state, mgmt_up, prod_up):
    ssh = host and os_state == "running" and prod_up          # needs OS + normal network
    bmc = ac and mgmt_up                                       # needs standby power + mgmt network
    can_reset = bmc                                            # BMC can press the power button
    can_read_sensors = bmc                                     # BMC has its own sensors
    return ssh, bmc, can_reset, can_read_sensors


def yn(x):
    return "yes" if x else "NO"


def main():
    print(f"{'scenario':26} {'SSH':>4} {'BMC':>4} {'reset':>6} {'sensors':>8}  advice")
    for name, ac, host, os_state, mgmt, prod in SCENARIOS:
        ssh, bmc, rst, sens = reach(ac, host, os_state, mgmt, prod)
        if ssh:
            advice = "normal management"
        elif bmc:
            advice = "use the BMC (Redfish/IPMI) to inspect or reset"
        else:
            advice = "nothing remote works: smart hands or fix power/network"
        print(f"{name:26} {yn(ssh):>4} {yn(bmc):>4} {yn(rst):>6} {yn(sens):>8}  {advice}")


if __name__ == "__main__":
    main()
