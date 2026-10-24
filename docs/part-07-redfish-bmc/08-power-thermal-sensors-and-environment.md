---
id: "c07-08"
title: "7.8 Power, thermal, sensors and environment"
sidebar_label: "7.8 Power, thermal, sensors and environment"
sidebar_position: 8
description: "How to read temperatures, fans, power supplies, power draw and cooling through Redfish: the modern Sensors design and the old Thermal and Power design, thresholds, power capping controls, telemetry reports, and a tool that reads both and flags real problems"
status: "drafted"
tier: "1b"
level: "I"
lab_venue: "GCP / GKE"
---

# 7.8 Power, thermal, sensors and environment

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop |
| Part | Part 7: Redfish and BMC |
| Status | Drafted (`sensors_lab.py`: 13 checks pass against mock and DMTF trees; **untested** on live BMC) |

## Why this matters for AI infrastructure

A training job can slow down by a third because one fan failed or one GPU got too hot, and the operating system may not say a word. The BMC watches the hardware from outside, so its sensors are the first place to look. Power is the other limit: every rack has a fixed budget (chapter 6.30) and the BMC can report, and sometimes limit, how much each server draws.

## Prerequisites and outcomes

You need 7.2 and 7.7, and chapter 6.30 helps. After this chapter you can:

- find temperature, fan, voltage and power readings on any Redfish service
- tell the modern design (`Sensors`, subsystems) from the old design (`Thermal`, `Power`)
- read thresholds and decide what to alert on
- explain `Status`, `Health` and thresholds as separate things
- read power supply and cooling data, and understand power-cap controls
- export readings in Prometheus format

## 1. Two designs for the same information

Redfish changed how it shows heat and power. Both exist in real equipment, so you must read both.

| | Old design (deprecated) | Modern design |
|---|---|---|
| Where | `Chassis/<id>/Thermal` and `Chassis/<id>/Power` | `Chassis/<id>/Sensors`, `ThermalSubsystem`, `PowerSubsystem`, `EnvironmentMetrics` |
| Shape | one big resource with **arrays** (`Temperatures[]`, `Fans[]`, `Voltages[]`, `PowerControl[]`, `PowerSupplies[]`) | **one resource per item** (a Sensor, a Fan, a PowerSupply) |
| Linking | items are array entries, found by position | each item has its own address and links |
| Status | the resource marks itself deprecated | current |

DMTF's rack-server example even carries a hint inside the chassis: `"Thermal@Redfish.Deprecated": "Please migrate to use /redfish/v1/Chassis/1U/ThermalSubsystem"`. The schema marks the old way as deprecated, but the spec says services may still implement it, so older BMC firmware keeps it.

The lab shows the difference in the same example tree: through the modern `Sensors` collection the tool found **41** readings. When I removed that link to force the old route it found **9**, from `Thermal` and `Power`. The modern way exposes more, with more detail.

## 2. Sensors: one resource per measurement

A `Sensor` is a single reading with its meaning attached. The most useful properties (from the schema):

| Property | Meaning |
|---|---|
| `Reading` | the current value |
| `ReadingType` | what is measured. Values include `Temperature`, `Humidity`, `Power`, `EnergykWh`, `Voltage`, `Current`, `Frequency`, `Pressure`, `LiquidLevel`, `Rotational`, `AirFlow`, `LiquidFlow`, `Percent`, `Heat` and more |
| `ReadingUnits` | the unit in UCUM style: `Cel`, `W`, `V`, `A`, `RPM`, `%`, `Hz` |
| `PhysicalContext` | where it applies: for example `CPU`, `GPU`, `Intake`, `Exhaust`, `PowerSupply`, `Fan` |
| `PhysicalSubContext` | a finer position inside that context |
| `ReadingRangeMin`, `ReadingRangeMax` | the range the sensor can measure |
| `Thresholds` | the limits (below) |
| `PeakReading` and similar | highest value seen |
| `SpeedRPM` | fan speed, for fan sensors |
| `Status` | `State` and `Health` |

Because the unit and context are in the data, one program can handle every sensor without a per-vendor list. You find sensors under `Chassis/<id>/Sensors`. Some BMCs also place sensors under other resources, so in a fleet tool treat the chassis list as the main route and the metric links of components (below) as extra.

### Thresholds

A sensor's `Thresholds` object can hold these limits, each with a `Reading` and an `Activation` direction (`Increasing`, `Decreasing`, `Either` or `Disabled`):

`UpperCaution`, `UpperCritical`, `UpperFatal`, `LowerCaution`, `LowerCritical`, `LowerFatal`, and user-set variants (`UpperCautionUser` and so on). Each threshold can also carry `DwellTime` (how long the value must break the limit before it counts) and hysteresis (how far back it must come to clear).

Caution, critical and fatal are three steps up: **caution** means "above normal", **critical** means "above normal but not yet fatal" and **fatal** means the level the equipment treats as dangerous. The BMC then sets `Status.Health` to `Warning` or `Critical`, and may take action itself such as raising fan speed or shutting down.

### Status is not the same as a reading

Three separate ideas:

| Idea | Where | Meaning |
|---|---|---|
| **Reading** | `Reading` | the number |
| **Threshold** | `Thresholds` | the limits for that number |
| **Health** | `Status.Health` | the BMC's own judgment: `OK`, `Warning`, `Critical` |

`Status.State` adds whether the sensor is `Enabled`, `Disabled`, `Absent` (nothing there) and so on. Do not mix them up: a sensor can be `Disabled` and have no reading, which is normal.

**Why your tool should check the value itself.** The BMC's health flag depends on firmware logic that you do not control. In my lab I set a GPU temperature above its critical threshold while leaving `Health: OK`, and the tool still flagged it. A monitoring tool that trusts only the health flag misses sensors whose firmware forgot to update it. Use both.

## 3. Thermal: fans, heat and cooling

Under the modern `ThermalSubsystem` (from the schema):

| Link | Contents |
|---|---|
| `Fans` | one `Fan` per fan: `SpeedPercent`, `Location`, `PhysicalContext`, `Replaceable`, `HotPluggable`. The actual RPM is on a linked sensor |
| `FanRedundancy` | groups of fans and how many must work (for example N plus M) |
| `ThermalMetrics` | a summary: `TemperatureSummaryCelsius` (intake, exhaust and so on) and a list of readings |
| `Heaters` | heating elements, if any |
| `LeakDetection`, `Pumps`, `Filters`, `CoolantConnectorRedundancy` | for liquid-cooled equipment |

**Fan redundancy** is worth reading. DMTF's example says each fan group has `MinNeededInGroup: 1` out of two. It tells you whether one failed fan is an emergency or just a repair ticket.

For liquid cooling the standard has more resources: `CoolingUnit` (a CDU, coolant distribution unit), `CoolantConnector`, `Pump`, `Reservoir`, `Filter`, `LeakDetection` and `LeakDetector`. The BCM manual says BCM uses Redfish for leak detection on NVL8 hardware. Chapter 6.30 explains why liquid cooling matters. I ran my reader on DMTF's cooling-unit example, which has a separate chassis for the CDU: 18 readings, nothing flagged.

## 4. Power: supplies, draw and limits

Under `PowerSubsystem`:

| Link or property | Meaning |
|---|---|
| `CapacityWatts` | total power the chassis can draw |
| `Allocation` | requested and allocated watts |
| `PowerSupplies` | one `PowerSupply` per unit |
| `PowerSupplyRedundancy` | for example `Failover`, which supplies are active, how many are needed |
| `Batteries` | battery units |

A `PowerSupply` has `PowerCapacityWatts`, `LineInputStatus` (is the input power present and normal), `PowerSupplyType` (AC or DC), efficiency ratings by load, input ranges, firmware version and a link to its `Metrics` (`PowerSupplyMetrics`: input and output watts, voltage, current, temperature). It also has `Status`, and in DMTF's example `Status.Conditions` holds a real-looking message: *"Power supply 'PSU 1' has a predicted failure condition."* with `Health: Warning`. This is the kind of early warning to alert on, before a supply actually fails.

`EnvironmentMetrics` is a handy summary on a chassis (and on many components, such as each GPU): `PowerWatts`, `EnergykWh`, `TemperatureCelsius`, `FanSpeedsPercent`, `HumidityPercent`, and `PowerLimitWatts`. Each entry has a `DataSourceUri` that points at the sensor it came from, so you can follow it for detail.

### Power capping with controls

A `Control` resource is a setting you can change. For power it looks like this, from DMTF's example:

```json
{
  "Id": "PowerLimit",
  "Name": "System Power Limit",
  "PhysicalContext": "Chassis",
  "ControlType": "Power",
  "ControlMode": "Automatic",
  "SetPoint": 500,
  "SetPointUnits": "W",
  "AllowableMax": 1000,
  "AllowableMin": 150,
  "Sensor": { "Reading": 374, "DataSourceUri": "/redfish/v1/Chassis/1U/Sensors/TotalPower" }
}
```

The server is drawing 374 W, the cap is 500 W, and it may be set between 150 and 1000 W. To change it you `PATCH` the control's `SetPoint` (with the usual ETag care from chapter 7.3). The NVIDIA notes say power capping on DGX H100 and H200 is done through Redfish. I could not check how.

:::warning Capping changes performance
A power cap makes the hardware slow itself down to stay under the limit. On GPU servers that directly lowers training speed. Change a cap only with a reason, record who changed it and why, and compare the job speed before and after. A cap that is lower than the normal draw of a busy server looks, from the user's side, like a slow cluster.
:::

### The old design's power data

For completeness: `Power` has `PowerControl[]` (with `PowerConsumedWatts`, `PowerCapacityWatts` and `PowerMetrics` with min, max and average over an interval, and a `PowerLimit`), `Voltages[]` and `PowerSupplies[]`. My tool reads these when the modern route is missing.

## 5. The tool: read both, flag by value

`code/part07/rf_sensors.py` reads every chassis. For each one it tries the `Sensors` collection first and falls back to the old `Thermal` and `Power`. It normalises everything into rows and applies checks:

- `Health` is not `OK`
- the reading is at or above `UpperCritical` or `UpperFatal`, or above `UpperCaution`
- the sensor is `Enabled` but has no reading (`null`)

`Disabled` and `Absent` sensors are skipped. With `--prom` it prints Prometheus text format. Example run on my mock after I set one GPU temperature to 92 C (its critical limit is 88):

```text
chassis Chassis_0: 4 readings via Sensors
   Sensors  Temp GPU0   Temperature   92.0 Cel   AT/ABOVE CRITICAL limit 88.0
```

and on DMTF's rack-server example:

```text
chassis 1U: 41 readings via Sensors
   Sensors  CPU #1 Temperature   ?   44 Cel   health=Warning; above caution limit 42
41 readings, 1 flagged
```

In the power-shelf example the tool flagged `Power Shelf Load Percent` at 93 % against a caution limit of 90. Across the DMTF examples the counts were: PDU 115 readings and nothing flagged, cooling unit 18 and nothing flagged, power shelf 35 and 1 flagged, rack server 41 and 1 flagged.

The lab (`sensors_lab.py`) has 13 checks. They test: normal values are not flagged, critical and caution by value, null reading, `Critical` health, `Disabled` sensors skipped, the Prometheus text (parsed with the official `prometheus_client` parser), and the fallback to the old route on DMTF's data.

### Prometheus export

`--prom` produces lines like:

```text
redfish_sensor_reading{chassis="1U",sensor="Ambient Temperature",kind="?",units="Cel"} 22.5
redfish_sensor_ok{chassis="1U",sensor="Ambient Temperature",kind="?",units="Cel"} 1
```

The `kind="?"` appears because that sensor in DMTF's example has no `ReadingType`, which is optional. Chapter 17's monitoring part builds on this idea. For a real fleet you would run an exporter service, not a script, and keep the number of unique label values small (fan and sensor names differ between machines, so test the cardinality).

## 6. Telemetry service: reports instead of polling

Reading every sensor every 10 seconds from 1,000 BMCs is heavy. The **TelemetryService** lets the BMC collect metrics itself and hand you a bundle:

| Resource | Meaning |
|---|---|
| `MetricDefinitions` | what can be measured |
| `MetricReportDefinitions` | a recipe: which properties to collect, how often (`Schedule`), what to do with the report (for example send it as an event) |
| `MetricReports` | the produced reports. A `MetricReport` has `MetricValues`, a `ReportSequence` and a `Timestamp` |
| `Triggers` | rules such as "when this reaches a threshold, take this action" |

The service says the shortest allowed collection time in `MinCollectionInterval`. Metric reports can be sent through the event service from chapter 7.5 (the spec has a separate metric-report event format). The NVIDIA notes show one DGX report address, `TelemetryService/MetricReports/NvidiaNMMetrics_0`. I could not confirm that name and it is likely specific to one NVIDIA platform and firmware version.

## 7. How this fits with GPU tools

The BMC and the GPU driver see different things:

| Source | Sees | Does not see |
|---|---|---|
| **BMC / Redfish** | inlet and exhaust air, fans, power supplies, board temperatures, total power, sometimes GPU temperature and power | GPU clocks, throttle reasons, ECC details (unless the vendor adds them) |
| **GPU driver (`nvidia-smi`, DCGM)** | GPU clocks, throttle reasons, utilization, memory errors, NVLink counters | fans, power supply health, anything when the OS is down |

Use both. If a job is slow, the driver tells you the GPU is throttling for thermal or power reasons. Redfish tells you why: a failed fan, a hot inlet, a power supply that dropped. The NVIDIA notes work through one such investigation ("ghost throttling") in a scenario that I carry into chapter 7.14.

## 8. Finding data on an unknown machine

Because layouts differ, use a fallback order. For "the GPU temperature" on a server you have not seen:

1. From each `ComputerSystem` look at `Processors` for `ProcessorType` equal to `GPU`. Follow the GPU's `EnvironmentMetrics` link if present (the notes show `GPU_SXM_<id>/EnvironmentMetrics` on the HGX baseboard).
2. Otherwise search the chassis `Sensors` for `ReadingType: Temperature` and a `PhysicalContext` of `GPU`.
3. Otherwise try the old `Thermal` resource and look for temperatures whose `PhysicalContext` or `RelatedItem` points to the GPU.
4. If none exist, say so. Do not invent a value. "No data" is a finding to report.

## 9. Exercises

1. Run `sensors_lab.py`. Which check would catch a BMC whose health flag is stuck on `OK`?
2. Serve DMTF's `public-pdu` and run `rf_sensors.py --all`. List the kinds of readings (current, voltage, energy). Why does a PDU need a chassis?
3. In the rack-server example, find the control for power limit and the sensor it watches. What would you `PATCH` to lower the limit to 450 W, and what must you check first?
4. Write an alert rule (in words) for "a power supply is predicting failure". Which property do you read?
5. Extend `rf_sensors.py` to also read `ThermalSubsystem/Fans` and report `SpeedPercent`. Test it on the rack-server example.
6. Using `redfish_mock.py` in-process, change a sensor so `Thresholds.UpperCritical.Activation` is `Disabled`. What should your tool do?

## 10. Interview angles

- "Training slowed down on one node. How do you check whether it is physical?" Look at BMC sensors (inlet temperature, fans, power supplies) and compare with the other nodes; then the GPU driver for throttle reasons.
- "Why check the reading and not just Health?" The health flag is firmware logic; thresholds and values are data you can verify.
- "Thermal versus ThermalSubsystem?" The old array-based design against the modern one-resource-per-item design. A tool must handle both.
- "What is a power cap and what is the risk?" A limit on server power. It protects the rack budget but slows the hardware; change it deliberately and record it.
- "How would you monitor 1,000 BMCs without overloading them?" Telemetry reports or events where supported, a moderate poll interval, and controlled concurrency.

## 11. Checkpoint questions (20)

1. Name the two Redfish designs for thermal and power data.
2. How many readings did the tool find in the rack-server example through `Sensors`, and through the old route?
3. What does `ReadingType` tell you? `ReadingUnits`? `PhysicalContext`?
4. Name the three upper thresholds in order.
5. What is `DwellTime` for?
6. What is the difference between a reading, a threshold and `Health`?
7. What does `State: Absent` mean for a sensor?
8. Why should a tool check the reading against the threshold itself?
9. What does `FanRedundancy` tell you?
10. What does `LineInputStatus` mean?
11. What is a power supply `Condition` such as a predictive failure?
12. What is `EnvironmentMetrics`?
13. What is a `Control` and what is `SetPoint`?
14. Why is a power cap not a free setting?
15. What does `TelemetryService` offer that polling does not?
16. What is a `MetricReportDefinition`?
17. What can the BMC see that the GPU driver cannot, and the reverse?
18. What is the fallback order for finding a GPU temperature?
19. What should a tool do when no data exists?
20. Why keep the number of Prometheus label values small?

## 12. Sources and review notes

- **Redfish Resource and Schema Guide DSP2046 (2024.4)** and the official JSON Schemas (`Sensor` v1.10 and later, `PowerSubsystem`, `PowerSupply`, `ThermalSubsystem`, `ThermalMetrics`, `EnvironmentMetrics`, `Control`, `Fan`, `Thermal`, `Power`, `TelemetryService`, `MetricReport`, `MetricReportDefinition`, `Triggers`): property meanings and enumerations.
- **DMTF example trees** (`public-rackmount1`, `public-pdu`, `public-power-shelf`, `public-cooling-unit`, `public-liquid-cooled-server`) at commit `fa6d23d9`: all numbers in the lab.
- **BCM 11 Administrator Manual**, appendix N: sensor and health monitoring and leak detection for NVL8 hardware.
- **NVIDIA-DevOps notes** (volume 10 chapter 1, section 3.3 and scenario 1): the GPU endpoints, the telemetry report name and the throttling investigation. Unchecked.
- **Chapter 6.30** for rack power and cooling arithmetic. The user's notes volume 20 chapter 9 (power supply issues and brownout scenarios) is routed to chapters 6.14, 10.21, 10.22, 12.18, 12.24 and 17.7 and is not used here.
- **Run here:** `rf_sensors.py` on six services and `sensors_lab.py` (13 checks).
- **Not verified:** real BMC sensor names, which sensors exist on DGX, HGX or GB200, the exact power-capping method on NVIDIA systems, and the NVIDIA telemetry report. DMTF's example data is illustrative.
