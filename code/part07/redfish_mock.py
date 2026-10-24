#!/usr/bin/env python3
"""A small Redfish service for learning and testing. NOT a real BMC and NOT a full implementation.

Standard library only. It follows the rules of DSP0266 closely enough to practise on:
service root, OData documents, collections with Members and Members@odata.count, Basic and session
authentication, ETag headers, $select/$top/$skip/$expand/only query options and Redfish-style errors.
Later chapters add actions, tasks, events and updates on the same server (see the 'features' in
handle_* functions). Two profiles use different IDs on purpose, so clients must discover URIs.

Run:  python3 redfish_mock.py --profile dgx --port 8443
"""
import argparse, base64, copy, hashlib, json, queue, re, secrets, sys, threading, time, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

def odata(path, typ, **kw):
    d = {"@odata.id": path, "@odata.type": typ}
    d.update(kw)
    return d


def build_tree(profile):
    """Return {uri: resource}. 'dgx' uses vendor-style IDs, 'generic' uses numbers."""
    if profile == "dgx":
        sysid, chid, mgrid = "System_0", "Chassis_0", "BMC_0"
        gpuboard = "HGX_Baseboard_0"
    else:
        sysid, chid, mgrid = "1", "1", "1"
        gpuboard = None
    R = "/redfish/v1"
    t = {}
    t[R] = odata(R, "#ServiceRoot.v1_17_0.ServiceRoot", Id="RootService", Name="Root Service",
                 RedfishVersion="1.17.0", UUID="92384634-2938-2342-8820-489239905423",
                 Systems={"@odata.id": f"{R}/Systems"}, Chassis={"@odata.id": f"{R}/Chassis"},
                 Managers={"@odata.id": f"{R}/Managers"},
                 SessionService={"@odata.id": f"{R}/SessionService"},
                 AccountService={"@odata.id": f"{R}/AccountService"},
                 UpdateService={"@odata.id": f"{R}/UpdateService"},
                 Tasks={"@odata.id": f"{R}/TaskService"},
                 EventService={"@odata.id": f"{R}/EventService"},
                 ProtocolFeaturesSupported={
                     "ExpandQuery": {"ExpandAll": False, "Levels": True, "Links": False, "NoLinks": False, "MaxLevels": 2},
                     "SelectQuery": True, "OnlyMemberQuery": True, "ExcerptQuery": False,
                     "FilterQuery": False},
                 Links={"Sessions": {"@odata.id": f"{R}/SessionService/Sessions"}})
    sysmembers = [f"{R}/Systems/{sysid}"] + ([f"{R}/Systems/{gpuboard}"] if gpuboard else [])
    for coll, name, typ, members in [
        ("Systems", "Computer System Collection", "#ComputerSystemCollection.ComputerSystemCollection", sysmembers),
        ("Chassis", "Chassis Collection", "#ChassisCollection.ChassisCollection", [f"{R}/Chassis/{chid}"]),
        ("Managers", "Manager Collection", "#ManagerCollection.ManagerCollection", [f"{R}/Managers/{mgrid}"]),
    ]:
        t[f"{R}/{coll}"] = odata(f"{R}/{coll}", typ, Name=name,
                                 Members=[{"@odata.id": m} for m in members],
                                 **{"Members@odata.count": len(members)})
    t[f"{R}/Systems/{sysid}"] = odata(
        f"{R}/Systems/{sysid}", "#ComputerSystem.v1_17_0.ComputerSystem", Id=sysid, Name="Compute node",
        SystemType="Physical", Manufacturer="ExampleCorp", Model="GPU-8", SerialNumber="SN0001",
        PowerState="On", Status={"State": "Enabled", "Health": "OK", "HealthRollup": "OK"},
        Boot={"BootSourceOverrideEnabled": "Disabled", "BootSourceOverrideTarget": "None"},
        ProcessorSummary={"Count": 2, "Model": "ExampleCPU"}, MemorySummary={"TotalSystemMemoryGiB": 2048},
        Storage={"@odata.id": f"{R}/Systems/{sysid}/Storage"},
        Links={"Chassis": [{"@odata.id": f"{R}/Chassis/{chid}"}],
               "ManagedBy": [{"@odata.id": f"{R}/Managers/{mgrid}"}]},
        Actions={"#ComputerSystem.Reset": {
            "target": f"{R}/Systems/{sysid}/Actions/ComputerSystem.Reset",
            "ResetType@Redfish.AllowableValues": ["On", "ForceOff", "GracefulShutdown", "GracefulRestart",
                                                   "ForceRestart", "Nmi", "PowerCycle", "FullPowerCycle"]}})
    if gpuboard:
        t[f"{R}/Systems/{gpuboard}"] = odata(
            f"{R}/Systems/{gpuboard}", "#ComputerSystem.v1_17_0.ComputerSystem", Id=gpuboard,
            Name="GPU baseboard", SystemType="Physical", PowerState="On",
            Status={"State": "Enabled", "Health": "OK"},
            Processors={"@odata.id": f"{R}/Systems/{gpuboard}/Processors"},
            Links={"Chassis": [{"@odata.id": f"{R}/Chassis/{chid}"}], "ManagedBy": [{"@odata.id": f"{R}/Managers/{mgrid}"}]})
        gpus = [f"GPU_SXM_{i}" for i in range(1, 9)]
        t[f"{R}/Systems/{gpuboard}/Processors"] = odata(
            f"{R}/Systems/{gpuboard}/Processors", "#ProcessorCollection.ProcessorCollection", Name="Processors",
            Members=[{"@odata.id": f"{R}/Systems/{gpuboard}/Processors/{g}"} for g in gpus],
            **{"Members@odata.count": len(gpus)})
        for i, g in enumerate(gpus):
            base = f"{R}/Systems/{gpuboard}/Processors/{g}"
            t[base] = odata(base, "#Processor.v1_20_1.Processor", Id=g, Name=f"GPU {i + 1}", ProcessorType="GPU",
                            Model="ExampleGPU", Status={"State": "Enabled", "Health": "OK"},
                            EnvironmentMetrics={"@odata.id": f"{base}/EnvironmentMetrics"})
            t[f"{base}/EnvironmentMetrics"] = odata(
                f"{base}/EnvironmentMetrics", "#EnvironmentMetrics.v1_3_2.EnvironmentMetrics", Id="EnvironmentMetrics",
                Name=f"{g} environment metrics", PowerWatts={"Reading": 310.0 + 7 * i},
                TemperatureCelsius={"Reading": 55.0 + i})
    t[f"{R}/Chassis/{chid}"] = odata(
        f"{R}/Chassis/{chid}", "#Chassis.v1_23_0.Chassis", Id=chid, Name="Chassis", ChassisType="RackMount",
        PowerState="On", Status={"State": "Enabled", "Health": "OK"},
        Sensors={"@odata.id": f"{R}/Chassis/{chid}/Sensors"},
        PCIeDevices={"@odata.id": f"{R}/Chassis/{chid}/PCIeDevices"},
        NetworkAdapters={"@odata.id": f"{R}/Chassis/{chid}/NetworkAdapters"},
        Links={"ComputerSystems": [{"@odata.id": m} for m in sysmembers],
               "ManagedBy": [{"@odata.id": f"{R}/Managers/{mgrid}"}]})
    # (id, reading type, value, units, physical context, upper caution, upper critical)
    sens = [("Temp_Inlet", "Temperature", 24.5, "Cel", "Intake", 35.0, 40.0),
            ("Temp_GPU0", "Temperature", 61.0, "Cel", "GPU", 80.0, 88.0),
            ("Fan_1", "Rotational", 7200, "RPM", "Fan", None, None),
            ("Power_Total", "Power", 4200.0, "W", "Chassis", 9000.0, 10200.0)]
    t[f"{R}/Chassis/{chid}/Sensors"] = odata(
        f"{R}/Chassis/{chid}/Sensors", "#SensorCollection.SensorCollection", Name="Sensors",
        Members=[{"@odata.id": f"{R}/Chassis/{chid}/Sensors/{s[0]}"} for s in sens],
        **{"Members@odata.count": len(sens)})
    for sid, reading_type, val, units, ctx, caution, crit in sens:
        sensor = odata(
            f"{R}/Chassis/{chid}/Sensors/{sid}", "#Sensor.v1_9_0.Sensor", Id=sid, Name=sid.replace("_", " "),
            ReadingType=reading_type, Reading=val, ReadingUnits=units, PhysicalContext=ctx,
            Status={"State": "Enabled", "Health": "OK"})
        if crit is not None:
            sensor["Thresholds"] = {"UpperCaution": {"Reading": caution, "Activation": "Increasing"},
                                    "UpperCritical": {"Reading": crit, "Activation": "Increasing"}}
        t[f"{R}/Chassis/{chid}/Sensors/{sid}"] = sensor
    t[f"{R}/Managers/{mgrid}"] = odata(
        f"{R}/Managers/{mgrid}", "#Manager.v1_19_0.Manager", Id=mgrid, Name="BMC", ManagerType="BMC",
        FirmwareVersion="1.0.0", Status={"State": "Enabled", "Health": "OK"},
        Links={"ManagerForServers": [{"@odata.id": m} for m in sysmembers],
               "ManagerForChassis": [{"@odata.id": f"{R}/Chassis/{chid}"}],
               "ManagerInChassis": {"@odata.id": f"{R}/Chassis/{chid}"}})
    # ---- PCIe devices (8 GPUs + 8 NICs), network adapters with one port each, boot drives ----
    pcie = [(f"GPU_{i}", "GPU", "ExampleGPU") for i in range(1, 9)] + [(f"NIC_{i}", "NIC", "ExampleNIC-400G") for i in range(1, 9)]
    t[f"{R}/Chassis/{chid}/PCIeDevices"] = odata(
        f"{R}/Chassis/{chid}/PCIeDevices", "#PCIeDeviceCollection.PCIeDeviceCollection", Name="PCIe Devices",
        Members=[{"@odata.id": f"{R}/Chassis/{chid}/PCIeDevices/{p[0]}"} for p in pcie], **{"Members@odata.count": len(pcie)})
    for pid, kind, model in pcie:
        u = f"{R}/Chassis/{chid}/PCIeDevices/{pid}"
        t[u] = odata(u, "#PCIeDevice.v1_23_0.PCIeDevice", Id=pid, Name=f"{kind} {pid}", Model=model, DeviceType="SingleFunction",
                     FirmwareVersion="1.0", Status={"State": "Enabled", "Health": "OK"},
                     PCIeInterface={"PCIeType": "Gen5", "MaxPCIeType": "Gen5", "LanesInUse": 16, "MaxLanes": 16})
    nics = [f"NIC_{i}" for i in range(1, 9)]
    t[f"{R}/Chassis/{chid}/NetworkAdapters"] = odata(
        f"{R}/Chassis/{chid}/NetworkAdapters", "#NetworkAdapterCollection.NetworkAdapterCollection", Name="Network Adapters",
        Members=[{"@odata.id": f"{R}/Chassis/{chid}/NetworkAdapters/{n}"} for n in nics], **{"Members@odata.count": len(nics)})
    for n in nics:
        u = f"{R}/Chassis/{chid}/NetworkAdapters/{n}"
        t[u] = odata(u, "#NetworkAdapter.v1_14_0.NetworkAdapter", Id=n, Name=f"Compute NIC {n}", Manufacturer="ExampleCorp",
                     Model="ExampleNIC-400G", Status={"State": "Enabled", "Health": "OK"}, Ports={"@odata.id": f"{u}/Ports"})
        t[f"{u}/Ports"] = odata(f"{u}/Ports", "#PortCollection.PortCollection", Name="Ports",
                                Members=[{"@odata.id": f"{u}/Ports/1"}], **{"Members@odata.count": 1})
        t[f"{u}/Ports/1"] = odata(f"{u}/Ports/1", "#Port.v1_20_0.Port", Id="1", Name=f"{n} port 1", PortProtocol="Ethernet",
                                  LinkNetworkTechnology="Ethernet", LinkState="Enabled", LinkStatus="LinkUp",
                                  CurrentSpeedGbps=400.0, MaxSpeedGbps=400.0, ActiveWidth=4, Width=4,
                                  Status={"State": "Enabled", "Health": "OK"})
    st_u = f"{R}/Systems/{sysid}/Storage"
    dr_u = f"{R}/Chassis/{chid}/Drives"            # Drive URIs under Storage are deprecated; drives live under the chassis
    t[st_u] = odata(st_u, "#StorageCollection.StorageCollection", Name="Storage", Members=[{"@odata.id": f"{st_u}/BootNVMe"}],
                    **{"Members@odata.count": 1})
    t[f"{st_u}/BootNVMe"] = odata(f"{st_u}/BootNVMe", "#Storage.v1_23_0.Storage", Id="BootNVMe", Name="Boot NVMe",
                                  Status={"State": "Enabled", "Health": "OK"}, Drives=[{"@odata.id": f"{dr_u}/1"}, {"@odata.id": f"{dr_u}/2"}],
                                  **{"Drives@odata.count": 2})
    t[dr_u] = odata(dr_u, "#DriveCollection.DriveCollection", Name="Drives", Members=[{"@odata.id": f"{dr_u}/1"}, {"@odata.id": f"{dr_u}/2"}],
                    **{"Members@odata.count": 2})
    t[f"{R}/Chassis/{chid}"]["Drives"] = {"@odata.id": dr_u}
    for d in (1, 2):
        t[f"{dr_u}/{d}"] = odata(
            f"{dr_u}/{d}", "#Drive.v1_22_0.Drive", Id=str(d), Name=f"Boot drive {d}", MediaType="SSD", Protocol="NVMe",
            CapacityBytes=1920383410176, PredictedMediaLifeLeftPercent=97, FailurePredicted=False, CapableSpeedGbs=32.0,
            NegotiatedSpeedGbs=32.0, Status={"State": "Enabled", "Health": "OK"})
    # ---- CPUs of the host system, and the modern thermal and power subsystems of the chassis ----
    t[f"{R}/Systems/{sysid}"]["Processors"] = {"@odata.id": f"{R}/Systems/{sysid}/Processors"}
    cpus = ["CPU_1", "CPU_2"]
    t[f"{R}/Systems/{sysid}/Processors"] = odata(
        f"{R}/Systems/{sysid}/Processors", "#ProcessorCollection.ProcessorCollection", Name="Processors",
        Members=[{"@odata.id": f"{R}/Systems/{sysid}/Processors/{c}"} for c in cpus], **{"Members@odata.count": len(cpus)})
    for i, cname in enumerate(cpus):
        u = f"{R}/Systems/{sysid}/Processors/{cname}"
        t[u] = odata(u, "#Processor.v1_20_1.Processor", Id=cname, Name=f"CPU {i + 1}", ProcessorType="CPU", Model="ExampleCPU",
                     Status={"State": "Enabled", "Health": "OK"})
    ch = f"{R}/Chassis/{chid}"
    t[ch]["ThermalSubsystem"] = {"@odata.id": f"{ch}/ThermalSubsystem"}
    t[ch]["PowerSubsystem"] = {"@odata.id": f"{ch}/PowerSubsystem"}
    t[f"{ch}/ThermalSubsystem"] = odata(f"{ch}/ThermalSubsystem", "#ThermalSubsystem.v1_5_0.ThermalSubsystem", Id="ThermalSubsystem",
                                        Name="Thermal subsystem", Status={"State": "Enabled", "Health": "OK"},
                                        Fans={"@odata.id": f"{ch}/ThermalSubsystem/Fans"})
    t[f"{ch}/ThermalSubsystem/Fans"] = odata(f"{ch}/ThermalSubsystem/Fans", "#FanCollection.FanCollection", Name="Fans",
                                             Members=[{"@odata.id": f"{ch}/ThermalSubsystem/Fans/{n}"} for n in (1, 2)], **{"Members@odata.count": 2})
    for n in (1, 2):
        t[f"{ch}/ThermalSubsystem/Fans/{n}"] = odata(f"{ch}/ThermalSubsystem/Fans/{n}", "#Fan.v1_6_0.Fan", Id=str(n), Name=f"Fan {n}",
                                                     SpeedPercent={"Reading": 55}, Status={"State": "Enabled", "Health": "OK"})
    t[f"{ch}/PowerSubsystem"] = odata(f"{ch}/PowerSubsystem", "#PowerSubsystem.v1_2_0.PowerSubsystem", Id="PowerSubsystem",
                                      Name="Power subsystem", CapacityWatts=10200, Status={"State": "Enabled", "Health": "OK"},
                                      PowerSupplies={"@odata.id": f"{ch}/PowerSubsystem/PowerSupplies"})
    t[f"{ch}/PowerSubsystem/PowerSupplies"] = odata(f"{ch}/PowerSubsystem/PowerSupplies", "#PowerSupplyCollection.PowerSupplyCollection",
                                                    Name="Power supplies", Members=[{"@odata.id": f"{ch}/PowerSubsystem/PowerSupplies/{n}"} for n in (1, 2, 3, 4, 5, 6)],
                                                    **{"Members@odata.count": 6})
    for n in range(1, 7):
        t[f"{ch}/PowerSubsystem/PowerSupplies/{n}"] = odata(f"{ch}/PowerSubsystem/PowerSupplies/{n}", "#PowerSupply.v1_8_0.PowerSupply",
                                                            Id=str(n), Name=f"Power supply {n}", PowerCapacityWatts=3300,
                                                            LineInputStatus="Normal", Status={"State": "Enabled", "Health": "OK"})
    t[f"{R}/Managers/{mgrid}"]["NetworkProtocol"] = {"@odata.id": f"{R}/Managers/{mgrid}/NetworkProtocol"}
    t[f"{R}/Managers/{mgrid}/NetworkProtocol"] = odata(
        f"{R}/Managers/{mgrid}/NetworkProtocol", "#ManagerNetworkProtocol.v1_10_1.ManagerNetworkProtocol", Id="NetworkProtocol",
        Name="Manager Network Protocol", HostName="bmc-lab", FQDN="bmc-lab.example.net", Status={"State": "Enabled", "Health": "OK"},
        HTTP={"ProtocolEnabled": True, "Port": 80}, HTTPS={"ProtocolEnabled": True, "Port": 443},
        IPMI={"ProtocolEnabled": True, "Port": 623}, SSH={"ProtocolEnabled": True, "Port": 22},
        Telnet={"ProtocolEnabled": True, "Port": 23}, SNMP={"ProtocolEnabled": True, "Port": 161},
        SSDP={"ProtocolEnabled": True, "Port": 1900, "NotifyMulticastIntervalSeconds": 600, "NotifyTTL": 5, "NotifyIPv6Scope": "Site"},
        NTP={"ProtocolEnabled": False, "NTPServers": []}, KVMIP={"ProtocolEnabled": True, "Port": 5900},
        VirtualMedia={"ProtocolEnabled": True, "Port": 443})
    t[f"{R}/SessionService"] = odata(f"{R}/SessionService", "#SessionService.v1_1_8.SessionService",
                                    Id="SessionService", Name="Session Service", ServiceEnabled=True,
                                    SessionTimeout=300, Sessions={"@odata.id": f"{R}/SessionService/Sessions"})
    t[f"{R}/SessionService/Sessions"] = odata(
        f"{R}/SessionService/Sessions", "#SessionCollection.SessionCollection", Name="Session Collection",
        Members=[], **{"Members@odata.count": 0})
    t[f"{R}/AccountService"] = odata(f"{R}/AccountService", "#AccountService.v1_17_0.AccountService",
                                    Id="AccountService", Name="Account Service", ServiceEnabled=True)
    return t


ROLE_PRIVS = {   # DSP0266 table 41 (13.4.2.1)
    "Administrator": ["Login", "ConfigureManager", "ConfigureUsers", "ConfigureComponents", "ConfigureSelf"],
    "Operator": ["Login", "ConfigureComponents", "ConfigureSelf"],
    "ReadOnly": ["Login", "ConfigureSelf"],
}
# (user, password, role, password_change_required)
SEED_ACCOUNTS = [("admin", "adminpass", "Administrator", False), ("operator", "operpass", "Operator", False),
                 ("viewer", "viewpass", "ReadOnly", False), ("factory", "changeme1", "Administrator", True)]


def load_mockup(root):
    """Load a DMTF mockup folder (each resource is <dir>/index.json) as {uri: resource}. Read-only data."""
    import os
    tree = {}
    for d, _, files in os.walk(root):
        if "index.json" in files:
            rel = os.path.relpath(d, root)
            uri = "/redfish/v1" + ("" if rel == "." else "/" + rel.replace(os.sep, "/"))
            with open(os.path.join(d, "index.json")) as f:
                try:
                    tree[uri] = json.load(f)
                except ValueError:
                    pass
    return tree


class State:
    def __init__(self, profile, mockup=None):
        self.static = mockup is not None
        self.tree = load_mockup(mockup) if mockup else build_tree(profile)
        self.sessions = {}                      # token -> {user, role, uri, last}
        self.lock = threading.Lock()
        self.profile = profile
        self.next_session = 1
        self.next_account = 1
        self.require_etag = False
        self.now = time.time                    # tests replace this to move time without sleeping
        self.session_timeout = 300
        self.lockout_threshold = 3
        self.lockout_duration = 30
        self.min_password_length = 8
        self.basic_enabled = True
        self.accounts = {}                      # user -> dict(password, role, enabled, fails, locked_until, pcr, uri)
        self.async_reset = False                # True: Reset answers 202 + task (a slow BMC)
        self.task_seconds = 20
        self.tasks = {}                         # id -> dict(start, dur, final, state, cancelled)
        self.next_task = 1
        self.subs = {}                          # id -> dict(uri, dest, filters..., failures)
        self.next_sub = 1
        self.sse = []                           # list of (queue, filters)
        self.event_id = 1
        self.delivery_attempts = 3
        self.sent_log = []                      # (sub id, ok) for tests
        self.reset_ids = []                     # not used by clients; for tests
        if self.static:
            for u, pw, role, pcr in SEED_ACCOUNTS:
                self.add_account(u, pw, role, pcr)
            return
        self.add_services()
        R = "/redfish/v1/AccountService"
        self.tree[f"{R}"].update(HTTPBasicAuth="Enabled", MinPasswordLength=8, AccountLockoutThreshold=3,
                                 AccountLockoutDuration=30, Accounts={"@odata.id": f"{R}/Accounts"},
                                 Roles={"@odata.id": f"{R}/Roles"})
        self.tree[f"{R}/Accounts"] = odata(f"{R}/Accounts", "#ManagerAccountCollection.ManagerAccountCollection",
                                           Name="Accounts Collection", Members=[], **{"Members@odata.count": 0})
        self.tree[f"{R}/Roles"] = odata(f"{R}/Roles", "#RoleCollection.RoleCollection", Name="Roles Collection",
                                        Members=[{"@odata.id": f"{R}/Roles/{r}"} for r in ROLE_PRIVS],
                                        **{"Members@odata.count": len(ROLE_PRIVS)})
        for r, p in ROLE_PRIVS.items():
            self.tree[f"{R}/Roles/{r}"] = odata(f"{R}/Roles/{r}", "#Role.v1_3_3.Role", Id=r, Name="User Role",
                                                IsPredefined=True, AssignedPrivileges=p, RoleId=r)
        for u, pw, role, pcr in SEED_ACCOUNTS:
            self.add_account(u, pw, role, pcr)
        import mock_update, mock_logs, mock_bios
        mock_update.install_state(self)
        mock_logs.install_state(self)
        mock_bios.install_state(self)
        import mock_certs
        mock_certs.install_state(self)

    def add_services(self):
        R = "/redfish/v1"
        self.tree[f"{R}/TaskService"] = odata(f"{R}/TaskService", "#TaskService.v1_2_1.TaskService", Id="TaskService",
                                              Name="Task Service", ServiceEnabled=True,
                                              Tasks={"@odata.id": f"{R}/TaskService/Tasks"})
        self.tree[f"{R}/TaskService/Tasks"] = odata(f"{R}/TaskService/Tasks", "#TaskCollection.TaskCollection",
                                                    Name="Task Collection", Members=[], **{"Members@odata.count": 0})
        self.tree[f"{R}/EventService"] = odata(
            f"{R}/EventService", "#EventService.v1_10_1.EventService", Id="EventService", Name="Event Service",
            ServiceEnabled=True, DeliveryRetryAttempts=3, DeliveryRetryIntervalSeconds=30,
            EventFormatTypes=["Event"], RegistryPrefixes=["Base", "Alert", "ResourceEvent"],
            ResourceTypes=["ComputerSystem", "Chassis", "Task"], ServerSentEventUri=f"{R}/EventService/SSE",
            SSEFilterPropertiesSupported={"EventFormatType": True, "MessageId": True, "OriginResource": False,
                                          "RegistryPrefix": True, "ResourceType": True, "SubordinateResources": False,
                                          "MetricReportDefinition": False},
            Subscriptions={"@odata.id": f"{R}/EventService/Subscriptions"},
            Actions={"#EventService.SubmitTestEvent": {"target": f"{R}/EventService/Actions/EventService.SubmitTestEvent"}})
        self.tree[f"{R}/EventService/Subscriptions"] = odata(
            f"{R}/EventService/Subscriptions", "#EventDestinationCollection.EventDestinationCollection",
            Name="Event Subscriptions Collection", Members=[], **{"Members@odata.count": 0})

    # ---- tasks ---------------------------------------------------------
    TASK_MSG = {
        "TransferringToComponent": "Image '%1' is being transferred to '%2'.",
        "VerifyingAtComponent": "Image '%1' is being verified at '%2'.",
        "InstallingOnComponent": "Image '%1' is being installed on '%2'.",
        "AwaitToActivate": "Awaiting for an action to proceed with activating image '%1' on '%2'.",
        "UpdateSuccessful": "Device '%1' successfully updated with image '%2'.",
        "UpdateSkippedSameVersion": "Device '%1' skipped the update with image '%2' because the same version is already installed.",
        "UpdateSkippedVersionTooLow": "Device '%1' skipped the update with image '%2' due to the minimum version requirement.",
        "UpdateNotApplicable": "Image '%1' was not applicable to device '%2'.",
        "TransferFailed": "Transfer of image '%1' to '%2' failed.",
        "VerificationFailed": "Verification of image '%1' at '%2' failed.",
    }

    def new_task(self, name, final, stages=None, fail=False, pending=False, on_start=None):
        with self.lock:
            tid = str(self.next_task); self.next_task += 1
            uri = f"/redfish/v1/TaskService/Tasks/{tid}"
            self.tasks[tid] = {"start": None if pending else self.now(), "dur": self.task_seconds, "final": final, "name": name,
                               "cancelled": False, "uri": uri, "stages": stages or [], "fail": fail, "pending": pending,
                               "on_start": on_start}
            self.tree[uri] = self.task_resource(tid)
            coll = self.tree["/redfish/v1/TaskService/Tasks"]
            coll["Members"].append({"@odata.id": uri}); coll["Members@odata.count"] = len(coll["Members"])
        return tid

    def task_end(self, t):
        """Seconds after the start at which the task is over: a failing task stops soon after its failure stage."""
        if t["fail"] and t["stages"]:
            return t["dur"] * min(1.0, t["stages"][-1][0] + 0.1)
        return t["dur"]

    def task_resource(self, tid):
        t = self.tasks[tid]
        if t["pending"]:
            state, pct, elapsed = "Pending", 0, 0.0
        else:
            elapsed = self.now() - t["start"]
            end = self.task_end(t)
            if t["cancelled"]:
                state, pct = "Cancelled", None
            elif elapsed >= end:
                state, pct = ("Exception" if t["fail"] else "Completed"), 100
            else:
                state, pct = "Running", int(100 * elapsed / end)
        status = "Warning" if state == "Cancelled" else ("Critical" if state == "Exception" else "OK")
        r = odata(t["uri"], "#Task.v1_7_4.Task", Id=tid, Name=t["name"], TaskState=state, TaskStatus=status)
        if t["start"] is not None:
            r["StartTime"] = iso(t["start"])
        if pct is not None:
            r["PercentComplete"] = pct
        if state in ("Completed", "Cancelled", "Exception"):
            r["EndTime"] = iso(t["start"] + min(elapsed, self.task_end(t)))
        msgs = []
        for frac, mid, args, sev in t["stages"]:
            if not t["pending"] and elapsed >= frac * t["dur"]:
                text = self.TASK_MSG.get(mid, mid)
                for i, a in enumerate(args, 1):
                    text = text.replace(f"%{i}", str(a))
                msgs.append({"@odata.type": "#Message.v1_1_1.Message", "MessageId": f"Update.1.0.{mid}", "Message": text,
                             "MessageArgs": [str(a) for a in args], "Severity": sev})
        if msgs:
            r["Messages"] = msgs
        r["TaskMonitor"] = f"/redfish/v1/TaskService/TaskMonitors/{tid}"
        return r

    def tick(self):
        """Run the completion step of every task whose time is up (e.g. stage new firmware), once."""
        for tid, t in list(self.tasks.items()):
            if t["pending"] or t["cancelled"] or t.get("applied") or t["start"] is None:
                continue
            if self.now() - t["start"] >= self.task_end(t):
                t["applied"] = True
                if not t["fail"] and t["final"].get("apply"):
                    t["final"]["apply"]()

    def start_pending(self):
        n = 0
        for tid, t in self.tasks.items():
            if t["pending"] and not t["cancelled"]:
                t["pending"] = False; t["start"] = self.now(); n += 1
                if t.get("on_start"):
                    t["on_start"]()
        return n

    # ---- events --------------------------------------------------------
    def emit(self, message_id, origin, severity="OK", message="", rtype="ComputerSystem"):
        """Deliver an event to every matching subscription (push) and every open SSE stream."""
        with self.lock:
            eid = self.event_id; self.event_id += 1
        prefix = message_id.split(".")[0]
        if hasattr(self, "logs"):
            import mock_logs
            mock_logs.log_event(self, message_id, "OK" if severity == "OK" else severity, message or message_id, origin)
        evt = {"@odata.type": "#Event.v1_6_0.Event", "Id": str(eid), "Name": "Event Array",
               "Events": [{"MemberId": "1", "EventId": str(eid), "EventTimestamp": iso(self.now()),
                           "Severity": severity, "Message": message, "MessageId": message_id,
                           "OriginOfCondition": {"@odata.id": origin}}]}
        for sid, sub in list(self.subs.items()):
            if not self.matches(sub, message_id, prefix, rtype):
                continue
            body = dict(evt, Context=sub["context"])
            ok = self.deliver(sub["dest"], body)
            self.sent_log.append((sid, ok))
            if ok:
                sub["failures"] = 0
            else:
                sub["failures"] += 1
                if sub["policy"] == "TerminateAfterRetries" and sub["failures"] >= self.delivery_attempts:
                    self.remove_sub(sid)
        for q, flt in list(self.sse):
            if self.matches(flt, message_id, prefix, rtype):
                q.put((eid, evt))

    @staticmethod
    def matches(f, mid, prefix, rtype):
        parts = mid.split(".")                    # Registry.major.minor.Name -> Registry.Name (no version, 12.1.5)
        base_id = parts[0] + "." + ".".join(parts[3:]) if len(parts) >= 4 else mid
        if f.get("exclude_ids") and base_id in f["exclude_ids"]:
            return False
        if f.get("message_ids") and base_id not in f["message_ids"]:
            return False
        if f.get("prefixes") and prefix not in f["prefixes"]:
            return False
        if f.get("rtypes") and rtype not in f["rtypes"]:
            return False
        return True

    def deliver(self, dest, body):
        try:
            r = urllib.request.Request(dest, data=json.dumps(body).encode(), method="POST",
                                       headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(r, timeout=3) as resp:
                return 200 <= resp.status < 300
        except (urllib.error.URLError, OSError):
            return False

    def remove_sub(self, sid):
        sub = self.subs.pop(sid, None)
        if sub:
            self.tree.pop(sub["uri"], None)
            coll = self.tree["/redfish/v1/EventService/Subscriptions"]
            coll["Members"] = [m for m in coll["Members"] if m["@odata.id"] != sub["uri"]]
            coll["Members@odata.count"] = len(coll["Members"])

    def add_account(self, user, password, role, pcr=False):
        R = "/redfish/v1/AccountService/Accounts"
        aid = str(self.next_account); self.next_account += 1
        uri = f"{R}/{aid}"
        self.accounts[user] = dict(password=password, role=role, enabled=True, fails=0, locked_until=0, pcr=pcr, uri=uri)
        if self.static:                         # mockup mode: accounts exist for login only, not in the tree
            return uri
        self.tree[uri] = odata(uri, "#ManagerAccount.v1_13_0.ManagerAccount", Id=aid, Name="User Account",
                               UserName=user, RoleId=role, Enabled=True, Locked=False, Password=None, AccountTypes=["Redfish"],
                               PasswordChangeRequired=pcr,
                               Links={"Role": {"@odata.id": f"/redfish/v1/AccountService/Roles/{role}"}},
                               Actions={"#ManagerAccount.ChangePassword": {"target": f"{uri}/Actions/ManagerAccount.ChangePassword"}})
        coll = self.tree[R]
        coll["Members"].append({"@odata.id": uri}); coll["Members@odata.count"] = len(coll["Members"])
        return uri

    def sync_account(self, user):
        a = self.accounts[user]
        if self.static:
            return
        r = self.tree[a["uri"]]
        r.update(RoleId=a["role"], Enabled=a["enabled"], Locked=a["locked_until"] > self.now(),
                 PasswordChangeRequired=a["pcr"])
        r["Links"]["Role"] = {"@odata.id": f"/redfish/v1/AccountService/Roles/{a['role']}"}


def etag_of(res):
    return 'W/"%s"' % hashlib.sha1(json.dumps(res, sort_keys=True).encode()).hexdigest()[:12]


def error(handler, status, code, message, resolution=None):
    body = {"error": {"code": f"Base.1.17.{code}", "message": message,
                      "@Message.ExtendedInfo": [{"@odata.type": "#Message.v1_1_1.Message",
                                                 "MessageId": f"Base.1.17.{code}", "Message": message,
                                                 "Severity": "Critical",
                                                 "Resolution": resolution or "None"}]}}
    handler.send_json(status, body)


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def msg(mid, text, related=None):
    m = {"@odata.type": "#Message.v1_1_1.Message", "MessageId": f"Base.1.17.{mid}", "Message": text, "Severity": "Warning"}
    if related:
        m["RelatedProperties"] = [related]
    return m


def error_body(code, message):
    return {"error": {"code": f"Base.1.17.{code}", "message": message,
                      "@Message.ExtendedInfo": [msg(code, message)]}}


def select_props(res, select):
    """$select: whole object for 'A', only the named child for 'A/B' (DSP0266 7.3.3). Unsupported names are omitted."""
    keep = {"@odata.id", "@odata.type", "@odata.context", "@odata.etag"}
    out = {k: v for k, v in res.items() if k in keep}
    for item in select:
        top, _, rest = item.partition("/")
        if top not in res:
            continue
        if not rest:
            out[top] = res[top]
        elif isinstance(res[top], dict) and rest in res[top]:
            out.setdefault(top, {})
            if isinstance(out[top], dict):
                out[top][rest] = res[top][rest]
    return out


def expand(state, res, levels):
    if levels <= 0:
        return res
    out = copy.deepcopy(res)
    def walk(o):
        if isinstance(o, dict):
            if set(o) == {"@odata.id"} and o["@odata.id"] in state.tree:
                sub = expand(state, state.tree[o["@odata.id"]], levels - 1)
                o.clear(); o.update(copy.deepcopy(sub))
            else:
                for v in o.values():
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for k, v in out.items():
        if k not in ("@odata.id", "Actions", "Links"):
            walk(v)
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "MockRedfish/0.1"
    state = None
    quiet = True

    def handle_one_request(self):
        """Like the standard one, plus fault injection (state.faults) so fleet tools can be tested against bad BMCs:
        {'delay': seconds, 'fail_first': n -> first n requests answer 503, 'hang': True -> accept and never answer}."""
        f = getattr(self.state, "faults", None)
        if not f:
            return super().handle_one_request()
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                return
            if f.get("hang"):
                time.sleep(f.get("hang_seconds", 30)); return
            if f.get("delay"):
                time.sleep(f["delay"])
            if f.get("fail_first", 0) > 0:
                f["fail_first"] -= 1
                n = int(self.headers.get("Content-Length") or 0)
                if n:
                    self.rfile.read(n)
                self.send_json(503, error_body("ServiceTemporarilyUnavailable", "The service is temporarily unavailable. Retry later."), {"Retry-After": "1"})
                self.wfile.flush()
                return
            getattr(self, "do_" + self.command)()
            self.wfile.flush()
        except TimeoutError:
            self.close_connection = True

    def log_message(self, fmt, *args):
        if not self.quiet:
            sys.stderr.write("%s\n" % (fmt % args))

    def send_json(self, status, body=None, headers=None):
        raw = b"" if body is None else json.dumps(body, indent=2).encode()
        self.send_response(status)
        self.send_header("OData-Version", "4.0")
        self.send_header("Cache-Control", "no-cache")
        if body is not None:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)

    # ---- authentication and authorization ----------------------------------
    def identify(self):
        """Return an identity dict, None (no valid credentials) or 'LOCKED' semantics folded into None.

        Sessions come from X-Auth-Token and expire after SessionTimeout seconds of inactivity (13.3.4.3).
        HTTP Basic can be switched off (AccountService HTTPBasicAuth). Repeated bad passwords lock an account.
        """
        st = self.state
        tok = self.headers.get("X-Auth-Token")
        if tok:
            s = st.sessions.get(tok)
            if not s:
                return None
            if st.now() - s["last"] > st.session_timeout:
                self.drop_session(tok)
                return None
            s["last"] = st.now()
            a = st.accounts.get(s["user"])
            if not a or not a["enabled"]:
                return None
            return {"user": s["user"], "role": a["role"], "session": s["uri"], "pcr": a["pcr"], "acct": a["uri"]}
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Basic ") and st.basic_enabled:
            try:
                user, _, pw = base64.b64decode(auth[6:]).decode().partition(":")
            except Exception:
                return None
            if self.check_password(user, pw):
                a = st.accounts[user]
                return {"user": user, "role": a["role"], "session": None, "pcr": a["pcr"], "acct": a["uri"]}
        return None

    def check_password(self, user, pw):
        """True if user/pw are valid now. Counts failures and locks the account (same 401 either way, 13.3.2.3)."""
        st = self.state
        a = st.accounts.get(user)
        if not a or not a["enabled"]:
            return False
        if a["locked_until"] > st.now():
            return False
        if a["password"] == pw:
            a["fails"] = 0
            return True
        a["fails"] += 1
        if st.lockout_threshold and a["fails"] >= st.lockout_threshold and st.lockout_duration:
            a["locked_until"] = st.now() + st.lockout_duration
            a["fails"] = 0
        st.sync_account(user)
        return False

    def drop_session(self, tok):
        st = self.state
        with st.lock:
            s = st.sessions.pop(tok, None)
            if s:
                st.tree.pop(s["uri"], None)
                coll = st.tree["/redfish/v1/SessionService/Sessions"]
                coll["Members"] = [m for m in coll["Members"] if m["@odata.id"] != s["uri"]]
                coll["Members@odata.count"] = len(coll["Members"])

    def needs_auth(self, path):
        p = path.rstrip("/")
        # open without login per DSP0266 13.3.2.1: version object, service root, OData and metadata documents
        return p not in ("/redfish", "/redfish/v1", "/redfish/v1/odata", "/redfish/v1/$metadata")

    def required_privilege(self, method, path):
        """A small operation-to-privilege map in the spirit of DSP0266 13.4.3."""
        if method in ("GET", "HEAD"):
            return "Login"
        if path.startswith("/redfish/v1/AccountService"):
            return "ConfigureUsers"
        if path.startswith("/redfish/v1/Managers") or path.startswith("/redfish/v1/EventService") or path.startswith("/redfish/v1/CertificateService"):
            return "ConfigureManager"
        if path.startswith("/redfish/v1/SessionService/Sessions"):
            return "Login"                       # create a session; deleting someone else's is checked later
        return "ConfigureComponents"

    def gate(self, method, path):
        """Authenticate and authorize. Returns the identity, or sends the error response and returns None."""
        self.state.tick()
        who = self.identify()
        if not who:
            error(self, 401, "NoValidSession", "There is no valid session established with the implementation.",
                  "Establish a session before attempting any operations.")
            return None
        if who["pcr"] and method != "GET":
            ok = (path == who["acct"] or path.startswith(who["acct"] + "/Actions/")
                  or (method == "DELETE" and path == who["session"]))
            if not ok:
                error(self, 403, "PasswordChangeRequired", "The password provided for this account must be changed before access is granted.",
                      "Change the password with PATCH on the account or with the ChangePassword action.")
                return None
        if who["pcr"] and method == "GET" and self.needs_auth(path) and path.rstrip("/") != who["acct"]:
            error(self, 403, "PasswordChangeRequired", "The password provided for this account must be changed before access is granted.",
                  "Change the password with PATCH on the account or with the ChangePassword action.")
            return None
        need = self.required_privilege(method, path.rstrip("/"))
        own = path.rstrip("/") == who["acct"] or path.rstrip("/").startswith(who["acct"] + "/")
        if own and method in ("PATCH", "POST"):
            need = "ConfigureSelf"
        if need not in ROLE_PRIVS[who["role"]]:
            error(self, 403, "InsufficientPrivilege", "There are insufficient privileges for the account or credentials associated with the current session to perform the requested operation.")
            return None
        return who

    # ---- GET / HEAD -----------------------------------------------------
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path if u.path == "/redfish" else (u.path.rstrip("/") or "/")
        q = parse_qs(u.query, keep_blank_values=True)
        if path == "/redfish":
            return self.send_json(200, {"v1": "/redfish/v1/"})
        if path == "/redfish/v1/odata":
            return self.send_json(200, {"@odata.context": "/redfish/v1/$metadata",
                                        "value": [{"name": "Service", "kind": "Singleton", "url": "/redfish/v1/"}]})
        if path == "/redfish/v1/$metadata":
            self.send_response(200); self.send_header("Content-Type", "application/xml")
            xml = b'<?xml version="1.0"?><edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0"/>'
            self.send_header("Content-Length", str(len(xml))); self.end_headers(); self.wfile.write(xml); return
        if self.needs_auth(path):
            if not self.gate("GET", path):
                return
        else:
            self.identify()                      # touch the session so root reads keep it alive
        self.state.tick()
        m = re.match(r"^/redfish/v1/TaskService/TaskMonitors/(\d+)$", path)
        if m:
            return self.task_monitor(m.group(1))
        if path == "/redfish/v1/EventService/SSE":
            return self.sse_stream(q)
        m_att = re.match(r"^(.*/LogServices/[^/]+)/Entries/(\d+)/attachment$", path)
        if m_att:
            return self.log_attachment(m_att.group(1), m_att.group(2))
        res = self.state.tree.get(path)
        if res is None:
            return error(self, 404, "ResourceMissingAtURI", f"The resource at the URI {path} was not found.",
                         "Place a valid resource at the URI or correct the URI and resubmit the request.")
        if path.startswith("/redfish/v1/TaskService/Tasks/") and path.rsplit("/", 1)[1] in self.state.tasks:
            res = self.state.tree[path] = self.state.task_resource(path.rsplit("/", 1)[1])
        if self.command == "HEAD" and u.query:
            return error(self, 400, "QueryNotSupportedOnOperation", "Query parameters are not supported with HEAD.")
        if self.check_query(q, res, path):          # True means an error response was already sent
            return
        tag = etag_of(res)
        if self.headers.get("If-None-Match") == tag and "$select" not in q and "$expand" not in q:
            return self.send_json(304, None, {"ETag": tag})
        res = copy.deepcopy(res)
        if "$expand" in q:
            m = re.search(r"\$levels=(\d+)", q["$expand"][0])
            res = expand(self.state, res, int(m.group(1)) if m else 1)
        if isinstance(res.get("Members"), list):
            top = int(q["$top"][0]) if "$top" in q else None
            skip = int(q["$skip"][0]) if "$skip" in q else 0
            total = len(res["Members"])
            res["Members"] = res["Members"][skip:(skip + top) if top is not None else None]
            if top is not None and skip + top < total:
                res["Members@odata.nextLink"] = f"{path}?$skip={skip + top}&$top={top}"
            if "only" in q and len(res["Members"]) == 1 and total == 1:
                res = copy.deepcopy(self.state.tree[res["Members"][0]["@odata.id"]])
            elif (res.get("@odata.type") or "").startswith("#LogEntryCollection") and "$expand" not in q:
                res = expand(self.state, res, 1)           # DSP0266 9.13.11: log entries are expanded by default
        if "$select" in q:
            res = select_props(res, set(q["$select"][0].split(",")))
        hdr = {"ETag": etag_of(self.state.tree[path]), "Link": '<http://redfish.dmtf.org/schemas/v1/%s.json>; rel=describedby' % res.get("@odata.type", "#X.X").lstrip("#").split(".")[0]}
        self.send_json(200, res, hdr)

    def task_monitor(self, tid):
        """DSP0266 12.2: 202 while running, then the status and body of the original operation."""
        st = self.state
        t = st.tasks.get(tid)
        if t is None or t.get("deleted"):
            return error(self, 404, "ResourceMissingAtURI", "The task monitor was not found.")
        if not self.gate("GET", self.path):
            return
        if t["cancelled"]:
            return error(self, 410, "ResourceMissingAtURI", "The task was cancelled and is gone.")
        st.tick()
        res = st.task_resource(tid)
        if res["TaskState"] in ("Completed", "Exception"):
            return self.send_json(t["final"]["status"], t["final"]["body"], t["final"].get("headers"))
        return self.send_json(202, res, {"Location": f"/redfish/v1/TaskService/TaskMonitors/{tid}", "Retry-After": "2",
                                         "Allow": "GET, DELETE"})

    def sse_stream(self, q):
        """Server-sent events (12.5). The stream ends when the client disconnects or ?_max seconds pass."""
        st = self.state
        if not self.gate("GET", "/redfish/v1/EventService"):
            return
        flt = {}
        if "$filter" in q:
            for kind, val in re.findall(r"(MessageId|RegistryPrefix|ResourceType) eq '([^']+)'", q["$filter"][0]):
                key = {"MessageId": "message_ids", "RegistryPrefix": "prefixes", "ResourceType": "rtypes"}[kind]
                flt.setdefault(key, []).append(val)
        sub_q = queue.Queue()
        entry = (sub_q, flt)
        st.sse.append(entry)
        sid = str(st.next_sub); st.next_sub += 1
        uri = f"/redfish/v1/EventService/Subscriptions/{sid}"
        st.tree[uri] = odata(uri, "#EventDestination.v1_15_1.EventDestination", Id=sid, Name="SSE subscription",
                             SubscriptionType="SSE", Context="sse-" + secrets.token_hex(4), Protocol="Redfish")
        coll = st.tree["/redfish/v1/EventService/Subscriptions"]
        coll["Members"].append({"@odata.id": uri}); coll["Members@odata.count"] = len(coll["Members"])
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        deadline = time.time() + float(q.get("_max", ["30"])[0])
        try:
            self.wfile.write(b": stream open\n\n"); self.wfile.flush()
            while time.time() < deadline:
                try:
                    eid, evt = sub_q.get(timeout=0.2)
                except queue.Empty:
                    continue
                data = json.dumps(evt)
                self.wfile.write(f"id: {eid}\ndata: {data}\n\n".encode()); self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            if entry in st.sse:
                st.sse.remove(entry)
            st.tree.pop(uri, None)
            coll["Members"] = [m for m in coll["Members"] if m["@odata.id"] != uri]
            coll["Members@odata.count"] = len(coll["Members"])

    SUPPORTED_Q = {"$top", "$skip", "$select", "$expand", "only"}

    def check_query(self, q, res, path):
        """DSP0266 7.3.1: 501 for unsupported $ options, 400 for bad values or collection-only options on a single resource.
        Returns True when it has already sent an error response."""
        for k in q:
            if k.startswith("$") and k not in self.SUPPORTED_Q:
                error(self, 501, "QueryNotSupported", f"The query parameter {k} is not supported by this implementation.")
                return True
        is_coll = isinstance(res.get("Members"), list)
        for k in ("$top", "$skip"):
            if k in q:
                if not q[k][0].isdigit():
                    error(self, 400, "QueryParameterValueFormatError", f"The value {q[k][0]} for the parameter {k} is not valid.")
                    return True
        for k in ("$top", "$skip", "only"):
            if k in q and not is_coll:
                error(self, 400, "QueryNotSupportedOnResource", f"The query parameter {k} is not supported on this resource.")
                return True
        if "only" in q and len(q) > 1:
            error(self, 400, "QueryCombinationInvalid", "The only query parameter cannot be combined with others.")
            return True
        return False

    WRITABLE = {"AssetTag", "IndicatorLED", "Boot"}

    def do_PATCH(self):
        path = urlparse(self.path).path.rstrip("/")
        who = self.gate("PATCH", path)
        if not who:
            return
        res = self.state.tree.get(path)
        if res is None:
            return error(self, 404, "ResourceMissingAtURI", f"The resource at the URI {path} was not found.")
        accounts_path = path.startswith("/redfish/v1/AccountService/Accounts/")
        netproto = bool(re.match(r"^/redfish/v1/Managers/[^/]+/NetworkProtocol$", path))
        if re.match(r"^/redfish/v1/Systems/[^/]+/Bios/Settings$", path):
            return self.patch_bios_settings(path, res)
        if re.match(r"^/redfish/v1/Systems/[^/]+/SecureBoot$", path):
            body_ = self.read_body()
            if not isinstance(body_, dict) or set(body_) != {"SecureBootEnable"} or not isinstance(body_["SecureBootEnable"], bool):
                return error(self, 400, "PropertyNotWritable", "Only SecureBootEnable (true or false) can be changed.")
            import mock_bios
            st_ = self.state
            st_.secureboot["enable"] = body_["SecureBootEnable"]
            mock_bios.sync_secureboot(st_)
            return self.send_json(200, copy.deepcopy(st_.tree[path]), {"ETag": etag_of(st_.tree[path])})
        if not (path.startswith("/redfish/v1/Systems/") or accounts_path or path == "/redfish/v1/AccountService" or netproto):
            return self.send_json(405, error_body("ActionNotSupported", "PATCH is not supported on this resource."), {"Allow": "GET, HEAD"})
        body = self.read_body()
        if not isinstance(body, dict):
            return error(self, 400, "MalformedJSON", "The request body submitted was malformed JSON and could not be parsed by the receiving service.")
        match = self.headers.get("If-Match")
        if self.state.require_etag and match is None:
            return error(self, 428, "PreconditionRequired", "The request needs an If-Match header with the ETag from a previous GET.")
        if match is not None and match != etag_of(res):
            return error(self, 412, "PreconditionFailed", "The ETag supplied did not match the ETag required for the change.",
                         "Read the resource again and retry with the new ETag.")
        body = {k: v for k, v in body.items() if not k.startswith("@odata")}
        if not body:
            return error(self, 400, "NoOperation", "The request body submitted contained no data to act upon and no operation could be performed.")
        if netproto:
            return self.patch_netproto(path, res, body)
        if accounts_path:
            return self.patch_account(path, res, body, who)
        if path == "/redfish/v1/AccountService":
            return self.patch_account_service(res, body)
        problems, applied = [], []
        for k, v in body.items():
            if k in self.WRITABLE:
                if isinstance(v, dict) and isinstance(res.get(k), dict):
                    res[k].update(v)
                else:
                    res[k] = v
                applied.append(k)
            elif k in res:
                problems.append(msg("PropertyNotWritable", f"The property {k} is a read only property and cannot be assigned a value.", f"#/{k}"))
            else:
                problems.append(msg("PropertyUnknown", f"The property {k} is not in the list of valid properties for the resource.", f"#/{k}"))
        if not applied:
            return self.send_json(400, {"error": {"code": "Base.1.17.GeneralError", "message": "A general error has occurred. See ExtendedInfo for more information.",
                                                  "@Message.ExtendedInfo": problems}})
        out = copy.deepcopy(res)
        if problems:
            out["@Message.ExtendedInfo"] = problems
        return self.send_json(200, out, {"ETag": etag_of(res)})

    def patch_account(self, path, res, body, who):
        st = self.state
        user = res["UserName"]
        a = st.accounts[user]
        is_admin = "ConfigureUsers" in ROLE_PRIVS[who["role"]]
        problems, applied = [], []
        for k, v in body.items():
            if k == "Password":
                if len(str(v)) < st.min_password_length:
                    problems.append(msg("PropertyValueFormatError", f"The value for the property Password is not valid: minimum length is {st.min_password_length}.", "#/Password"))
                else:
                    a["password"] = str(v); a["pcr"] = False; a["fails"] = 0; a["locked_until"] = 0
                    applied.append(k)
            elif k in ("RoleId", "Enabled") and is_admin:
                if k == "RoleId" and v not in ROLE_PRIVS:
                    problems.append(msg("PropertyValueNotInList", f"The value {v} for the property RoleId is not in the list of acceptable values.", "#/RoleId"))
                    continue
                a["role" if k == "RoleId" else "enabled"] = v
                applied.append(k)
            elif k in ("RoleId", "Enabled"):
                error(self, 403, "InsufficientPrivilege", f"Changing {k} needs the ConfigureUsers privilege.")
                return
            elif k == "Locked" and is_admin and v is False:
                a["locked_until"] = 0; a["fails"] = 0; applied.append(k)
            elif k in res:
                problems.append(msg("PropertyNotWritable", f"The property {k} is a read only property and cannot be assigned a value.", f"#/{k}"))
            else:
                problems.append(msg("PropertyUnknown", f"The property {k} is not in the list of valid properties for the resource.", f"#/{k}"))
        if not applied:
            return self.send_json(400, {"error": {"code": "Base.1.17.GeneralError", "message": "A general error has occurred. See ExtendedInfo for more information.",
                                                  "@Message.ExtendedInfo": problems}})
        st.sync_account(user)
        if "Password" in applied or "Enabled" in applied and not a["enabled"]:
            for tok, s in list(st.sessions.items()):          # 13.5.2: changes may close the account's sessions
                if s["user"] == user and "Password" in applied and tok != self.headers.get("X-Auth-Token"):
                    self.drop_session(tok)
        out = copy.deepcopy(st.tree[path])
        if problems:
            out["@Message.ExtendedInfo"] = problems
        return self.send_json(200, out, {"ETag": etag_of(st.tree[path])})

    def patch_bios_settings(self, path, res):
        """DSP0266 9.10 Settings resource: changes are written to the pending object and apply at the next reset."""
        import mock_bios
        st = self.state
        body = self.read_body()
        if not isinstance(body, dict) or not isinstance(body.get("Attributes"), dict) or not body["Attributes"]:
            return error(self, 400, "NoOperation", "Send {\"Attributes\": {name: value}} with at least one attribute.")
        problems = []
        for k, v in body["Attributes"].items():
            bad = mock_bios.validate(k, v)
            if bad:
                problems.append(msg(bad[0], bad[1], f"#/Attributes/{k}"))
        if problems:
            return self.send_json(400, {"error": {"code": "Base.1.17.GeneralError", "message": "A general error has occurred. See ExtendedInfo for more information.",
                                                  "@Message.ExtendedInfo": problems}})
        st.bios["pending"].update(body["Attributes"])
        st.bios["settings_time"] = iso(st.now())
        mock_bios.sync(st)
        reset_uri = f"{st.sys_uri}/Actions/ComputerSystem.Reset"
        m = msg("ResetRequired", f"In order to apply changes, a component reset is required with the Reset action URI '{reset_uri}' and ResetType 'GracefulRestart'.")
        m["Severity"] = "OK"
        return self.send_json(200, dict(copy.deepcopy(st.tree[path]), **{"@Message.ExtendedInfo": [m]}), {"ETag": etag_of(st.tree[path])})

    def patch_netproto(self, path, res, body):
        """ManagerNetworkProtocol: each protocol is an object with ProtocolEnabled and Port (NTP also NTPServers)."""
        problems, applied = [], []
        for k, v in body.items():
            if k in res and isinstance(res[k], dict) and isinstance(v, dict):
                bad = [x for x in v if x not in res[k]]
                if bad:
                    problems.append(msg("PropertyUnknown", f"The property {k}/{bad[0]} is not in the list of valid properties for the resource.", f"#/{k}/{bad[0]}"))
                    continue
                if "ProtocolEnabled" in v and not isinstance(v["ProtocolEnabled"], bool):
                    problems.append(msg("PropertyValueFormatError", f"The value for {k}/ProtocolEnabled must be true or false.", f"#/{k}/ProtocolEnabled"))
                    continue
                if "Port" in v and not (isinstance(v["Port"], int) and 1 <= v["Port"] <= 65535):
                    problems.append(msg("PropertyValueFormatError", f"The value {v['Port']} for {k}/Port is not a valid port.", f"#/{k}/Port"))
                    continue
                res[k].update(v); applied.append(k)
            elif k in ("HostName", "FQDN") and isinstance(v, str):
                res[k] = v; applied.append(k)
            elif k in res:
                problems.append(msg("PropertyNotWritable", f"The property {k} is a read only property and cannot be assigned a value.", f"#/{k}"))
            else:
                problems.append(msg("PropertyUnknown", f"The property {k} is not in the list of valid properties for the resource.", f"#/{k}"))
        if not applied:
            return self.send_json(400, {"error": {"code": "Base.1.17.GeneralError", "message": "A general error has occurred. See ExtendedInfo for more information.",
                                                  "@Message.ExtendedInfo": problems}})
        out = copy.deepcopy(res)
        if problems:
            out["@Message.ExtendedInfo"] = problems
        return self.send_json(200, out, {"ETag": etag_of(res)})

    def patch_account_service(self, res, body):
        st = self.state
        applied = []
        for k, v in body.items():
            if k == "HTTPBasicAuth" and v in ("Enabled", "Disabled", "Unadvertised"):
                st.basic_enabled = v != "Disabled"; res[k] = v; applied.append(k)
            elif k == "AccountLockoutThreshold" and isinstance(v, int):
                st.lockout_threshold = v; res[k] = v; applied.append(k)
            elif k == "AccountLockoutDuration" and isinstance(v, int):
                st.lockout_duration = v; res[k] = v; applied.append(k)
            elif k == "MinPasswordLength" and isinstance(v, int):
                st.min_password_length = v; res[k] = v; applied.append(k)
        if not applied:
            return error(self, 400, "PropertyNotWritable", "None of the properties can be changed.")
        return self.send_json(200, copy.deepcopy(res), {"ETag": etag_of(res)})

    def do_PUT(self):
        return self.send_json(405, error_body("ActionNotSupported", "PUT is not supported in this mock."), {"Allow": "GET, HEAD, PATCH"})

    # ---- POST: sessions (more actions are added by later chapters) -------
    def read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n))
        except ValueError:
            return None

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "/redfish/v1/UpdateService/upload":
            return self.update_upload()
        body = self.read_body()
        if body is None:
            return error(self, 400, "MalformedJSON", "The request body submitted was malformed JSON and could not be parsed by the receiving service.")
        st = self.state
        if path == "/redfish/v1/SessionService/Sessions":
            return self.create_session(body)
        who = self.gate("POST", path)
        if not who:
            return
        if path == "/redfish/v1/AccountService/Accounts":
            user, pw, role = body.get("UserName"), body.get("Password"), body.get("RoleId")
            if not user or not pw or role not in ROLE_PRIVS:
                return error(self, 400, "CreateFailedMissingReqProperties", "UserName, Password and a valid RoleId are required.")
            if user in st.accounts:
                return error(self, 409, "ResourceAlreadyExists", f"The account {user} already exists.")
            if len(pw) < st.min_password_length:
                return error(self, 400, "PropertyValueFormatError", f"Password must have at least {st.min_password_length} characters.")
            uri = st.add_account(user, pw, role)
            return self.send_json(201, copy.deepcopy(st.tree[uri]), {"Location": uri, "ETag": etag_of(st.tree[uri])})
        m = re.match(r"^(/redfish/v1/AccountService/Accounts/\d+)/Actions/ManagerAccount\.ChangePassword$", path)
        if m:
            user = st.tree[m.group(1)]["UserName"] if m.group(1) in st.tree else None
            if not user:
                return error(self, 404, "ResourceMissingAtURI", "No such account.")
            new, cur = body.get("NewPassword"), body.get("SessionAccountPassword")
            if not new or not cur:
                return error(self, 400, "ActionParameterMissing", "NewPassword and SessionAccountPassword are required.")
            if st.accounts[who["user"]]["password"] != cur:
                return error(self, 401, "ResourceAtUriUnauthorized", "SessionAccountPassword is not correct.")
            if len(new) < st.min_password_length:
                return error(self, 400, "PropertyValueFormatError", f"Password must have at least {st.min_password_length} characters.")
            st.accounts[user].update(password=new, pcr=False)
            st.sync_account(user)
            return self.send_json(200, {"error": {"code": "Base.1.17.Success", "message": "Successfully Completed Request",
                                                  "@Message.ExtendedInfo": [msg("Success", "Successfully Completed Request")]}})
        m_log = re.match(r"^(/redfish/v1/(?:Managers|Systems)/[^/]+/LogServices/[^/]+)/Actions/LogService\.(ClearLog|CollectDiagnosticData)$", path)
        if m_log and m_log.group(1) in st.logs:
            return self.log_action(m_log.group(1), m_log.group(2), body)
        if path == "/redfish/v1/CertificateService/Actions/CertificateService.GenerateCSR":
            import mock_certs
            if not getattr(st, "tls_files", None):
                return error(self, 501, "ActionNotSupported", "This service runs without TLS in this lab, so it has no certificate to replace.")
            if not body.get("CertificateCollection") or not body.get("CommonName"):
                return error(self, 400, "ActionParameterMissing", "CertificateCollection and CommonName are required.")
            try:
                csr = mock_certs.generate_csr(st, body)
            except ValueError as e:
                return error(self, 400, "ActionParameterValueFormatError", f"The request could not be made: {e}")
            return self.send_json(200, {"CSRString": csr, "CertificateCollection": body["CertificateCollection"]})
        if path == "/redfish/v1/CertificateService/Actions/CertificateService.ReplaceCertificate":
            import mock_certs
            for p_ in ("CertificateString", "CertificateType", "CertificateUri"):
                if p_ not in body:
                    return error(self, 400, "ActionParameterMissing", f"The action ReplaceCertificate requires the parameter {p_}.")
            if body["CertificateType"] != "PEM":
                return error(self, 400, "PropertyValueNotInList", "Only PEM is supported.")
            if (body["CertificateUri"].get("@odata.id") if isinstance(body["CertificateUri"], dict) else None) != st.cert_uri:
                return error(self, 404, "ResourceMissingAtURI", "That certificate is not on this service.")
            try:
                mock_certs.replace(st, body["CertificateString"])
            except ValueError as e:
                return error(self, 400, "ActionParameterValueFormatError", f"The certificate was not accepted: {e}")
            return self.send_json(200, {"error": {"code": "Base.1.17.Success", "message": "Successfully Completed Request",
                                                  "@Message.ExtendedInfo": [msg("Success", "The certificate was replaced.")]}})
        if path == "/redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate":
            return self.simple_update(body)
        if path == "/redfish/v1/UpdateService/Actions/UpdateService.StartUpdate":
            n = st.start_pending()
            return self.send_json(202 if n else 200, {"error": {"code": "Base.1.17.Success", "message": f"Started {n} update(s).",
                                                             "@Message.ExtendedInfo": [msg("Success", f"Started {n} update(s).")]}})
        if re.match(r"^/redfish/v1/Systems/[^/]+/SecureBoot/Actions/SecureBoot\.ResetKeys$", path):
            import mock_bios
            kind = body.get("ResetKeysType")
            if kind not in ("ResetAllKeysToDefault", "DeleteAllKeys", "DeletePK"):
                return error(self, 400, "PropertyValueNotInList", f"The value {kind} for the property ResetKeysType is not in the list of acceptable values.")
            st.secureboot["mode"] = "UserMode" if kind == "ResetAllKeysToDefault" else "SetupMode"
            mock_bios.sync_secureboot(st)
            return self.send_json(200, {"error": {"code": "Base.1.17.Success", "message": "Successfully Completed Request",
                                                  "@Message.ExtendedInfo": [msg("Success", "Keys changed. The effect shows after the next boot.")]}})
        if re.match(r"^/redfish/v1/Systems/[^/]+/Bios/Actions/Bios\.ResetBios$", path):
            import mock_bios
            st.bios["reset_defaults"] = True
            mock_bios.sync(st)
            return self.send_json(200, {"error": {"code": "Base.1.17.Success", "message": "Successfully Completed Request",
                                                  "@Message.ExtendedInfo": [msg("Success", "Defaults will be applied at the next reset.")]}})
        m = re.match(r"^(/redfish/v1/Managers/[^/]+)/Actions/Manager\.Reset$", path)
        if m and m.group(1) in st.tree:
            import mock_update
            if body.get("ResetType") not in ("GracefulRestart", "ForceRestart"):
                return error(self, 400, "PropertyValueNotInList", f"The value {body.get('ResetType')} for the property ResetType is not in the list of acceptable values.")
            done = mock_update.activate(st, "BMC")
            return self.send_json(200, {"error": {"code": "Base.1.17.Success", "message": "Successfully Completed Request",
                                                  "@Message.ExtendedInfo": [msg("Success", "Successfully Completed Request. The BMC restarts now.")]}})
        m = re.match(r"^(/redfish/v1/Systems/[^/]+)/Actions/ComputerSystem\.Reset$", path)
        if m and m.group(1) in st.tree:
            return self.system_reset(m.group(1), body)
        if path == "/redfish/v1/EventService/Subscriptions":
            return self.create_subscription(body)
        if path == "/redfish/v1/EventService/Actions/EventService.SubmitTestEvent":
            mid = body.get("MessageId", "Base.1.17.TestEvent")
            st.emit(mid, body.get("OriginOfCondition", "/redfish/v1/EventService"), "OK", "Test event")
            return self.send_json(204)
        return self.send_json(405, error_body("ActionNotSupported", f"POST to {path} is not supported in this chapter's mock."), {"Allow": "GET, HEAD"})

    ALLOWED_RESET = ["On", "ForceOff", "GracefulShutdown", "GracefulRestart", "ForceRestart", "Nmi", "PowerCycle", "FullPowerCycle"]

    def system_reset(self, uri, body):
        """DSP0266 7.11: 400 for missing or bad parameters, 200 with a message, 202 + task monitor when slow."""
        st = self.state
        rt = body.get("ResetType")
        if rt is None:
            return error(self, 400, "ActionParameterMissing", "The action Reset requires the parameter ResetType to be present in the request body.")
        if rt not in self.ALLOWED_RESET:
            return error(self, 400, "PropertyValueNotInList",
                         f"The value {rt} for the parameter ResetType in the action Reset is not in the list of acceptable values.",
                         "Choose a value from the ResetType@Redfish.AllowableValues list.")
        res = st.tree[uri]
        before = res["PowerState"]
        def apply():
            if rt in ("GracefulRestart", "ForceRestart", "PowerCycle", "FullPowerCycle"):
                import mock_bios
                mock_bios.apply_on_reset(st)
            if rt in ("GracefulRestart", "ForceRestart", "PowerCycle"):
                import mock_update
                mock_update.activate(st, "SYSTEM")
            if rt == "FullPowerCycle":
                import mock_update
                mock_update.activate(st, "AC")
            if rt in ("ForceOff", "GracefulShutdown"):
                res["PowerState"] = "Off"
            elif rt == "On":
                res["PowerState"] = "On"
            elif rt in ("ForceRestart", "GracefulRestart", "PowerCycle", "FullPowerCycle"):
                res["PowerState"] = "On"
            if res["PowerState"] != before:
                st.emit("ResourceEvent.1.0.ResourceStatusChanged", uri, "OK", f"PowerState changed from {before} to {res['PowerState']}")
        if rt == "On" and before == "On":
            return self.send_json(200, {"error": {"code": "Base.1.17.NoOperation", "message": "The request body submitted contained no data to act upon and no operation could be performed.",
                                                  "@Message.ExtendedInfo": [msg("NoOperation", "The system is already On.")]}})
        if st.async_reset and rt in ("ForceRestart", "GracefulRestart"):
            tid = st.new_task("System reset", {"status": 200, "body": {"error": {"code": "Base.1.17.Success", "message": "Successfully Completed Request",
                                                                               "@Message.ExtendedInfo": [msg("Success", "Successfully Completed Request")]}},
                                               "apply": apply})
            return self.send_json(202, st.task_resource(tid), {"Location": f"/redfish/v1/TaskService/TaskMonitors/{tid}", "Retry-After": "2"})
        apply()
        return self.send_json(200, {"error": {"code": "Base.1.17.Success", "message": "Successfully Completed Request",
                                              "@Message.ExtendedInfo": [msg("Success", "Successfully Completed Request")]}})

    def log_attachment(self, svc, eid):
        st = self.state
        if not self.gate("GET", svc):
            return
        data = st.logs.get(svc, {}).get("attachments", {}).get(eid)
        if data is None:
            return error(self, 404, "ResourceMissingAtURI", "No attachment for that log entry.")
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def log_action(self, svc, action, body):
        import mock_logs
        st = self.state
        if action == "ClearLog":
            want = body.get("LogEntriesETag")
            if want is not None and want != etag_of(st.tree[f"{svc}/Entries"]):
                return error(self, 412, "PreconditionFailed", "The LogEntriesETag does not match: the log changed since you read it.")
            mock_logs.clear(st, svc)
            return self.send_json(204)
        if action == "CollectDiagnosticData":
            t = body.get("DiagnosticDataType")
            if t is None:
                return error(self, 400, "ActionParameterMissing", "The action CollectDiagnosticData requires the parameter DiagnosticDataType.")
            if t not in ("Manager", "OEM"):
                return error(self, 400, "PropertyValueNotInList", f"The value {t} for the property DiagnosticDataType is not in the list of acceptable values.")
            final = {"status": 200, "body": {"error": {"code": "Base.1.17.Success", "message": "Successfully Completed Request",
                                                      "@Message.ExtendedInfo": [msg("Success", "Diagnostic data collected.")]}}}
            def apply():
                e = mock_logs.make_dump(st, svc)
                if e:
                    final["headers"] = {"Location": e["@odata.id"]}      # the schema says the finished task's Location is the LogEntry
            final["apply"] = apply
            tid = st.new_task("Collect diagnostic data", final)
            return self.send_json(202, st.task_resource(tid), {"Location": f"/redfish/v1/TaskService/TaskMonitors/{tid}", "Retry-After": "2"})
        return error(self, 404, "ResourceMissingAtURI", "No such log action.")

    def simple_update(self, body):
        """DSP0266 12.6.2.1: pull an image from ImageURI. 202 + task monitor."""
        import mock_update
        st = self.state
        uri, proto = body.get("ImageURI"), body.get("TransferProtocol", "HTTP")
        if not uri:
            return error(self, 400, "ActionParameterMissing", "The action SimpleUpdate requires the parameter ImageURI to be present in the request body.")
        if proto not in ("HTTP", "HTTPS"):
            return error(self, 400, "PropertyValueNotInList", f"The value {proto} for the property TransferProtocol is not in the list of acceptable values.")
        tid = mock_update.start_update(st, uri, body.get("Targets"), bool(body.get("ForceUpdate")), uri.rsplit("/", 1)[-1],
                                       body.get("@Redfish.OperationApplyTime", "Immediate"))
        return self.send_json(202, st.task_resource(tid), {"Location": f"/redfish/v1/TaskService/TaskMonitors/{tid}", "Retry-After": "2"})

    def update_upload(self):
        """DSP0266 12.6.2.2: multipart/form-data push with an UpdateParameters part and an UpdateFile part."""
        import mock_update
        st = self.state
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        if not self.gate("POST", "/redfish/v1/UpdateService/upload"):
            return
        if n > st.max_image:
            return error(self, 413, "ResourceExhaustion", "The image is larger than MaxImageSizeBytes.")
        ct = self.headers.get("Content-Type", "")
        if not ct.startswith("multipart/form-data"):
            return error(self, 415, "UnsupportedMediaType" if False else "MalformedJSON", "The body must be multipart/form-data.")
        try:
            parts = mock_update.parse_multipart(ct, raw)
        except Exception:
            return error(self, 400, "MalformedJSON", "The multipart body could not be parsed.")
        if "UpdateParameters" not in parts or "UpdateFile" not in parts:
            return error(self, 400, "PropertyMissing", "Both the UpdateParameters part and the UpdateFile part are required.")
        try:
            params = json.loads(parts["UpdateParameters"][1] or b"{}")
        except ValueError:
            return error(self, 400, "MalformedJSON", "UpdateParameters is not valid JSON.")
        fname = parts["UpdateFile"][0].get_filename() or "upload.bin"
        tid = mock_update.start_update(st, parts["UpdateFile"][1], params.get("Targets"), bool(params.get("ForceUpdate")), fname,
                                       params.get("@Redfish.OperationApplyTime", "Immediate"))
        return self.send_json(202, st.task_resource(tid), {"Location": f"/redfish/v1/TaskService/TaskMonitors/{tid}", "Retry-After": "2"})

    def create_subscription(self, body):
        """DSP0266 12.1.2: POST to the Subscriptions collection. 201 + Location, 400 for conflicting parameters."""
        st = self.state
        dest = body.get("Destination")
        if not dest or not re.match(r"^https?://", dest):
            return error(self, 400, "PropertyMissing", "The Destination property is required and must be an http or https URI.")
        if body.get("Protocol", "Redfish") != "Redfish":
            return error(self, 400, "PropertyValueNotInList", "Only the Redfish protocol is supported.")
        if body.get("EventFormatType", "Event") != "Event":
            return error(self, 400, "PropertyValueNotInList", "Only the Event format is supported.")
        sid = str(st.next_sub); st.next_sub += 1
        uri = f"/redfish/v1/EventService/Subscriptions/{sid}"
        policy = body.get("DeliveryRetryPolicy", "TerminateAfterRetries")
        st.subs[sid] = {"uri": uri, "dest": dest, "context": body.get("Context", ""), "policy": policy, "failures": 0,
                        "message_ids": body.get("MessageIds", []), "prefixes": body.get("RegistryPrefixes", []),
                        "rtypes": body.get("ResourceTypes", []), "exclude_ids": body.get("ExcludeMessageIds", [])}
        res = odata(uri, "#EventDestination.v1_15_1.EventDestination", Id=sid, Name="Event Subscription",
                    Destination=dest, SubscriptionType="RedfishEvent", Protocol="Redfish", EventFormatType="Event",
                    Context=body.get("Context", ""), DeliveryRetryPolicy=policy, RegistryPrefixes=body.get("RegistryPrefixes", []),
                    MessageIds=body.get("MessageIds", []), ResourceTypes=body.get("ResourceTypes", []))
        st.tree[uri] = res
        coll = st.tree["/redfish/v1/EventService/Subscriptions"]
        coll["Members"].append({"@odata.id": uri}); coll["Members@odata.count"] = len(coll["Members"])
        return self.send_json(201, copy.deepcopy(res), {"Location": uri})

    def create_session(self, body):
        st = self.state
        user, pw = body.get("UserName"), body.get("Password")
        if self.check_password(user, pw):
            a = st.accounts[user]
            with st.lock:
                sid = str(st.next_session); st.next_session += 1
                token = secrets.token_hex(16)
                uri = f"/redfish/v1/SessionService/Sessions/{sid}"
                st.sessions[token] = {"user": user, "role": a["role"], "uri": uri, "last": st.now()}
                sess = odata(uri, "#Session.v1_7_0.Session", Id=sid, Name="User Session", UserName=user, Password=None)
                st.tree[uri] = sess
                coll = st.tree["/redfish/v1/SessionService/Sessions"]
                coll["Members"].append({"@odata.id": uri}); coll["Members@odata.count"] = len(coll["Members"])
            out = copy.deepcopy(sess)
            if a["pcr"]:
                out["@Message.ExtendedInfo"] = [msg("PasswordChangeRequired", "The password provided for this account must be changed before access is granted.")]
            return self.send_json(201, out, {"X-Auth-Token": token, "Location": uri})
        return error(self, 401, "ResourceAtUriUnauthorized", "While accessing the resource, the service received an authorization error.",
                     "Verify that the provided credentials are correct.")

    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip("/")
        st = self.state
        who = self.gate("DELETE", path)
        if not who:
            return
        for tok, s in list(st.sessions.items()):
            if s["uri"] == path:
                if s["user"] != who["user"] and "ConfigureManager" not in ROLE_PRIVS[who["role"]]:
                    return error(self, 403, "InsufficientPrivilege", "Only an administrator may end another user's session.")
                self.drop_session(tok)
                return self.send_json(204)
        m = re.match(r"^/redfish/v1/EventService/Subscriptions/(\d+)$", path)
        if m and m.group(1) in st.subs:
            st.remove_sub(m.group(1))
            return self.send_json(204)
        m = re.match(r"^/redfish/v1/TaskService/(?:Tasks|TaskMonitors)/(\d+)$", path)
        if m and m.group(1) in st.tasks:
            t = st.tasks[m.group(1)]
            if st.task_resource(m.group(1))["TaskState"] == "Completed":
                return error(self, 409, "ResourceInUse", "The task has already completed and cannot be cancelled.")
            t["cancelled"] = True
            if t.get("fw"):
                import mock_update
                for k in t["fw"]:
                    st.fw[k]["state"] = "Enabled"
                    mock_update.sync_fw(st, k)
            return self.send_json(204)
        m = re.match(r"^/redfish/v1/AccountService/Accounts/\d+$", path)
        if m and path in st.tree:
            user = st.tree[path]["UserName"]
            if user == who["user"]:
                return error(self, 409, "ResourceInUse", "You cannot delete the account you are logged in with.")
            del st.accounts[user]
            st.tree.pop(path)
            coll = st.tree["/redfish/v1/AccountService/Accounts"]
            coll["Members"] = [x for x in coll["Members"] if x["@odata.id"] != path]
            coll["Members@odata.count"] = len(coll["Members"])
            for tok, s in list(st.sessions.items()):
                if s["user"] == user:
                    self.drop_session(tok)
            return self.send_json(204)
        return error(self, 404, "ResourceMissingAtURI", f"The resource at the URI {path} was not found.")


def make_server(profile="dgx", port=0, mockup=None, tls=None):
    """tls=(certfile, keyfile) serves HTTPS with TLS 1.2 or newer (DSP0266 13.1); otherwise plain HTTP for labs."""
    st = State(profile, mockup)
    H = type("H", (Handler,), {"state": st})
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    if tls:
        import ssl
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(*tls)
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        st.tls_ctx = ctx
        st.tls_files = tuple(tls)
        import mock_certs
        mock_certs.refresh(st)
    return srv, st


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["dgx", "generic"], default="dgx")
    ap.add_argument("--port", type=int, default=8443)
    ap.add_argument("--mockup", help="serve a DMTF mockup folder (read-only), e.g. .../mockups/public-rackmount1")
    ap.add_argument("--tls", nargs=2, metavar=("CERT", "KEY"), help="serve HTTPS with this certificate and key")
    ap.add_argument("--require-etag", action="store_true", help="answer PATCH without If-Match with 428")
    a = ap.parse_args()
    srv, st = make_server(a.profile, a.port, a.mockup, tuple(a.tls) if a.tls else None)
    st.require_etag = a.require_etag
    Handler.quiet = False
    print(f"mock Redfish ({a.profile}) on {'https' if a.tls else 'http'}://127.0.0.1:{a.port}/redfish/v1/  ({'TLS 1.2+' if a.tls else 'plain HTTP: lab only'})")
    srv.serve_forever()
