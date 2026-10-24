#!/usr/bin/env python3
"""Self-checking lab for chapter 7.4: sessions, Basic auth, roles, lockout, forced password change.

Runs a mock Redfish service in-process and moves its clock forward instead of sleeping, so timeouts and
lockouts are tested in milliseconds. Clause numbers refer to DSP0266 v1.21.0. A pass means the *mock*
follows the rule. It does not prove any real BMC does.
"""
import sys, threading
from redfish_mock import make_server
from protocol_lab import call

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def login(base, user, pw):
    s, h, b = call(base, "POST", "/redfish/v1/SessionService/Sessions", {"UserName": user, "Password": pw}, auth=None)
    return s, h, b


def main():
    srv, st = make_server("dgx", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    clock = [1000.0]
    st.now = lambda: clock[0]
    SYS = "/redfish/v1/Systems/System_0"
    ACC = "/redfish/v1/AccountService/Accounts"

    # --- sessions
    s, h, b = login(base, "admin", "adminpass")
    check("login returns 201 with X-Auth-Token, Location and a Session body [13.3.4.2]",
          s == 201 and "X-Auth-Token" in h and "Location" in h and b["@odata.type"].startswith("#Session"), s)
    check("session body never shows the password (it is null) [13.2]", b.get("Password") is None)
    tok, loc = h["X-Auth-Token"], h["Location"]
    check("session id (in Location) differs from the token [13.3.4.2]", loc.rsplit("/", 1)[1] != tok)
    T = {"X-Auth-Token": tok}
    s, _, _ = call(base, "GET", SYS, headers=T, auth=None)
    check("token authenticates later requests", s == 200)
    clock[0] += 200
    s, _, _ = call(base, "GET", SYS, headers=T, auth=None)
    check("a request within the timeout keeps the session alive [13.3.4.3]", s == 200)
    clock[0] += 200
    s, _, _ = call(base, "GET", SYS, headers=T, auth=None)
    check("200 s after the last request: still valid because the timer restarted", s == 200)
    clock[0] += 301
    s, _, _ = call(base, "GET", SYS, headers=T, auth=None)
    check("idle longer than SessionTimeout: session is gone, 401 [13.3.4.3]", s == 401, s)

    # --- failures do not leak
    s1, _, b1 = login(base, "nosuchuser", "whatever1")
    s2, _, b2 = login(base, "admin", "wrongpass1")
    check("unknown user and wrong password give the same 401 and message [13.3.2.3]",
          s1 == s2 == 401 and b1["error"]["message"] == b2["error"]["message"])

    # --- lockout
    for _ in range(2):
        login(base, "viewer", "bad-bad-1")
    s, _, _ = login(base, "viewer", "viewpass")
    check("below the threshold the right password still works", s == 201, s)
    for _ in range(3):
        login(base, "viewer", "bad-bad-1")
    s, _, _ = login(base, "viewer", "viewpass")
    check("after 3 bad attempts the account is locked: even the right password gets 401", s == 401, s)
    s, _, b = call(base, "GET", f"{ACC}/3")
    check("an administrator can see Locked: true on the account", b.get("Locked") is True, b)
    clock[0] += 31
    s, _, _ = login(base, "viewer", "viewpass")
    check("after AccountLockoutDuration the account works again", s == 201, s)
    for _ in range(3):
        login(base, "viewer", "bad-bad-1")
    s, _, b = call(base, "PATCH", f"{ACC}/3", {"Locked": False})
    check("an administrator can unlock early with PATCH Locked false", s == 200 and b["Locked"] is False, (s, b))
    s, _, _ = login(base, "viewer", "viewpass")
    check("unlocked account logs in", s == 201, s)

    # --- roles
    s, _, _ = call(base, "PATCH", SYS, {"AssetTag": "OP-1"}, auth=("operator", "operpass"))
    check("Operator can configure components (PATCH a system) [13.4.2.1]", s == 200, s)
    s, _, _ = call(base, "POST", ACC, {"UserName": "x", "Password": "longenough1", "RoleId": "ReadOnly"}, auth=("operator", "operpass"))
    check("Operator cannot create accounts (needs ConfigureUsers): 403", s == 403, s)
    s, _, _ = call(base, "PATCH", SYS, {"AssetTag": "VW-1"}, auth=("viewer", "viewpass"))
    check("ReadOnly cannot change components: 403", s == 403, s)
    s, _, _ = call(base, "GET", SYS, auth=("viewer", "viewpass"))
    check("ReadOnly can read", s == 200, s)
    s, h, b = call(base, "POST", ACC, {"UserName": "prom_scraper", "Password": "scrape-pass-1", "RoleId": "ReadOnly"})
    check("Administrator creates an account: 201 with Location, password hidden",
          s == 201 and "Location" in h and b["Password"] is None, (s, b))
    s, _, _ = call(base, "POST", ACC, {"UserName": "prom_scraper", "Password": "scrape-pass-1", "RoleId": "ReadOnly"})
    check("creating the same user again gives 409", s == 409, s)
    s, _, _ = call(base, "POST", ACC, {"UserName": "weak", "Password": "short", "RoleId": "ReadOnly"})
    check("password shorter than MinPasswordLength is refused: 400", s == 400, s)
    s, _, _ = call(base, "POST", ACC, {"UserName": "bad", "Password": "longenough1", "RoleId": "God"})
    check("unknown RoleId is refused: 400", s == 400, s)
    s, _, _ = call(base, "GET", SYS, auth=("prom_scraper", "scrape-pass-1"))
    check("the new read-only account can read", s == 200, s)

    # --- own password
    s, _, b = call(base, "GET", f"{ACC}/3", auth=("viewer", "viewpass"))
    check("a user can read their own account", s == 200 and b["UserName"] == "viewer", s)
    s, _, _ = call(base, "PATCH", f"{ACC}/3", {"Password": "new-viewer-pass"}, auth=("viewer", "viewpass"))
    check("ConfigureSelf lets a user change their own password", s == 200, s)
    s, _, _ = call(base, "PATCH", f"{ACC}/3", {"RoleId": "Administrator"}, auth=("viewer", "new-viewer-pass"))
    check("a user cannot promote themselves: 403", s == 403, s)
    s, _, _ = call(base, "PATCH", f"{ACC}/2", {"Password": "hijack-pass-1"}, auth=("viewer", "new-viewer-pass"))
    check("a ReadOnly user cannot change someone else's password: 403", s == 403, s)

    # --- forced password change
    s, h, b = login(base, "factory", "changeme1")
    check("account with PasswordChangeRequired can log in and is told so (ExtendedInfo) [13.5.4]",
          s == 201 and any("PasswordChangeRequired" in m["MessageId"] for m in b.get("@Message.ExtendedInfo", [])), (s, b))
    FT = {"X-Auth-Token": h["X-Auth-Token"]}
    s, _, b = call(base, "GET", SYS, headers=FT, auth=None)
    check("...but everything else is 403 PasswordChangeRequired [13.5.4]", s == 403 and "PasswordChangeRequired" in b["error"]["code"], (s, b))
    s, _, b = call(base, "GET", f"{ACC}/4", headers=FT, auth=None)
    check("...except reading its own account", s == 200 and b["PasswordChangeRequired"] is True, s)
    s, _, _ = call(base, "PATCH", f"{ACC}/4", {"Password": "short"}, headers=FT, auth=None)
    check("too-short new password is refused: 400", s == 400, s)
    s, _, b = call(base, "PATCH", f"{ACC}/4", {"Password": "a-better-password-2"}, headers=FT, auth=None)
    check("PATCH own Password clears the flag [13.5.4]", s == 200 and b["PasswordChangeRequired"] is False, (s, b))
    s, _, _ = call(base, "GET", SYS, headers=FT, auth=None)
    check("the session now works normally", s == 200, s)

    # --- ChangePassword action
    s, _, _ = call(base, "POST", f"{ACC}/2/Actions/ManagerAccount.ChangePassword",
                   {"NewPassword": "operator-new-pw-3", "SessionAccountPassword": "WRONG"}, auth=("operator", "operpass"))
    check("ChangePassword with a wrong SessionAccountPassword is refused: 401 [13.5.3]", s == 401, s)
    s, _, _ = call(base, "POST", f"{ACC}/2/Actions/ManagerAccount.ChangePassword",
                   {"NewPassword": "operator-new-pw-3", "SessionAccountPassword": "operpass"}, auth=("operator", "operpass"))
    check("ChangePassword with the current password works [13.5.3]", s == 200, s)
    s, _, _ = login(base, "operator", "operator-new-pw-3")
    check("login with the new password works", s == 201, s)

    # --- session management
    s, h, _ = login(base, "operator", "operator-new-pw-3")
    OT, ouri = {"X-Auth-Token": h["X-Auth-Token"]}, h["Location"]
    s, _, _ = call(base, "DELETE", ouri, auth=("viewer", "new-viewer-pass"))
    check("a ReadOnly user cannot end someone else's session: 403", s == 403, s)
    s, _, _ = call(base, "DELETE", ouri)
    check("an administrator can end another user's session: 204 [13.3.4.4]", s == 204, s)
    s, _, _ = call(base, "GET", SYS, headers=OT, auth=None)
    check("the ended session no longer works", s == 401, s)
    s, h, _ = login(base, "operator", "operator-new-pw-3")
    OT2 = {"X-Auth-Token": h["X-Auth-Token"]}
    call(base, "PATCH", f"{ACC}/2", {"Password": "operator-pw-again-4"})
    s, _, _ = call(base, "GET", SYS, headers=OT2, auth=None)
    check("an admin password reset closes that user's open sessions [13.5.2]", s == 401, s)
    s, _, _ = call(base, "DELETE", f"{ACC}/1")
    check("you cannot delete the account you are using: 409", s == 409, s)

    # --- Basic can be switched off
    s, _, _ = call(base, "PATCH", "/redfish/v1/AccountService", {"HTTPBasicAuth": "Disabled"})
    check("administrator can disable HTTP Basic [13.3.3]", s == 200, s)
    s, _, _ = call(base, "GET", SYS)
    check("Basic is now refused: 401", s == 401, s)
    s, h, _ = login(base, "admin", "adminpass")
    s2, _, _ = call(base, "GET", SYS, headers={"X-Auth-Token": h["X-Auth-Token"]}, auth=None)
    check("sessions still work with Basic disabled", s2 == 200, s2)

    print(f"\n{ok_count} passed, {fail_count} failed")
    srv.shutdown()
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
