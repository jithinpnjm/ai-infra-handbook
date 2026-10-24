#!/usr/bin/env python3
"""Users, authentication and certificate rules from BCM 11 Administrator Manual sections 2.3 and chapter 6, as small testable pieces.

Not BCM. Each part names the manual section it follows. Where the manual is silent the code says so.
"""
import datetime as dt, re

class SecError(ValueError):
    pass

# ---- 6.1-6.2 users --------------------------------------------------------------------------------------------
def commit_user(name, distro="rhel", existing_ids=(), password=None, props=None):
    """What a committed user looks like. Empty fields are filled with defaults; an unset password means no login is allowed.
    IDs start at 1000 (500 on SLES), per AdvancedConfig LowUserId. Defaults from the manual's `show` output: shell /bin/bash,
    home /home/<name>, shadowmin 0, shadowmax 999999, shadowwarning 7, shadowinactive 0, expiration 2038/1/1."""
    props = dict(props or {})
    start = 500 if distro.lower() in ("sles", "suse") else 1000
    uid = props.get("id") or next(i for i in range(start, 10**6) if i not in set(existing_ids))
    u = {"name": name, "id": uid, "groupid": props.get("groupid", uid), "loginshell": props.get("loginshell", "/bin/bash"),
         "homedirectory": props.get("homedirectory", f"/home/{name}"), "shadowmin": 0, "shadowmax": 999999, "shadowwarning": 7,
         "shadowinactive": 0, "expirationdate": props.get("expirationdate", "2038/1/1"), "profile": props.get("profile", "")}
    u["password_set"] = bool(password)
    u["can_login"] = bool(password) and name != "cmsupport"
    return u

def password_is_hash(pw):
    """6.2.3: a string starting with {MD5}, {CRYPT} or {SSHA} is taken to be the hash of the password."""
    return pw.startswith(("{MD5}", "{CRYPT}", "{SSHA}"))

def remove_user(name, data=False):
    """6.1/6.2.5: cmsupport must not be removed (BCM uses it for diagnostics). `-d` also removes the home directory."""
    if name == "cmsupport":
        raise SecError("cmsupport is used by BCM diagnostics and its home directory contents: do not remove it")
    return {"removed": name, "home_removed": bool(data)}

def group_members(members, action, users):
    """append / removefrom add or remove extra members; `clear members` clears all of them (and the extras)."""
    members = list(members)
    if action == "append":
        return members + [u for u in users if u not in members]
    if action == "removefrom":
        return [m for m in members if m not in users]
    if action == "clear":
        return []
    raise SecError(action)

# ---- 6.5 profiles and tokens ---------------------------------------------------------------------------------------
NONUSER = {"autonomous-hardware-recovery", "autonomous-job-recovery", "bootstrap", "cmhealth", "cmpam", "litenode", "monitoringpush",
           "mqtt", "node", "power", "prs"}
USER_PROFILES = {"admin", "readonly", "portal"}

class Profile:
    def __init__(self, name, tokens=None, all_tokens=False):
        self.name, self.tokens, self.all = name, set(tokens or []), all_tokens

    def allows(self, token):
        return self.all or token in self.tokens

    def remove_tokens(self, *tokens):
        if self.name in NONUSER:
            raise SecError(f"{self.name} is a nonuser profile used by cluster manager clients: never modify it")
        self.tokens -= set(tokens)

def assign_profile(user, profile):
    """6.5: only a subset of the preconfigured profiles is available to users: readonly, admin, portal (plus custom profiles)."""
    if profile in NONUSER:
        raise SecError(f"{profile} is a nonuser profile and cannot be assigned to a user")
    user["profile"] = profile
    return user

def readonly_profile():
    return Profile("readonly", {"GET_DEVICE_TOKEN", "GET_CATEGORY_TOKEN", "GET_NODEGROUP_TOKEN", "POWER_STATUS_TOKEN", "BURN_STATUS_TOKEN", "GET_BURN_LOG_TOKEN"})

# ---- certificates --------------------------------------------------------------------------------------------------------
class Certificate:
    """6.5.2: a certificate carries a profile and a system login, and has an expiry that cannot be extended after creation."""
    def __init__(self, cn, profile, login, days, issued, signed_by="admin-cert-1"):
        if profile not in USER_PROFILES and profile not in NONUSER and not profile.islower():
            raise SecError("profile name must be a valid profile")
        self.cn, self.profile, self.login = cn, profile, login
        self.issued, self.expires, self.signed_by, self.revoked = issued, issued + dt.timedelta(days=days), signed_by, False

    def valid(self, now):
        return not self.revoked and self.issued <= now <= self.expires

    def extend(self, days):
        raise SecError("the time of expiry cannot be extended after creation: create an entirely new certificate")

def createcertificate_args(key_length, cn, org, ou, locality, state, country, profile, sys_login, days, key_file, cert_file, known_profiles):
    """cmsh cert mode: createcertificate <key-length> <common-name> <organization> <organizational-unit> <locality> <state> <country>
    <profile> <sys-login> <days> <key-file> <cert-file>. Light checks only."""
    if int(key_length) < 2048:
        raise SecError("use a key length of at least 2048 (the manual's example)")
    if profile not in known_profiles:
        raise SecError(f"unknown profile {profile}")
    if int(days) <= 0:
        raise SecError("days must be positive")
    return {"cn": cn, "profile": profile, "login": sys_login, "days": int(days), "key": key_file, "cert": cert_file}

def certs_needing_regeneration(certs, admin_cert_replaced=False, license_replaced=False, evaluation_license_replaced=False):
    """2.3.3: if the administrator certificate and key are replaced, certificates signed by the original must be generated again.
    If a license (temporary or evaluation) is replaced, regular user certificates must be generated again."""
    if admin_cert_replaced or license_replaced or evaluation_license_replaced:
        return [c for c in certs if c.profile != "admin" or license_replaced]
    return []

def cmsh_key_lookup(i=None, k=None, home_files=()):
    """6.5.2: -i/-k win; otherwise $HOME/.cm/admin.{pem,key}, then $HOME/.cm/cert.{pem,key}."""
    if i and k:
        return (i, k)
    for base in (".cm/admin", ".cm/cert"):
        if f"{base}.pem" in home_files and f"{base}.key" in home_files:
            return (f"{base}.pem", f"{base}.key")
    return None

# ---- passwords and SSH --------------------------------------------------------------------------------------------------
def password_change_plan(items, ha=False):
    """2.3.1: cm-change-passwd changes the head node root, the root in the software images, the root in the node-installer and MySQL root.
    The LDAP root password is NOT changed by it (Appendix I). HA: rerun on both heads (the image password is copied over automatically).
    An image password works on a running node only after imageupdate or a reboot."""
    valid = {"head", "image", "node-installer", "mysql"}
    bad = set(items) - valid
    if bad:
        raise SecError(f"cm-change-passwd does not change {sorted(bad)} (the LDAP root password has its own procedure, Appendix I)")
    steps = [f"change {i}" for i in items]
    if ha:
        steps.append("run cm-change-passwd on the other head node too (image password copies over by itself)")
    if "image" in items:
        steps.append("imageupdate or reboot nodes so the new image password works on them")
    return steps

def ssh_allowed_without_password(src, dst, user, home_mounted=True):
    """2.3.2: head -> node works passwordless for everyone if /home is mounted (root keys live in /root). node -> head for root asks for a password."""
    if src == "head" and dst == "node":
        return True if user == "root" else home_mounted
    if src == "node" and dst == "head":
        return False if user == "root" else home_mounted
    return False

# ---- external LDAP ------------------------------------------------------------------------------------------------------
def ldap_client_files(distro):
    """6.3: RHEL8 uses /etc/nslcd.conf (+ nslcd daemon); RHEL9 uses /etc/sssd/sssd.conf (+ sssd). Both use /etc/openldap/ldap.conf and the certs
    under /cm/local/apps/openldap/etc/certs/. In the node image the same files live under /cm/images/<image>/."""
    d = distro.lower()
    if d in ("rhel8", "rocky8"):
        return ["/etc/nslcd.conf", "/etc/openldap/ldap.conf"], "nslcd"
    if d in ("rhel9", "rocky9"):
        return ["/etc/sssd/sssd.conf", "/etc/openldap/ldap.conf"], "sssd"
    raise SecError("the manual's LDAP section covers RHEL 8 and RHEL 9 families")

def syncrepl_interval_seconds(text):
    """6.3.1: interval=DD:HH:MM:SS."""
    m = re.fullmatch(r"(\d\d):(\d\d):(\d\d):(\d\d)", text)
    if not m:
        raise SecError("interval format is DD:HH:MM:SS")
    d, h, mi, s = map(int, m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + s

def keycloak_prereq_problems(bcm_version, os_name, ports_free, github_access, prestaged_archive, mysql_running=True, ldap_running=True):
    """6.4.1."""
    p = []
    major_minor_patch = tuple(int(x) for x in bcm_version.split("."))
    if major_minor_patch < (11, 34):
        p.append("needs BCM 11.34 or later")
    if os_name not in ("ubuntu24.04", "ubuntu26.04"):
        p.append("head node must run Ubuntu 24.04 or 26.04 (the scripts use apt; RHEL and Rocky are not supported)")
    if not {9443, 9999} <= set(ports_free):
        p.append("ports 9443 (HTTPS) and 9999 (HTTP) must be free on the head node")
    if not (github_access or prestaged_archive):
        p.append("needs outbound HTTPS to GitHub, or a pre-staged keycloak-<version>.tar.gz under --install-dir (default /opt)")
    if not mysql_running:
        p.append("MySQL or MariaDB must be running")
    if not ldap_running:
        p.append("BCM's internal LDAP must be running")
    return p

def audit_settings(directives):
    """6.5.4: CMDaemonAudit enables logging; CMDaemonAuditorFile sets the location; DisableAuditorForProfiles excludes profiles."""
    p = []
    if str(directives.get("CMDaemonAudit", "0")).lower() not in ("1", "yes", "true", "on"):
        p.append("CMDaemon auditing is off: user actions are not logged")
    elif not directives.get("CMDaemonAuditorFile"):
        p.append("auditing is on but no CMDaemonAuditorFile is set")
    if directives.get("DisableAuditorForProfiles"):
        p.append(f"auditing is disabled for profiles: {directives['DisableAuditorForProfiles']}")
    return p
