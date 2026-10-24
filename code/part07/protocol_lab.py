#!/usr/bin/env python3
"""Self-checking lab for chapter 7.3: methods, headers, status codes, ETags, query parameters.

Starts its own mock service on a free port, runs numbered checks against it and prints PASS/FAIL.
Everything it checks is a rule from DSP0266 (clause numbers in brackets). It tests the *mock*, so a pass
means "the mock behaves like the spec says", which is what lets you practise on it.
"""
import base64, json, sys, threading, urllib.request, urllib.error
from redfish_mock import make_server

ok_count = fail_count = 0


def call(base, method, path, body=None, headers=None, auth=("admin", "adminpass")):
    h = {"Accept": "application/json"}
    if auth:
        h["Authorization"] = "Basic " + base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    h.update(headers or {})
    data = json.dumps(body).encode() if body is not None else None
    if data:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(base + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            raw = resp.read()
            return resp.status, dict(resp.headers), json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, dict(e.headers), json.loads(raw) if raw else None
        except ValueError:
            return e.code, dict(e.headers), None


def check(name, cond, detail=""):
    global ok_count, fail_count
    if cond:
        ok_count += 1
    else:
        fail_count += 1
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def main():
    srv, st = make_server("dgx", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    SYS = "/redfish/v1/Systems/System_0"

    s, h, b = call(base, "GET", "/redfish", auth=None)
    check("GET /redfish needs no login and returns the v1 pointer [6.6]", s == 200 and b == {"v1": "/redfish/v1/"})
    s, h, b = call(base, "GET", "/redfish/v1/", auth=None)
    check("service root readable without login [7.2.3]", s == 200 and "RedfishVersion" in b)
    check("root advertises ProtocolFeaturesSupported [7.3.1]", "ProtocolFeaturesSupported" in b)
    s, h, b = call(base, "GET", "/redfish/v1/Systems", auth=None)
    check("collection without login gives 401 [13.3.2]", s == 401, s)
    check("error body has @Message.ExtendedInfo [8.6]", "@Message.ExtendedInfo" in b["error"])
    s, h, b = call(base, "GET", "/redfish/v1/Systems", auth=("admin", "wrong"))
    check("wrong password gives 401, not 403 [8.3]", s == 401, s)

    s, h, b = call(base, "GET", SYS)
    check("GET resource returns 200 + ETag header [6.5]", s == 200 and "ETag" in h)
    check("response has OData-Version 4.0 [8.1]", h.get("OData-Version") == "4.0")
    etag = h["ETag"]
    s2, h2, _ = call(base, "GET", SYS, headers={"If-None-Match": etag})
    check("conditional GET with current ETag gives 304 [7.2.1]", s2 == 304, s2)

    s, h, b = call(base, "GET", SYS + "?$select=PowerState,Status/State")
    check("$select keeps @odata.id/@odata.type and asked properties [7.3.3]",
          s == 200 and set(b) >= {"@odata.id", "@odata.type", "PowerState", "Status"} and "Model" not in b, b)
    s, h, b = call(base, "GET", "/redfish/v1/Chassis/Chassis_0/Sensors?$top=2")
    check("$top=2 returns 2 members, count stays 4, nextLink present [7.2.2]",
          len(b["Members"]) == 2 and b["Members@odata.count"] == 4 and "Members@odata.nextLink" in b)
    s, h, b = call(base, "GET", "/redfish/v1/Chassis/Chassis_0/Sensors?$skip=3&$top=2")
    check("last page has one member and no nextLink", len(b["Members"]) == 1 and "Members@odata.nextLink" not in b)
    s, h, b = call(base, "GET", "/redfish/v1/Chassis?only")
    check("only returns the single member itself [7.3.1]", s == 200 and b.get("@odata.type", "").startswith("#Chassis."))
    s, h, b = call(base, "GET", "/redfish/v1/Systems?only")
    check("only on a 2-member collection returns the collection", b.get("@odata.type", "").startswith("#ComputerSystemCollection"))
    s, h, b = call(base, "GET", "/redfish/v1/Systems?$filter=SystemType%20eq%20'Physical'")
    check("unsupported $filter gives 501 [7.3.1]", s == 501, s)
    s, h, b = call(base, "GET", "/redfish/v1/Systems?$top=abc")
    check("invalid $top value gives 400 [7.3.1]", s == 400, s)
    s, h, b = call(base, "GET", SYS + "?$top=1")
    check("collection-only option on single resource gives 400 [7.3.1]", s == 400, s)
    s, h, b = call(base, "GET", "/redfish/v1/Chassis?only&$top=1")
    check("only combined with another option gives 400 [7.3.1]", s == 400, s)
    s, h, b = call(base, "GET", "/redfish/v1/Chassis/Chassis_0/Sensors?$expand=.($levels=1)&$select=Members")
    check("$expand with $levels=1 inlines members [7.3.2]", "Reading" in b["Members"][0])
    s, h, b = call(base, "HEAD", SYS)
    check("HEAD returns headers and no body [7.4]", s == 200 and b is None)
    s, h, b = call(base, "HEAD", SYS + "?$select=Name")
    check("HEAD with a query parameter is rejected with 400 [7.4]", s == 400, s)
    s, h, b = call(base, "GET", "/redfish/v1/Systems/NoSuchSystem")
    check("missing resource gives 404 [8.3]", s == 404, s)

    # modification
    s, h, b = call(base, "GET", SYS)
    etag = h["ETag"]
    s, h, b = call(base, "PATCH", SYS, {"AssetTag": "RACK12-U7"}, {"If-Match": etag})
    check("PATCH with correct If-Match gives 200 and the new resource [7.6]", s == 200 and b["AssetTag"] == "RACK12-U7", s)
    check("ETag changed after the update [6.5]", h.get("ETag") not in (None, etag))
    s, h, b = call(base, "PATCH", SYS, {"AssetTag": "OTHER"}, {"If-Match": etag})
    check("PATCH with the OLD ETag gives 412 [8.3]", s == 412, s)
    s, h, b = call(base, "PATCH", SYS, {"AssetTag": "A2", "SerialNumber": "X", "Bogus": 1})
    check("partial success: 200 plus ExtendedInfo for the rejected properties [7.6]",
          s == 200 and b["AssetTag"] == "A2" and len(b["@Message.ExtendedInfo"]) == 2, b)
    s, h, b = call(base, "PATCH", SYS, {"SerialNumber": "X"})
    check("all properties read-only gives 400 with details [7.6]", s == 400 and b["error"]["@Message.ExtendedInfo"], s)
    s, h, b = call(base, "PATCH", SYS, {})
    check("empty PATCH gives 400 NoOperation", s == 400, s)
    s, h, b = call(base, "PATCH", SYS, {"AssetTag": "ZZ"}, auth=("viewer", "viewpass"))
    check("read-only role gets 403, not 401 [8.3]", s == 403, s)
    s, h, b = call(base, "PATCH", "/redfish/v1/Chassis/Chassis_0", {"Name": "x"})
    check("PATCH on a resource that does not allow it gives 405 + Allow header [8.3]", s == 405 and "Allow" in h, (s, h.get("Allow")))
    s, h, b = call(base, "PUT", SYS, {"AssetTag": "x"})
    check("unsupported method gives 405 [6.2]", s == 405, s)

    st.require_etag = True
    s, h, b = call(base, "PATCH", SYS, {"AssetTag": "A3"})
    check("service that insists on If-Match answers 428 when it is missing [6.5]", s == 428, s)
    st.require_etag = False

    # session create / delete
    s, h, b = call(base, "POST", "/redfish/v1/SessionService/Sessions", {"UserName": "operator", "Password": "operpass"}, auth=None)
    check("session create gives 201 + X-Auth-Token + Location [8.1]", s == 201 and "X-Auth-Token" in h and "Location" in h, s)
    tok, loc = h["X-Auth-Token"], h["Location"]
    s, h, b = call(base, "GET", SYS, headers={"X-Auth-Token": tok}, auth=None)
    check("token works without Basic auth", s == 200)
    s, h, b = call(base, "DELETE", loc, headers={"X-Auth-Token": tok}, auth=None)
    check("DELETE the session gives 204", s == 204, s)
    s, h, b = call(base, "GET", SYS, headers={"X-Auth-Token": tok}, auth=None)
    check("deleted token no longer works", s == 401, s)

    print(f"\n{ok_count} passed, {fail_count} failed")
    srv.shutdown()
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
