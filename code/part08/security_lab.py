#!/usr/bin/env python3
"""Self-checking lab for chapter 8.6: user, profile, certificate and password rules from the BCM 11 manual, tested in bcm_security.py."""
import datetime as dt, sys
import bcm_security as s

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except s.SecError:
        return True

def main():
    u = s.commit_user("maureen")
    check("a new user gets ID 1000 and the manual's defaults", u["id"] == 1000 and u["loginshell"] == "/bin/bash" and u["homedirectory"] == "/home/maureen" and u["shadowmax"] == 999999 and u["shadowwarning"] == 7 and u["expirationdate"] == "2038/1/1")
    check("with no password set, login is not allowed", not u["can_login"])
    check("after a password is set, login is allowed", s.commit_user("maureen", password="x")["can_login"])
    check("IDs start at 500 on SLES", s.commit_user("a", distro="sles")["id"] == 500)
    check("the next free ID is used", s.commit_user("b", existing_ids=[1000, 1001])["id"] == 1002)
    check("cmsupport can never log in and cannot be removed", not s.commit_user("cmsupport", password="x")["can_login"] and raises(lambda: s.remove_user("cmsupport")))
    check("remove -d also removes the home directory", s.remove_user("maureen", data=True)["home_removed"] and not s.remove_user("maureen")["home_removed"])
    check("password strings starting with {SSHA}, {MD5}, {CRYPT} are taken as hashes", all(s.password_is_hash(h) for h in ("{SSHA}abc", "{MD5}abc", "{CRYPT}abc")) and not s.password_is_hash("seteca5tr0n0my"))

    m = s.group_members([], "append", ["maureen", "tim", "fred"])
    check("append adds members to a group", m == ["maureen", "tim", "fred"])
    check("removefrom removes only the named members", s.group_members(m, "removefrom", ["tim", "fred"]) == ["maureen"])
    check("clear members empties the group", s.group_members(m, "clear", []) == [])

    p = s.readonly_profile()
    check("readonly may read the burn log by default", p.allows("GET_BURN_LOG_TOKEN") and p.allows("BURN_STATUS_TOKEN"))
    p.remove_tokens("BURN_STATUS_TOKEN", "GET_BURN_LOG_TOKEN")
    check("removing the two burn tokens stops readonly users seeing burn results (the manual's example)", not p.allows("BURN_STATUS_TOKEN") and p.allows("GET_DEVICE_TOKEN"))
    check("readonly has no power-on token", not p.allows("POWER_ON_TOKEN"))
    check("admin profile allows everything", s.Profile("admin", all_tokens=True).allows("ANY_TOKEN"))
    check("nonuser profiles must not be modified", raises(lambda: s.Profile("cmhealth", {"X"}).remove_tokens("X")))
    check("only admin, readonly and portal are the user-assignable preconfigured profiles", s.USER_PROFILES == {"admin", "readonly", "portal"})
    user = {"name": "conner"}
    check("a readonly profile can be assigned to a user", s.assign_profile(user, "readonly")["profile"] == "readonly")
    check("a nonuser profile (power) cannot be assigned to a user", raises(lambda: s.assign_profile(user, "power")))
    check("eleven profiles are nonuser (the manual's table)", len(s.NONUSER) == 11)

    now = dt.datetime(2025, 6, 1)
    c = s.Certificate("democert", "readonly", "peter", 30, now)
    check("a 30-day certificate is valid on day 29 and expired on day 31", c.valid(now + dt.timedelta(days=29)) and not c.valid(now + dt.timedelta(days=31)))
    check("the expiry of a certificate cannot be extended", raises(lambda: c.extend(30)))
    c.revoked = True
    check("a revoked certificate is not valid", not c.valid(now))
    args = ("2048", "democert", "a", "b", "c", "d", "ef", "readonly", "peter", "30", "/home/peter/peterfile.key", "/home/peter/peterfile.pem")
    check("createcertificate with the manual's arguments is accepted", s.createcertificate_args(*args, known_profiles={"readonly", "admin"})["days"] == 30)
    check("createcertificate with an unknown profile is refused", raises(lambda: s.createcertificate_args(*args[:7], "nothere", *args[8:], known_profiles={"readonly"})))
    check("createcertificate with a small key is refused (my choice: under 2048)", raises(lambda: s.createcertificate_args("1024", *args[1:], known_profiles={"readonly"})))
    certs = [s.Certificate("a", "readonly", "peter", 30, now), s.Certificate("b", "admin", "root", 3000, now), s.Certificate("c", "power", "slurm", 3000, now)]
    check("a replaced administrator certificate means certificates it signed must be regenerated", len(s.certs_needing_regeneration(certs, admin_cert_replaced=True)) == 2)
    check("a replaced license means regular user certificates must be regenerated", len(s.certs_needing_regeneration(certs, license_replaced=True)) == 3)
    check("nothing replaced: nothing to regenerate", s.certs_needing_regeneration(certs) == [])
    check("cmsh -i/-k win", s.cmsh_key_lookup("p.pem", "p.key", [".cm/admin.pem", ".cm/admin.key"]) == ("p.pem", "p.key"))
    check("otherwise ~/.cm/admin.* before ~/.cm/cert.*", s.cmsh_key_lookup(home_files=[".cm/cert.pem", ".cm/cert.key", ".cm/admin.pem", ".cm/admin.key"]) == (".cm/admin.pem", ".cm/admin.key"))
    check("only cert.* present: those are used", s.cmsh_key_lookup(home_files=[".cm/cert.pem", ".cm/cert.key"]) == (".cm/cert.pem", ".cm/cert.key"))
    check("no keys: None", s.cmsh_key_lookup(home_files=[]) is None)

    plan = s.password_change_plan(["head", "image", "node-installer", "mysql"], ha=True)
    check("cm-change-passwd changes four passwords", len([x for x in plan if x.startswith("change")]) == 4)
    check("in HA the other head node needs a rerun", any("other head node" in x for x in plan))
    check("an image password needs imageupdate or reboot to reach a running node", any("imageupdate" in x for x in plan))
    check("the LDAP root password is not part of cm-change-passwd", raises(lambda: s.password_change_plan(["ldap"])))
    check("ssh: head to node is passwordless for root", s.ssh_allowed_without_password("head", "node", "root"))
    check("ssh: root from a node to the head asks for a password", not s.ssh_allowed_without_password("node", "head", "root"))
    check("ssh: ordinary users work both ways when /home is mounted", s.ssh_allowed_without_password("node", "head", "alice") and not s.ssh_allowed_without_password("node", "head", "alice", home_mounted=False))

    check("RHEL 8 LDAP clients use nslcd.conf and nslcd", s.ldap_client_files("rhel8") == (["/etc/nslcd.conf", "/etc/openldap/ldap.conf"], "nslcd"))
    check("RHEL 9 LDAP clients use sssd.conf and sssd", s.ldap_client_files("rocky9")[1] == "sssd" and "/etc/sssd/sssd.conf" in s.ldap_client_files("rocky9")[0])
    check("syncrepl interval 01:00:00:00 is one day", s.syncrepl_interval_seconds("01:00:00:00") == 86400)
    check("a malformed syncrepl interval is refused", raises(lambda: s.syncrepl_interval_seconds("1d")))
    ok = s.keycloak_prereq_problems("11.34.0", "ubuntu24.04", [9443, 9999], True, False)
    check("Keycloak prerequisites met: no problems", ok == [])
    bad = s.keycloak_prereq_problems("11.30.0", "rocky9", [9443], False, False)
    check("Keycloak: old BCM, Rocky, a busy port and no download route are all flagged", len(bad) == 4, bad)
    check("a pre-staged Keycloak archive replaces GitHub access", s.keycloak_prereq_problems("11.34.0", "ubuntu24.04", [9443, 9999], False, True) == [])
    check("auditing off is flagged", any("off" in x for x in s.audit_settings({})))
    check("auditing on without a file is flagged", any("no CMDaemonAuditorFile" in x for x in s.audit_settings({"CMDaemonAudit": "yes"})))
    check("auditing on with a file and no profile exclusion is clean", s.audit_settings({"CMDaemonAudit": "yes", "CMDaemonAuditorFile": "/var/log/cmd-audit"}) == [])
    check("excluding a profile from auditing is reported", any("disabled for profiles" in x for x in s.audit_settings({"CMDaemonAudit": "yes", "CMDaemonAuditorFile": "/x", "DisableAuditorForProfiles": "admin"})))

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
