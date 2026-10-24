"""BIOS settings for redfish_mock.py (chapter 7.14): the Bios resource, a pending Settings object, an attribute
registry, and one-time boot override. Attribute NAMES are invented for this lab: real platforms publish their own
attribute registry and the names differ (that is the whole point of the registry)."""
R = "/redfish/v1"
REG_ID = "BiosAttributeRegistryLab.v1_0_0"

# name, type, default (factory, energy-saving), allowed values or (min, max), display name
ATTRS = [
    ("PowerProfile", "Enumeration", "Balanced", ["Balanced", "MaxPerf", "EnergySaver"], "System power profile"),
    ("ProcCStates", "Enumeration", "Enabled", ["Enabled", "Disabled"], "Processor C-states"),
    ("ProcHyperthreading", "Enumeration", "Enabled", ["Enabled", "Disabled"], "Hyper-threading or SMT"),
    ("SubNumaClustering", "Enumeration", "Disabled", ["Enabled", "Disabled"], "Sub-NUMA clustering"),
    ("PcieRelaxedOrdering", "Enumeration", "Disabled", ["Enabled", "Disabled"], "PCIe relaxed ordering"),
    ("PcieMaxPayloadSize", "Enumeration", "256B", ["128B", "256B", "512B"], "PCIe maximum payload size"),
    ("PcieLinkSpeed", "Enumeration", "Auto", ["Auto", "Gen3", "Gen4", "Gen5"], "PCIe link speed"),
    ("BootMode", "Enumeration", "Uefi", ["Uefi", "Legacy"], "Boot mode"),
    ("IommuMode", "Enumeration", "Enabled", ["Enabled", "Disabled"], "IOMMU"),
    ("ProcCoreDisable", "Integer", 0, (0, 64), "Disabled cores per socket"),
    ("AdminPhone", "String", "", None, "Administrator phone number"),
]
READONLY = {"BiosVersionString": "1.20"}


def install_state(st):
    sysu = st.sys_uri
    reg_uri = f"{R}/Registries/{REG_ID}"
    attrs = {a[0]: a[2] for a in ATTRS}
    attrs.update(READONLY)
    st.bios = {"attrs": attrs, "pending": {}, "reset_defaults": False, "settings_time": None, "boot_log": []}
    st.tree[sysu]["Bios"] = {"@odata.id": f"{sysu}/Bios"}
    st.tree[sysu]["Boot"] = {"BootSourceOverrideEnabled": "Disabled", "BootSourceOverrideTarget": "None",
                             "BootSourceOverrideTarget@Redfish.AllowableValues": ["None", "Pxe", "Hdd", "UefiHttp", "BiosSetup", "Diags"],
                             "BootSourceOverrideMode": "UEFI"}
    st.tree[f"{R}/Registries"] = {"@odata.id": f"{R}/Registries", "@odata.type": "#MessageRegistryFileCollection.MessageRegistryFileCollection",
                                  "Name": "Registry File Collection", "Members": [{"@odata.id": reg_uri}], "Members@odata.count": 1}
    st.tree[reg_uri] = {"@odata.id": reg_uri, "@odata.type": "#MessageRegistryFile.v1_1_5.MessageRegistryFile", "Id": REG_ID,
                        "Name": "Lab BIOS attribute registry file", "Languages": ["en"], "Registry": REG_ID,
                        "Location": [{"Language": "en", "Uri": f"{R}/Registries/{REG_ID}/Registry"}]}
    entries = []
    for i, (name, typ, default, allowed, disp) in enumerate(ATTRS):
        e = {"AttributeName": name, "DisplayName": disp, "DisplayOrder": i + 1, "Type": typ, "DefaultValue": default,
             "CurrentValue": None, "ReadOnly": False, "Hidden": False, "MenuPath": "./Lab", "ResetRequired": True}
        if typ == "Enumeration":
            e["Value"] = [{"ValueName": v, "ValueDisplayName": v} for v in allowed]
        elif typ == "Integer":
            e["LowerBound"], e["UpperBound"] = allowed
        elif typ == "String":
            e["MinLength"], e["MaxLength"] = 0, 32
        entries.append(e)
    entries.append({"AttributeName": "BiosVersionString", "DisplayName": "BIOS version", "Type": "String", "ReadOnly": True,
                    "Hidden": False, "DefaultValue": None, "CurrentValue": None, "MenuPath": "./Lab"})
    st.tree[f"{R}/Registries/{REG_ID}/Registry"] = {
        "@odata.id": f"{R}/Registries/{REG_ID}/Registry", "@odata.type": "#AttributeRegistry.v1_5_1.AttributeRegistry", "Id": REG_ID,
        "Name": "Lab BIOS Attribute Registry", "Language": "en", "RegistryVersion": "1.0.0", "OwningEntity": "Handbook lab",
        "RegistryEntries": {"Attributes": entries}}
    # UEFI Secure Boot of the host (the key databases belong to the HOST firmware, not to the BMC)
    sb = f"{sysu}/SecureBoot"
    st.tree[sysu]["SecureBoot"] = {"@odata.id": sb}
    st.secureboot = {"enable": False, "current": "Disabled", "mode": "SetupMode"}
    st.tree[f"{sb}/SecureBootDatabases"] = {"@odata.id": f"{sb}/SecureBootDatabases", "@odata.type": "#SecureBootDatabaseCollection.SecureBootDatabaseCollection",
                                          "Name": "UEFI Secure Boot Databases", "Members": [{"@odata.id": f"{sb}/SecureBootDatabases/{n}"} for n in ("PK", "KEK", "db", "dbx")],
                                          "Members@odata.count": 4}
    for n in ("PK", "KEK", "db", "dbx"):
        u = f"{sb}/SecureBootDatabases/{n}"
        st.tree[u] = {"@odata.id": u, "@odata.type": "#SecureBootDatabase.v1_0_3.SecureBootDatabase", "Id": n, "Name": f"{n} database", "DatabaseId": n,
                      "Certificates": {"@odata.id": f"{u}/Certificates"}}
        st.tree[f"{u}/Certificates"] = {"@odata.id": f"{u}/Certificates", "@odata.type": "#CertificateCollection.CertificateCollection",
                                        "Name": f"{n} certificates", "Members": [], "Members@odata.count": 0}
    sync_secureboot(st)
    sync(st)


def sync_secureboot(st):
    sb = f"{st.sys_uri}/SecureBoot"
    b = st.secureboot
    st.tree[sb] = {"@odata.id": sb, "@odata.type": "#SecureBoot.v1_2_1.SecureBoot", "Id": "SecureBoot", "Name": "UEFI Secure Boot",
                   "SecureBootEnable": b["enable"], "SecureBootCurrentBoot": b["current"], "SecureBootMode": b["mode"],
                   "SecureBootDatabases": {"@odata.id": f"{sb}/SecureBootDatabases"},
                   "Actions": {"#SecureBoot.ResetKeys": {"target": f"{sb}/Actions/SecureBoot.ResetKeys",
                                                         "ResetKeysType@Redfish.AllowableValues": ["ResetAllKeysToDefault", "DeleteAllKeys", "DeletePK"]}}}


def validate(attr_name, value):
    """Return None when OK, else (message id, text)."""
    for name, typ, default, allowed, disp in ATTRS:
        if name == attr_name:
            if typ == "Enumeration":
                if value not in allowed:
                    return ("PropertyValueNotInList", f"The value {value} for the property {name} is not in the list of acceptable values.")
            elif typ == "Integer":
                if not isinstance(value, int) or isinstance(value, bool):
                    return ("PropertyValueTypeError", f"The value for {name} must be an integer.")
                if not allowed[0] <= value <= allowed[1]:
                    return ("PropertyValueNotInList", f"The value {value} for {name} is outside {allowed[0]} to {allowed[1]}.")
            elif typ == "String" and (not isinstance(value, str) or len(value) > 32):
                return ("PropertyValueFormatError", f"The value for {name} must be a string of at most 32 characters.")
            return None
    if attr_name in READONLY:
        return ("PropertyNotWritable", f"The property {attr_name} is a read-only property and cannot be assigned a value.")
    return ("PropertyUnknown", f"The property {attr_name} is not in the list of valid properties for the resource.")


def sync(st):
    sysu, b = st.sys_uri, st.bios
    bios = f"{sysu}/Bios"
    st.tree[bios] = {
        "@odata.id": bios, "@odata.type": "#Bios.v1_2_3.Bios", "Id": "Bios", "Name": "BIOS current settings",
        "AttributeRegistry": REG_ID, "Attributes": dict(b["attrs"]), "ResetBiosToDefaultsPending": b["reset_defaults"],
        "@Redfish.Settings": {"@odata.type": "#Settings.v1_3_5.Settings", "SettingsObject": {"@odata.id": f"{bios}/Settings"},
                              "SupportedApplyTimes": ["OnReset"]},
        "Actions": {"#Bios.ResetBios": {"target": f"{bios}/Actions/Bios.ResetBios"}}}
    if b["settings_time"]:
        st.tree[bios]["@Redfish.Settings"]["Time"] = b["settings_time"]
    st.tree[f"{bios}/Settings"] = {"@odata.id": f"{bios}/Settings", "@odata.type": "#Bios.v1_2_3.Bios", "Id": "Settings",
                                   "Name": "BIOS pending settings", "AttributeRegistry": REG_ID, "Attributes": dict(b["pending"])}


def apply_on_reset(st):
    """The host restarts: pending BIOS settings become live, then the one-time boot override is consumed."""
    b = st.bios
    if b["reset_defaults"]:
        b["attrs"].update({a[0]: a[2] for a in ATTRS})
        b["reset_defaults"] = False
    b["attrs"].update(b["pending"])
    b["pending"] = {}
    sb = st.secureboot                       # Secure Boot takes effect at the next boot, like BIOS settings
    sb["current"] = "Enabled" if sb["enable"] and sb["mode"] in ("UserMode", "DeployedMode") else "Disabled"   # enforced only with a PK enrolled
    sync_secureboot(st)
    boot = st.tree[st.sys_uri]["Boot"]
    target = boot.get("BootSourceOverrideTarget")
    if boot.get("BootSourceOverrideEnabled") in ("Once", "Continuous") and target not in (None, "None"):
        b["boot_log"].append(target)
        if boot["BootSourceOverrideEnabled"] == "Once":
            boot["BootSourceOverrideEnabled"] = "Disabled"
            boot["BootSourceOverrideTarget"] = "None"
    else:
        b["boot_log"].append("Hdd")
    sync(st)
