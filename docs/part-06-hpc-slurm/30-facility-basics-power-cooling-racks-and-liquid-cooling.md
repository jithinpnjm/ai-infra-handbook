---
id: "c06-30"
title: "6.30 Facility basics: power, cooling, racks and liquid cooling"
sidebar_label: "6.30 Facility basics: power, cooling, racks and liquid cooling"
sidebar_position: 30
description: "The physical side of a GPU cluster explained from scratch: how much power servers and switches use, how power reaches a rack (circuits, breakers, redundancy), how heat is removed (air, containment, liquid), racks, cables, UPS and safe shutdown, PUE and energy cost, with calculators that reproduce NVIDIA's published rack tables"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 6.30 Facility basics: power, cooling, racks and liquid cooling

| | |
|---|---|
| Level | Beginner to Intermediate |
| Priority tier | 1 |
| Lab venue | Laptop (calculators) |
| Part | Part 6: HPC and Slurm |
| Status | Drafted. The rack power table, airflow figures and cost example from the books were **recomputed** with `code/part06/facility_calc.py`: all nine rows of NVIDIA's DGX B200 power table matched. `code/part06/ups_shutdown_sim.py` simulates the book's staged UPS shutdown; its battery sizes are invented for illustration. No real facility was measured. Cooling and power figures are the books' planning numbers: always use your vendor's current site-requirements document |

## Why this matters for AI infrastructure

A GPU server is a machine that turns electricity into computation, and almost all of that electricity ends up as heat. The more GPUs you pack in a rack, the more power you must bring in and the more heat you must carry out. Power, cooling and space are the three limits of every data center, and they limit how many GPUs you can run before software even matters. Infrastructure engineers do not have to design buildings, but they must speak to the facility team, understand why a rack holds only two servers, and know what happens when the power fails.

## Prerequisites and outcomes

Nothing special. After this chapter you can:

- Convert between watts, kilowatts, megawatts and kilowatt-hours, and estimate a cluster's energy bill.
- Explain why a rack can hold only a few GPU servers, using power and cooling limits.
- Read a power provisioning table: voltage, amps, breaker derating, usable kW, stranded power.
- Explain N and N+1 redundancy for servers that have internal power supplies, and why some designs make things worse.
- Describe air cooling and the four kinds of liquid cooling, and say what PUE tells you.
- Plan racks, cabling and distances for an InfiniBand cluster.
- Describe what a UPS does and how to shut a cluster down in stages when power fails.

## 1. Start with the simple idea

Every watt a server draws becomes a watt of heat. A server that draws 10 kilowatts (kW) heats the room like ten space heaters of 1 kW each running all day. Cooling must remove exactly as much heat as the machines make.

The units, in plain words:

| Unit | Meaning | Example |
|---|---|---|
| Watt (W) | Rate of using energy | A GPU can draw 700 W |
| Kilowatt (kW) | 1,000 W | One DGX server: about 10 to 14 kW |
| Megawatt (MW) | 1,000 kW | A large AI cluster: several MW; one GB300 SuperPOD scalable unit alone is rated about 1.2 MW |
| Kilowatt-hour (kWh) | Energy: 1 kW used for 1 hour | What your electricity bill counts |

Data centers have **finite resources**: the NVIDIA data-center guide says the three main constraints are **power, cooling and space**, they are linked, and "excess demand on one resource could negatively impact other resources". For example, pushing more power into a rack needs more cooling, and spreading racks apart to cool them makes InfiniBand cables longer than they are allowed to be.

The ADC book (*AI Data Center Network Design and Technologies*, chapter 5) puts data centers in context: they use roughly 2 percent of the world's electricity, and AI makes it grow. Inside a data center, it estimates IT equipment takes 40 to 45 percent of the power, the **cooling system 35 to 40 percent** (the second biggest consumer), and the rest goes to power distribution, UPS and lighting.

## 2. How much power does the equipment use?

| Item | Power | Source |
|---|---|---|
| One H100 GPU (SXM) | up to 700 W | AI Factory vol. 21 |
| DGX H100 server (8 GPUs) | about 10.2 kW maximum | vol. 21 (NVIDIA user guide) |
| DGX B200 server (8 GPUs) | 14.3 kW maximum | NVIDIA DGX B200 data-center guide |
| Network switch, 64 x 400 G | about 3 kW power supply | ADC book (example switch) |
| Optical module, QSFP28 / QSFP56-DD / OSFP | 3.2 W / 12 W / 15 W | ADC book |
| Traditional rack | about 10 to 25 kW budget; most around 16 to 18 kW | ADC book |

Optics look small but add up: a 64-port switch full of 15 W modules has close to 1 kW of optics alone.

A note that avoids confusion: the ADC book says a DGX H100 has six power supplies of 3.3 kW with 4+2 redundancy, so "it consumes 4 x 3.3 kW = 13.2 kW". That 13.2 kW is the **capacity of the four working supplies**, not what the server draws. NVIDIA's rated maximum for the DGX H100 is about 10.2 kW. Use the vendor's rated maximum for planning, and measured power (DCGM, PDU meters, 6.26) to learn what you really use.

**Planning rule** (vol. 21): provision circuits, PDUs and cooling for the server's rated maximum, then use measurements to refine your cost estimates.

Why racks hold so few servers: a DGX B200 is 14.3 kW. Two per rack is 28.6 kW; four per rack is 57.2 kW. The books say a typical enterprise rack was built for about 15 kW, so a rack of GPU servers needs special power and cooling. (The volume-01 notes say a rack "can consume over 100 kW"; that is true for liquid-cooled rack-scale systems such as GB200 NVL72, not for air-cooled DGX racks. Be careful with such ranges.)

## 3. How power gets to the rack

### 3.1 Circuits, voltage and amps

Data-center racks are fed by **three-phase** circuits. The usable power of one circuit is:

```text
usable kW = square root of 3 x line-to-line volts x amps x breaker derating x power factor
```

- **Breaker derating**: you may only load a circuit breaker to 80 percent of its rating for continuous loads (common practice; the NVIDIA table uses 80 percent and also shows 100 percent for sites that allow it).
- **Power factor**: how efficiently the load uses the current; NVIDIA uses 0.95.

`code/part06/facility_calc.py` applies this formula for two circuits and a 14.3 kW server. It reproduced **every row** of NVIDIA's table:

| Volts (line to line) | Amps | Derating | Servers/rack | Capacity (kW) | Demand (kW) | Stranded (kW) |
|---|---|---|---|---|---|---|
| 380 | 32 | 80% | 2 | 32.0 | 28.6 | 3.4 |
| 400 | 32 | 80% | 2 | 33.7 | 28.6 | 5.1 |
| 415 | 32 | 80% | 2 | 35.0 | 28.6 | 6.4 |
| 415 | 60 | 80% | 4 | 65.6 | 57.2 | 8.4 |
| 415 | 63 | 80% | 4 | 68.8 | 57.2 | 11.6 |
| 380 | 32 | 100% | 2 | 40.0 | 28.6 | 11.4 |
| 415 | 32 | 100% | 2 | 43.7 | 28.6 | 15.1 |
| 415 | 60 | 100% | 4 | 81.9 | 57.2 | 24.7 |
| 415 | 63 | 100% | 4 | 86.0 | 57.2 | 28.8 |

(The table's small differences, for example 34 versus 33.7 kW, are rounding.) **Stranded power** is capacity you paid for and installed but cannot use because the next whole server does not fit. Stranded power is a real cost: choose circuits so that the rack is filled efficiently. With two circuits each must be able to carry 50 percent of the rack's peak demand, as NVIDIA's guide says ("N = 2 power circuits").

### 3.2 Redundancy: why servers with internal power supplies need care

A DGX B200 has **six power supplies and needs five of them** to run (internal N+1). It keeps working if one supply loses power, but not if two do, *no matter how redundant the feeds upstream are*. The guide therefore says: traditional power redundancy models are not effective, and you should treat rack provisioning as delivering only **N**, even with two feeds. It compares designs:

| Design | What happens on a failure | Verdict in the guide |
|---|---|---|
| **N with two separate sources** (half the servers on UPS A, half on UPS B) | A failed PDU or UPS affects only half the servers | Fewest dependencies, the best option when only two UPS sources exist |
| **N with one source** | A UPS failure stops all servers; more risk during maintenance | Weaker |
| **N with interleaved dual sources** (each server fed from both) | A failure of either source can take down every server, because losing three of six supplies breaks the 5-of-6 rule | Marked STOP: not recommended |
| **N+1 with a static transfer switch (STS)** | The switch itself becomes a single point of failure | NVIDIA has not tested STS with DGX B200 and does not recommend it |
| **N+1 "6 to make 5"** (six separate sources, one per supply) | A single PDU or UPS failure affects nothing | Highest availability, but few sites can provide six UPS sources; usually limited to 2 servers per rack |

The lesson is general: always ask how a server's internal redundancy interacts with the facility's redundancy.

### 3.3 Rack PDUs

NVIDIA recommends smart rack PDUs (rPDUs) with: a network interface and REST API, per-PDU and per-outlet metering, remote outlet switching, ports for temperature and humidity probes, locking receptacles, and optionally red/blue colours to tell the two circuits apart. These give you power telemetry for monitoring (6.26) and remote power-cycling.

### 3.4 UPS and staged shutdown

A **UPS** (uninterruptible power supply) is a battery that keeps equipment running during an outage for minutes, usually just long enough for generators to start or for an orderly shutdown. The SCL book (chapters 19 and 28) shows how the author handled this on real clusters with the `apcupsd` daemon (for APC UPS units; a similar multi-vendor tool is NUT, Network UPS Tools, covered in 6.26).

#### Configuring `/etc/apcupsd/apcupsd.conf`

When building `apcupsd` from source, the book enables SNMP and CGI support (`./configure --prefix=/usr --sbindir=/sbin --enable-threads --enable-snmp --enable-cgi --with-libwrap=/lib64/libwrap.so.0 --with-cgi-bin=/usr/apache/cgi-bin && make && make install` `(untested here)`) and verifies communication with `apcaccess` (which prints `STATUS: ONLINE`, `LINEV`, `LOADPCT`, `BCHARGE`, `TIMELEFT`). In `/etc/apcupsd/apcupsd.conf`, the key daemon, network, and shutdown parameters from the book's Chapter 28 example are `(untested here)`:

```text
# /etc/apcupsd/apcupsd.conf excerpt (untested here)
UPSNAME Smart-UPS RT 10000
UPSCABLE smart                  # simple, smart, ether, usb
UPSTYPE snmp
DEVICE 195.208.252.115:161:APC:private
#POLLTIME 60                    # polling interval in seconds (default 60)
LOCKFILE /var/lock
SCRIPTDIR /etc/apcupsd
PWRFAILDIR /etc/apcupsd
NOLOGINDIR /etc

# Parameters used on power failure (whichever of BATTERYLEVEL, MINUTES, or TIMEOUT trips first triggers doshutdown)
ONBATTERYDELAY 6                # seconds on battery before reacting to power failure
BATTERYLEVEL 5                  # remaining battery charge (%) that triggers server shutdown
MINUTES 3                       # remaining runtime (minutes) that triggers server shutdown
TIMEOUT 0                       # max seconds on battery (0 disables timer)
ANNOY 300                       # seconds between user warning broadcasts
ANNOYDELAY 60                   # delay after power failure before warning users
NOLOGON disable                 # when to block user logins: disable, timeout, percent, minutes, always
KILLDELAY 0                     # seconds between UPS killpower and shutdown command (0 disables)

# Network Information Server (NIS) for apcaccess and multimon.cgi
NETSERVER on
NISIP 0.0.0.0
NISPORT 3551                    # default port 3551
EVENTSFILE /var/log/apcupsd.events
EVENTSFILEMAX 10                # max kilobytes

UPSCLASS standalone             # standalone | shareslave | sharemaster
UPSMODE disable                 # disable | share
```

(The file also holds EEPROM parameters used by `apctest` such as `WAKEUP 60`, `SLEEP 180`, `LOTRANSFER 208`, `HITRANSFER 253`, `LOWBATT 2`, `OUTPUTVOLTS 230`, and `SELFTEST 336`.) Table 28-1 of the book lists the supported `UPSTYPE` and `DEVICE` combinations:

| `UPSTYPE` | `DEVICE` | Meaning |
|---|---|---|
| `apcsmart` | `/dev/tty**` | Serial COM port connection |
| `usb` | `-` (blank) | USB connection (auto-detected in most cases) |
| `net` | `hostname:port` | Slave connection to another computer running `apcupsd` |
| `dumb` | `/dev/tty**` | Voltage-signalling serial connection for older unmanaged UPSs |
| `pcnet` | `ipaddr:username:passphrase` | APC PowerChute Network Shutdown protocol over IP |
| `snmp` | `hostname:port:vendor:community` | SNMP network connection (UPS must have SNMP enabled) |

#### Staged cluster shutdown scripts (`onbattery`, `offbattery`, and `haltall`)

While `/etc/apcupsd/apccontrol` handles standard `doshutdown` events when `BATTERYLEVEL` or `MINUTES` trips, shutting down an entire cluster takes longer than a single server and benefits from shedding idle nodes early. In the book's Chapter 28 recipe, `/etc/apcupsd/onbattery` emails the administrator (`apcaccess status`) and launches `/etc/apcupsd/haltall` in the background (`nohup /etc/apcupsd/haltall &`), while `/etc/apcupsd/offbattery` aborts an in-progress shutdown if utility power returns (`pkill -9 haltall`) `(untested here)`:

1. Log the event and warn users via `wall`.
2. **Wait 30 minutes (`sleep 1800`)**: most outages are short; if power returns, `offbattery` kills `haltall`.
3. Power off the **idle nodes** (scanning `/etc/nodes` via `ping` and checking if node load `/usr/local/cluster/ndload` is `< 10`, then running `ssh $host /sbin/poweroff`) to stretch the battery for busy nodes.
4. Poll `apcaccess` in `tlwait 5` (`awk '$1 == "TIMELEFT" {printf "%.0f\n", $3}'`) every 60 seconds until only **5 minutes of battery** remain.
5. Stop the batch queue (`qstop $CLUSTERNAME`) and cancel running jobs (`qdel $LIST`).
6. Wait 1 minute (`sleep 60`), power off all remaining compute nodes (`ssh $host /sbin/poweroff`), wait 1 more minute (`sleep 60`), and power off the head node (`/sbin/poweroff`).

```sh
#!/bin/sh
# /etc/apcupsd/haltall excerpt from the book's PBS example (untested here)
CLUSTERNAME=MYCLUSTER
OUT=/etc/apcupsd/halt.log
TPRED=7200

tlprint() {
  t=$(/sbin/apcaccess | awk '$1 == "TIMELEFT" {printf "%.0f\n", $3}')
  echo "TIMELEFT = $t" >> $OUT 2>&1
}

tlwait() {
  while [ $t -gt $1 ]; do
    sleep 60
    t=$(/sbin/apcaccess | awk '$1 == "TIMELEFT" {printf "%.0f\n", $3}')
    echo "TIMELF=$t SECONDS=$SECONDS" >> $OUT 2>&1
    if [ $SECONDS -gt $TPRED ]; then
      break
    fi
  done
}

echo "::: Starting Shutdown process: $(date):::" | wall
tlprint
sleep 1800
tlprint

# Turn off free (idle) nodes
for host in $(cat /etc/nodes); do
  ping $host -i 1 -c 1 > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    avg=$(ssh $host /usr/local/cluster/ndload)
    if [ $avg -lt 10 ]; then
      ssh $host /sbin/poweroff
      sleep 1
    fi
  fi
done

tlprint
tlwait 5
qstop $CLUSTERNAME
LIST=$(qstat -a | grep $CLUSTERNAME | grep " R " || awk -F. '/^[0-9]*\./ {print $1}')
qdel $LIST
sleep 60

# Turn off all remaining nodes, then host computer
for host in $(cat /etc/nodes); do
  ping $host -i 1 -c 1 > /dev/null 2>&1 && ssh $host /sbin/poweroff
done
sleep 60
/sbin/poweroff
```

#### APC SNMP ambient and internal temperature monitoring (`ambtemp.sh` and `upstemp`)

Many APC UPS management cards expose both an internal UPS temperature sensor and an external room probe over SNMP. In Chapter 28, the book pairs `ambtemp.sh` (which queries the APC enterprise MIB OIDs via `snmpget`) with a daemon loop `upstemp` that polls every 10 minutes (`sleep 600`), warns `root` by mail and terminal `write` above `25.0` °C (`TMAXW=25.0`), and runs an immediate `haltall` emergency shutdown above `30.0` °C (`TMAXSH=30.0`) `(untested here)`:

```bash
#!/bin/bash
# /usr/local/cluster/ambtemp.sh (untested here)
# SNMP OID for internal temperature of the APC UPS:
inttempcmd=".1.3.6.1.4.1.318.1.1.1.2.2.2.0"
# SNMP OID for external ambient temperature sensor attached to the APC UPS:
ambtempcmd=".1.3.6.1.4.1.318.1.1.10.2.3.2.1.4.0"

function sendcmd(){
  host=$1
  cmd=$2
  res=$(snmpget -c public -v 2c $host $cmd | awk -F: '{print $4}')
  echo $res
}

tempamb=$(sendcmd ups_3 $ambtempcmd)
echo $tempamb
```

The book cautions that these scripts are examples and must be adapted for your storage servers, scheduler (Slurm `scontrol` instead of Torque `qstop`/`qdel`), power connections, and UPS load distribution.

`code/part06/ups_shutdown_sim.py` models these steps with made-up battery numbers (100 nodes, 60 busy; battery runtime inversely proportional to load). Output:

```text
--- outage lasts 10 min
  t+ 10 min  power restored: shutdown aborted (100 nodes still on, 65 min left)
--- outage lasts 45 min
  t+ 30 min  30 min elapsed: powered off 40 idle nodes; 75 min of battery left
  t+ 45 min  power restored: shutdown aborted (60 nodes still on, 60 min left)
--- long outage
  t+ 30 min  30 min elapsed: powered off 40 idle nodes; 75 min of battery left
  t+101 min  battery at 4.0 min: queue stopped, running jobs cancelled
  t+102 min  all nodes powered off
  t+103 min  head node powered off. End of shutdown.
UPS temperature policy: 22 C ok; 26 C warn admin; 31 C halt cluster now
```

It shows why step 3 matters: shutting idle nodes down gives the busy ones about 15 extra minutes. Real GPU clusters differ: GPU racks draw so much that UPS runtime is often a few minutes, so modern designs rely on generators, and newer racks (the GB300 reference design) put large energy storage in the rack power shelf to flatten peak demand. Checkpointed training jobs should survive a power loss because they can restart (6.21); the staged shutdown mainly protects data and hardware.

## 4. Getting the heat out: air cooling

### 4.1 How much air?

NVIDIA's planning figure is **about 150 cubic feet per minute (CFM) of cold air per kilowatt**. A rack with two DGX B200 (28.6 kW) needs about 4,290 CFM; four per rack (57.2 kW) needs about 8,580 CFM (matches the guide: the calculator printed 4290 and 8580). Each DGX B200 needs up to roughly 2,145 CFM at sea level. A general formula (vol. 21) is `CFM = 3.16 x watts / temperature rise in degrees Fahrenheit`: for 81.6 kW and a 20 C (36 F) rise it gives about 7,160 CFM, which the calculator confirmed (7,163).

### 4.2 Conditions the room must meet

The DGX B200 guide: supply air should generally meet **ASHRAE Class A1** (15 to 32 C allowed) but at most **30 C (86 F)** at the server inlet; the server operates at 5 to 30 C and less at high altitude (5 to 25 C between 5,000 and 10,000 feet). Air must be filtered: at least MERV 13 filters and an ISO 14644-1 Class 8 clean room level for the rack area (dust damages electronics and clogs filters). Noise is high: around 96 to 101 dB sound power, so these are not offices.

### 4.3 Good habits for air-cooled rooms

The guide's list: **aisle containment** (separate hot and cold aisles with physical barriers), **blanking panels** (fill empty rack slots so hot air cannot flow back), brush grommets on cable openings, humidification control, proper filtration, perforated floor tile airflow audits (measured with an anemometer), and computational fluid dynamics (CFD) modelling. Rear-door heat exchangers and in-row coolers are "not typically suitable" for DGX B200 per the guide, but are a normal way to cool other dense racks (section 5).

### 4.4 Airflow direction

From the ADC book: **front-to-back** airflow (cold air in at the port side, hot air out the back) is what most customers prefer, and it cools the network optics first. **Back-to-front** cools the power supplies first and may need extra heat sinks on optics. **Bidirectional fans** can do both but cost a lot. Rule: pick one direction for the whole room before you buy, and make sure every device (servers, storage, switches) matches.

## 5. Liquid cooling

Water or special fluids carry heat far better than air, so they allow denser racks and lower power for cooling. The ADC book describes four types (it says liquid cooling could cut cooling power by about 70 percent and improve PUE, with market growth to billions of dollars):

| Type | How it works | Good for | Cost and trade-offs |
|---|---|---|---|
| **Immersion, single-phase** | Whole servers sit in a tank of non-conductive liquid; pumps move the liquid to a heat exchanger | Very high density | Whole room and all equipment must support it; messy servicing |
| **Immersion, two-phase** | Liquid boils at a low temperature on hot parts, vapour condenses on a cold-water tube at the top of the tank and drips back | Highest density; no external heat exchanger | Fluid choice is critical; specialised |
| **Cold plate (direct to chip)** | Pipes carry liquid to plates sitting on CPUs and GPUs; warm liquid goes to a heat exchanger | High density with normal servers | Equipment is cheaper than immersion; needs plumbing, a coolant distribution unit (CDU), leak detection |
| **Rear-door heat exchanger** | A radiator door at the back of the rack cools the exhaust air with chilled water; can cool about a 20 kW rack at normal chilled-water temperatures | Retrofitting dense air-cooled racks | Simplest; less efficient than the other types; equipment must be air cooled and ideally front-to-back |
| **Spray** | Coolant is sprayed on hot parts | Targeted cooling with little coolant | Equipment must be modified; the book cites 25.8 percent lower total energy than air cooling |

The book names real adopters: Microsoft uses two-phase immersion in production, Google uses cold-plate-like cooling for TPUs, and Meta plans rear-door and cold-plate cooling. (A small error in the book: it expands the rear-door acronym AALC as "air-assisted liquid chromatography" in the text; the acronym appendix correctly says **Air-Assisted Liquid Cooling**.)

NVIDIA's newer rack-scale systems use **hybrid cooling**: the DGX GB300 liquid-cools the most power-hungry parts (GPUs, CPUs) and air-cools the rest, and its rack-integrated design is meant for quick installation of liquid-cooled, high-density compute racks. Liquid cooling adds new things to operate: CDUs, coolant quality and temperature, flow and pressure sensors, leak detection, quick-disconnect couplings, and building-management integration. The GB300 reference architecture also says the data center should generally meet Uptime Institute Tier 3 design standards (or equivalents such as TIA-942-B Rated 3 or EN 50600 Availability Class 3). It notes the building management system's power and cooling telemetry must flow through the uplink interfaces as part of the *untrusted* zone, a security design point (Part 18).

## 6. Efficiency: PUE and the energy bill

**PUE (power usage effectiveness)** = total facility power divided by the power used by the computing equipment. The ideal is 1.0; higher means more of your electricity goes to cooling and losses. Example from the AI Factory notes (illustrative): an 8-server H100 cluster has an IT load of 8 x 10.2 = 81.6 kW; with a PUE of 1.35 the facility draws about 110 kW. With 16 hours/day of training at 110 kW, 4 hours idle at 20 kW and 4 hours maintenance at 40 kW, the monthly energy is 52,800 + 2,400 + 4,800 = **60,000 kWh**, which at $0.12 per kWh is **$7,200 per month**, about $86,400 per year (calculator output matches). The notes list air cooling as lowest capital but highest operating cost and liquid options as higher capital but lower operating cost; compare options by your **measured** PUE, not generic numbers.

A quick check on the ADC percentages: if IT is 40 to 45 percent of the total, PUE is about 2.2 to 2.5, which describes older or poorly cooled sites; modern efficient data centers aim for 1.1 to 1.4.

## 7. Space, racks and cables

**Racks**: NVIDIA does not name a brand, but racks must follow the **EIA-310** standard (19-inch mounting), be at least **24 x 44 inches (600 x 1100 mm)** and at least **48U** tall; NVIDIA recommends **30 x 48 x 52U (700 x 1200 mm)**. A DGX B200 is 10U, weighs over 130 kg and is 897 mm deep, so floor loading and doorways matter. Do **not** share DGX racks with unrelated equipment, and do not put unrelated equipment in spaces between DGX racks that exist to spread the cooling load.

**Building block**: a DGX SuperPOD "scalable unit" (SU) is up to 32 DGX B200 systems, about 458 kW. A full SuperPOD has up to four SUs in the typical build (the reference design can scale much further); with UFM management appliances, up to 127 servers (1,016 GPUs) in the table. Cable counts grow quickly: the guide's table lists 1 SU: 31 nodes, 8 leaf switches, 4 spine switches, 252 node cables; 4 SUs: 127 nodes, 32 leaf, 16 spine, 1,020 node cables and 1,024 spine-leaf cables. Cables concentrate in the management racks and overhead trays, so plan: cable tray type, width, depth and fill ratio, top-of-rack penetrations, structural load, and cable management.

**Cable types and distance limits** (InfiniBand): passive DAC (direct-attach copper) works up to about **5 m** at 100 Gb (the guide says up to 3 m at 400 Gb); active optical cables (AOC) reach up to **30 m**. Distance limits come from signal loss and delay of the **whole path**, so you cannot extend them with patch panels (they add loss) or extra top-of-rack switches (they add latency), says the guide's FAQ. This is why rack distance is limited and why cooling needs and cable lengths conflict.

**Cabling practices from the guide**: bundle cables by purpose (inter-switch links, uplinks), use the right length and allow for bend radius, keep runs under 90 percent of the maximum supported distance, separate copper from fiber, install spare cables in advance, colour-code cable ties by endpoint and label both ends (and along the run).

## 8. People and ownership

The guide's closing point: a deployment succeeds only if five groups agree on the plan: **facility operations** (power, cooling), **IT operations**, the **systems operations center**, **network operations**, and the **application owner**. A fix in one area (cooling) changes budgets, staff and schedules in another. When you propose a cluster, ask: who owns power and cooling? How many kW per rack, on which circuits? What are the inlet temperature and airflow limits? Where are the cable paths? Who is on call for a cooling alarm?

## 9. Monitoring the physical layer

Feed these into 6.26's monitoring: rack inlet and outlet temperature, PDU and outlet power, UPS state and time left, CDU temperature/flow/pressure, leak sensors, BMC sensors (Part 7), GPU temperature and throttle reasons (DCGM). Alert on rising temperature at constant load (a failing fan or blocked airflow), power near the circuit limit, and any containment breach. Practise the response: a cooling failure can overheat a dense rack within minutes, so know in advance which jobs to stop and which nodes to power off first (the staged-shutdown idea).

## 10. Exercises

Tested with the calculators:

1. Run `facility_calc.py` and match each row of the power table by hand for one row.
2. A site offers 3-phase 400 V, 63 A circuits, 80 percent derating. How many DGX B200 fit on two circuits? How much power is stranded? (Compute with the formula, then verify with the script.)
3. Change the cost example: PUE 1.15, electricity $0.08 per kWh, training 20 hours a day. What changes most?
4. Run `ups_shutdown_sim.py`; change the number of busy nodes and the battery size; find the busy-node count at which step 3 no longer helps much.

Desk exercises:

5. Sketch a "6 to make 5" power diagram and a diagram with a failed UPS in the interleaved design.
6. List what you would ask the facility team before accepting 16 DGX B200 servers.
7. Write a one-page runbook for a cooling failure.

## 11. Interview angles

- Why can only two DGX B200 servers go in a typical air-cooled rack?
- What is stranded power and how do you reduce it?
- Why does internal N+1 power supply design break the usual dual-feed redundancy model?
- Compare air cooling with cold-plate and immersion cooling.
- What is PUE? What does a PUE of 1.5 mean?
- Why can't InfiniBand cable limits be extended with patch panels?
- What happens in your cluster when power is lost for 10 minutes? For two hours?
- Which teams must agree before a GPU cluster is installed?

## 12. Checkpoint questions (25)

1. Define watt, kilowatt, megawatt, kilowatt-hour.
2. What are the three resource limits of a data center?
3. Roughly how is data center electricity split between IT and cooling?
4. What is a DGX H100's rated maximum? A DGX B200's?
5. What does "4 x 3.3 kW = 13.2 kW" actually represent?
6. Write the three-phase circuit power formula.
7. What do breaker derating and power factor mean?
8. What is stranded power?
9. How many of the six power supplies must a DGX B200 have energized?
10. Why is interleaved dual-source power not recommended?
11. What are the issues with static transfer switches here?
12. What is "6 to make 5"?
13. What features should a smart rack PDU have?
14. What does a UPS do and for how long?
15. Describe the staged shutdown in six steps.
16. In `apcupsd.conf`, which three parameters work together to trigger shutdown on power failure, what are the APC SNMP OIDs for internal UPS and external ambient sensor temperatures, and at what temperatures does the book's `upstemp` script warn and halt? (Answer: `BATTERYLEVEL`, `MINUTES`, and `TIMEOUT`—whichever trips first; `.1.3.6.1.4.1.318.1.1.1.2.2.2.0` for internal UPS temperature and `.1.3.6.1.4.1.318.1.1.10.2.3.2.1.4.0` for external ambient sensor temperature; warn above `25.0` °C and halt above `30.0` °C.)
17. What is NVIDIA's airflow planning figure per kW?
18. What inlet temperature limits apply to DGX B200?
19. What air filtration is required?
20. Name five good air-cooling habits.
21. Compare front-to-back and back-to-front airflow.
22. List the four liquid cooling methods and one trait each.
23. What is hybrid cooling in the GB300?
24. Define PUE; what is ideal?
25. Which cable distance limits apply to DAC and AOC, and why can't they be extended?

## 13. Sources and review notes

- Book source (`supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`):
  - Chapter `19. Cluster Status Monitoring Systems` (read in full): APCUPS (`apcupsd`, `apcaccess`, `onbattery`/`offbattery`, `multimon.cgi`, `/etc/apcupsd/hosts.conf`).
  - Chapter `28. One-Two-Three Instructions` (read in full): `/etc/apcupsd/apcupsd.conf` parameters (`UPSCABLE`, `UPSTYPE`, `DEVICE`, `ONBATTERYDELAY`, `BATTERYLEVEL`, `MINUTES`, `TIMEOUT`, `NETSERVER`, `NISIP`, `NISPORT`, and Table 28-1 `UPSTYPE`/`DEVICE` values), `onbattery`/`offbattery` and the staged cluster shutdown script (`haltall`), and the `upstemp`/`ambtemp.sh` APC SNMP temperature scripts (`.1.3.6.1.4.1.318.1.1.1.2.2.2.0` internal UPS temperature and `.1.3.6.1.4.1.318.1.1.10.2.3.2.1.4.0` external sensor temperature).
- Thermal and power concepts, airflow, liquid cooling types, PUE, rack power budgets: *AI Data Center Network Design and Technologies* (ADC), chapter 5, read in full; restated in my words.
- DGX B200 power profiles, power provisioning table, redundancy designs, ASHRAE/filtration, best practices, cabling, FAQ: NVIDIA, *Data Center Best Practices with DGX B200* (the "superpod-b200-dc" document in the corpus), read in full. It is marked NVIDIA confidential in the source; I summarised without reproducing its slides.
- GB300 hybrid cooling, power shelves with energy storage, BMS telemetry zone: NVIDIA, *DGX SuperPOD Reference Architecture, DGX GB300* (corpus), keyword passages only.
- Power and cooling planning numbers, energy cost example, CFM formula: the AI Factory volume-21 chapter 5 of the NVIDIA-DevOps notes (figures marked there as planning assumptions). The volume-01 summary's statements about rack power ("over 40 to 100 kW", "enterprise racks 15 kW") are loose; I limited them as above.
- Original and run: `facility_calc.py` (matches all nine table rows and the book numbers), `ups_shutdown_sim.py` (invented battery parameters).
- Corrections noted: the ADC book's "air-assisted liquid chromatography" is a typo for liquid cooling; the 13.2 kW figure is supply capacity, not draw.
- Unverified: current NVIDIA specifications beyond the quoted documents, regional electrical code details (derating rules vary), CDU and coolant specifics, `apcupsd.conf` and `haltall`/`ambtemp.sh` scripts (from the book, not run here), UPS runtime for real GPU racks.
