#!/usr/bin/env python3
"""Audit and (carefully) fix BMC security settings through Redfish.

  rf_harden.py audit http://host:port user pw --policy profiles/bmc_policy.json
  rf_harden.py apply http://host:port user pw --policy profiles/bmc_policy.json [--yes]

audit  prints findings: FIX (this tool can change it), MANUAL (needs a person: accounts, certificates, Secure Boot)
apply  sends the FIX items only. Dry run unless --yes. It refuses to switch off the protocol it is using for its own
       connection (you would lock yourself out), and it re-reads and checks every change.
Checks: management protocols (HTTP, Telnet, IPMI, SSDP on?), NTP, HTTP Basic, password and lockout policy, session
timeout, accounts (default names, forced password change, too many administrators), the HTTPS certificate (self-signed,
near expiry) and UEFI Secure Boot. Teaching tool: it knows the standard Redfish names only.
"""
import json, sys, time, calendar
from redfish_crawl import Client
from rf_inventory import get, collection


def parse_iso(s):
    try:
        return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))
    except (TypeError, ValueError):
        return None


def audit(c, policy, now=time.time, using_scheme="https"):
    root = get(c, "/redfish/v1/")
    F = []                                                   # (severity, kind, text, fix)
    add = lambda sev, kind, text, fix=None: F.append((sev, kind, text, fix))
    # protocols
    for m in collection(c, root["Managers"]["@odata.id"]):
        np = get(c, m["NetworkProtocol"]["@odata.id"]) if "NetworkProtocol" in m else None
        if not np:
            add("HIGH", "MANUAL", f"{m['Id']}: no NetworkProtocol resource: cannot check which services are on")
            continue
        for name in policy["protocols_off"]:
            p = np.get(name)
            if p and p.get("ProtocolEnabled"):
                add("HIGH" if name in ("Telnet", "IPMI", "HTTP") else "MEDIUM", "FIX", f"{name} is enabled (policy: off)",
                    ("PATCH", np["@odata.id"], {name: {"ProtocolEnabled": False}}, name))
        for name in policy["protocols_on"]:
            p = np.get(name)
            if not (p and p.get("ProtocolEnabled")):
                add("HIGH", "MANUAL", f"{name} is not enabled (policy: on)")
        ntp = np.get("NTP") or {}
        if not ntp.get("ProtocolEnabled") or not ntp.get("NTPServers"):
            add("MEDIUM", "FIX", "NTP is off or has no servers: log timestamps will drift (chapter 7.11)",
                ("PATCH", np["@odata.id"], {"NTP": {"ProtocolEnabled": True, "NTPServers": policy["ntp_servers"]}}, "NTP"))
        cert_coll = (np.get("HTTPS") or {}).get("Certificates", {}).get("@odata.id")
        if cert_coll:
            for cert in collection(c, cert_coll):
                issuer, subject = (cert.get("Issuer") or {}).get("CommonName"), (cert.get("Subject") or {}).get("CommonName")
                if issuer and issuer == subject:
                    add("HIGH", "MANUAL", f"HTTPS certificate is self-signed ({subject}): install one signed by your CA (GenerateCSR then ReplaceCertificate)")
                end = parse_iso(cert.get("ValidNotAfter"))
                if end and (end - now()) / 86400 < policy["min_cert_days_left"]:
                    add("HIGH", "MANUAL", f"HTTPS certificate expires in {int((end - now()) / 86400)} days")
    # account service
    acs = get(c, root["AccountService"]["@odata.id"])
    fix = {}
    if acs.get("HTTPBasicAuth") not in (policy["basic_auth"], None):
        fix["HTTPBasicAuth"] = policy["basic_auth"]
        add("MEDIUM", "FIX", f"HTTP Basic authentication is {acs.get('HTTPBasicAuth')} (policy: {policy['basic_auth']})", ("PATCH", acs["@odata.id"], {"HTTPBasicAuth": policy["basic_auth"]}, "HTTPBasicAuth"))
    if (acs.get("MinPasswordLength") or 0) < policy["min_password_length"]:
        add("MEDIUM", "FIX", f"MinPasswordLength is {acs.get('MinPasswordLength')} (policy: {policy['min_password_length']})", ("PATCH", acs["@odata.id"], {"MinPasswordLength": policy["min_password_length"]}, "MinPasswordLength"))
    if not acs.get("AccountLockoutThreshold"):
        add("MEDIUM", "FIX", "no account lockout (AccountLockoutThreshold is 0 or missing)", ("PATCH", acs["@odata.id"], {"AccountLockoutThreshold": policy["lockout_threshold"]}, "AccountLockoutThreshold"))
    ss = get(c, root["SessionService"]["@odata.id"])
    if (ss.get("SessionTimeout") or 0) > policy["max_session_timeout"]:
        add("LOW", "MANUAL", f"SessionTimeout is {ss.get('SessionTimeout')} s (policy: at most {policy['max_session_timeout']})")
    # accounts
    accts = collection(c, acs["Accounts"]["@odata.id"]) if "Accounts" in acs else []
    admins = [a for a in accts if a.get("RoleId") == "Administrator" and a.get("Enabled", True)]
    for a in accts:
        if a.get("PasswordChangeRequired"):
            add("HIGH", "MANUAL", f"account '{a['UserName']}' still has PasswordChangeRequired: a factory or reset password is in use")
        if a["UserName"] in policy["default_usernames"] and a.get("Enabled", True) and a.get("RoleId") == "Administrator" and a["UserName"] not in ("admin",):
            add("MEDIUM", "MANUAL", f"account '{a['UserName']}' is a default-style administrator name: rename or disable it")
    if len(admins) > policy["max_administrators"]:
        add("LOW", "MANUAL", f"{len(admins)} enabled administrator accounts (policy: at most {policy['max_administrators']}): use per-purpose roles (chapter 7.4)")
    # secure boot
    for s in collection(c, root["Systems"]["@odata.id"]):
        if "SecureBoot" in s:
            sb = get(c, s["SecureBoot"]["@odata.id"])
            if sb and sb.get("SecureBootCurrentBoot") != "Enabled":
                add("MEDIUM", "MANUAL", f"{s['Id']}: UEFI Secure Boot is not active (enable: {sb.get('SecureBootEnable')}, mode: {sb.get('SecureBootMode')})")
    return F


def apply_fixes(c, findings, using_scheme, yes, out=print):
    done, refused = 0, 0
    for sev, kind, text, fix in findings:
        if kind != "FIX":
            continue
        method, uri, body, tag = fix
        if tag.upper() == using_scheme.upper() or (tag == "HTTP" and using_scheme == "http"):
            out(f"REFUSED  {text}: this tool is connected over {using_scheme.upper()}; switching it off would lock you out"); refused += 1; continue
        if not yes:
            out(f"DRY RUN  {method} {uri} {json.dumps(body)}"); continue
        st, _, r = c.req(method, uri, body)
        out(f"{'OK' if st == 200 else 'FAILED':8} {method} {uri} {json.dumps(body)} -> HTTP {st}")
        done += st == 200
    return done, refused


def main(argv):
    cmd, base, user, pw = argv[1:5]
    a = argv[5:]
    policy = json.load(open(a[a.index("--policy") + 1]))
    c = Client(base, user, pw)
    scheme = base.split(":")[0]
    try:
        F = audit(c, policy)
        for sev, kind, text, _ in sorted(F, key=lambda f: ("HIGH", "MEDIUM", "LOW").index(f[0])):
            print(f"{sev:6} {kind:6} {text}")
        print(f"\n{sum(1 for f in F if f[1] == 'FIX')} fixable by this tool, {sum(1 for f in F if f[1] == 'MANUAL')} need a person")
        if cmd == "apply":
            done, refused = apply_fixes(c, F, scheme, "--yes" in a)
            if "--yes" in a:
                left = [f for f in audit(c, policy) if f[1] == "FIX"]
                print(f"after the changes: {len(left)} fixable finding(s) left")
        return 1 if any(f[0] == "HIGH" for f in F) else 0
    finally:
        c.logout()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
