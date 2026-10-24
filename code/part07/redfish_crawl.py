#!/usr/bin/env python3
"""Discover a Redfish service by following @odata.id links only. No hard-coded resource names.

Why: DSP0266 5.3 says the resource tree differs between systems, can contain loops, and links must
not be reused between services. This client starts at /redfish/v1/, logs in with a session, walks
every link once (visited set = loop protection), and reports what it found by @odata.type.

usage: redfish_crawl.py http://host:port user password
"""
import collections, json, os, ssl, sys, urllib.error, urllib.request


def tls_context(base, ca=None, insecure=None):
    """HTTPS settings for the clients. By default the certificate is VERIFIED against the system store, or
    against the file in $REDFISH_CA (or the 'ca' argument). Skipping verification needs the explicit
    $REDFISH_INSECURE=1 (or insecure=True) and prints a warning: use it only for a lab."""
    if not base.startswith("https://"):
        return None
    ca = ca or os.environ.get("REDFISH_CA")
    if insecure is None:
        insecure = os.environ.get("REDFISH_INSECURE") == "1"
    if insecure:
        print("WARNING: TLS certificate verification is OFF", file=sys.stderr)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return ssl.create_default_context(cafile=ca)


class LoginError(Exception):
    """Raised when a session cannot be created. .status holds the HTTP status (401 wrong password, 503 busy ...)."""
    def __init__(self, status):
        super().__init__(f"login failed: HTTP {status}")
        self.status = status


class Client:
    def __init__(self, base, user, pw, ca=None, insecure=None, timeout=10):
        self.base, self.token = base.rstrip("/"), None
        self.ctx = tls_context(base, ca, insecure)
        self.creds = (user, pw)
        self.timeout = timeout
        self.relogins = 0
        self.login(user, pw)

    def req(self, method, path, body=None, headers=None, _retry=True):
        """One request. A session that timed out (401 while holding a token) is renewed once and the request repeated."""
        st, hd, b = self._req(method, path, body, headers)
        if st == 401 and self.token and _retry and path != "/redfish/v1/SessionService/Sessions":
            self.token = None
            self.login(*self.creds)
            self.relogins += 1
            return self.req(method, path, body, headers, _retry=False)
        return st, hd, b

    def _req(self, method, path, body=None, headers=None):
        h = {"Accept": "application/json"}
        if self.token:
            h["X-Auth-Token"] = self.token
        h.update(headers or {})
        data = None
        if body is not None:
            data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
        r = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(r, timeout=getattr(self, 'timeout', 10), context=self.ctx) as resp:
                raw = resp.read()
                return resp.status, dict(resp.headers), (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                return e.code, dict(e.headers), json.loads(raw) if raw else None
            except ValueError:
                return e.code, dict(e.headers), raw.decode(errors="replace")

    def login(self, user, pw):
        st, hd, _ = self.req("POST", "/redfish/v1/SessionService/Sessions", {"UserName": user, "Password": pw})
        if st != 201:
            raise LoginError(st)
        self.token, self.session_uri = hd["X-Auth-Token"], hd["Location"]

    def logout(self):
        self._req("DELETE", self.session_uri)       # no renewal here: an expired session is already gone


def links(obj):
    """Yield every @odata.id found anywhere inside a JSON value (not the object's own id)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "@odata.id" and isinstance(v, str):
                yield v
            else:
                yield from links(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from links(v)


def crawl(c):
    seen, todo, types = {}, ["/redfish/v1/"], collections.defaultdict(list)
    while todo:
        uri = todo.pop()
        key = uri.rstrip("/")
        if key in seen:
            continue
        st, _, res = c.req("GET", uri)
        seen[key] = st
        if st != 200 or not isinstance(res, dict):
            continue
        types[(res.get("@odata.type") or "?").lstrip("#").split(".")[0]].append(key)
        own = res.get("@odata.id", "").rstrip("/")
        for l in links({k: v for k, v in res.items() if k not in ("@odata.id", "Actions")}):
            if l.startswith("/redfish/") and l.rstrip("/") not in seen and l.rstrip("/") != own:
                todo.append(l)
    return seen, types


if __name__ == "__main__":
    base, user, pw = sys.argv[1:4]
    c = Client(base, user, pw)
    seen, types = crawl(c)
    print(f"visited {len(seen)} URIs, {sum(1 for s in seen.values() if s != 200)} not OK")
    for u, st in sorted(seen.items()):
        if st != 200:
            print(f"  not OK: HTTP {st} {u}")
    for t in sorted(types):
        print(f"  {t:28} {len(types[t])}  e.g. {types[t][0]}")
    c.logout()
