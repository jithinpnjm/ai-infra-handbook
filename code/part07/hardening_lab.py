#!/usr/bin/env python3
"""Self-checking lab for chapter 7.15: replace a self-signed HTTPS certificate through Redfish (GenerateCSR and
ReplaceCertificate), audit and harden BMC settings, protect against self lock-out, and Secure Boot.
Needs the openssl command. TLS is real (the mock serves HTTPS with TLS 1.2 or newer); the CA is a throw-away lab CA."""
import json, os, shutil, ssl, sys, tempfile, threading
from redfish_mock import make_server
from redfish_crawl import Client
import tls_setup, rf_harden

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def main():
    if not shutil.which("openssl"):
        print("SKIP  needs the openssl command"); return 0
    here = os.path.dirname(os.path.abspath(__file__))
    policy = json.load(open(os.path.join(here, "profiles", "bmc_policy.json")))
    pki = tls_setup.make_pki(tempfile.mkdtemp())
    pkid = os.path.dirname(pki["ca.pem"])
    srv, st = make_server("dgx", 0, tls=(pki["selfsigned.pem"], pki["selfsigned.key"]))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"https://127.0.0.1:{srv.server_address[1]}"

    # --- the starting problem: a self-signed certificate
    try:
        Client(base, "admin", "adminpass", ca=pki["ca.pem"])
        refused = False
    except Exception as e:
        refused = "CERTIFICATE_VERIFY_FAILED" in str(e)
    check("a client that trusts the lab CA REFUSES the BMC's self-signed certificate", refused)
    c = Client(base, "admin", "adminpass", insecure=True)
    cert = c.req("GET", st.cert_uri)[2]
    check("the Certificate resource shows a self-signed certificate (issuer equals subject)", cert["Issuer"]["CommonName"] == cert["Subject"]["CommonName"] == "bmc-selfsigned", cert["Issuer"])
    try:
        import schema_tools
        if os.environ.get("REDFISH_PUBLICATIONS"):
            errs = schema_tools.validate_payload(cert) or []
            errs += schema_tools.validate_payload(c.req("GET", "/redfish/v1/CertificateService")[2]) or []
            errs += schema_tools.validate_payload(c.req("GET", "/redfish/v1/Systems/System_0/SecureBoot")[2]) or []
            check("the Certificate, CertificateService and SecureBoot resources validate against the official schemas", not errs, errs)
    except ImportError:
        pass

    # --- GenerateCSR then ReplaceCertificate
    CS = "/redfish/v1/CertificateService/Actions/CertificateService."
    coll = f"{st.mgr_uri}/NetworkProtocol/HTTPS/Certificates"
    s, _, b = c.req("POST", CS + "ReplaceCertificate", {"CertificateString": "x", "CertificateType": "PEM", "CertificateUri": {"@odata.id": st.cert_uri}})
    check("ReplaceCertificate without a pending request is refused: the private key must be made inside the BMC (400)", s == 400, s)
    s, _, b = c.req("POST", CS + "GenerateCSR", {"CertificateCollection": {"@odata.id": coll}})
    check("GenerateCSR without CommonName is refused (400)", s == 400, s)
    s, _, b = c.req("POST", CS + "GenerateCSR", {"CertificateCollection": {"@odata.id": coll}, "CommonName": "bmc-lab", "Country": "US", "Organization": "Handbook lab",
                                                  "AlternativeNames": ["IP:127.0.0.1", "DNS:localhost"], "KeyPairAlgorithm": "TPM_ALG_RSA", "KeyBitLength": 2048})
    csr = b.get("CSRString", "")
    check("GenerateCSR returns a PEM certificate request (the private key stays in the BMC)", s == 200 and csr.startswith("-----BEGIN CERTIFICATE REQUEST-----") and "PRIVATE" not in csr, s)
    signed = tls_setup.sign_csr(csr, pkid)
    other = open(pki["server.pem"]).read()                      # a valid certificate for a DIFFERENT key
    s, _, b = c.req("POST", CS + "ReplaceCertificate", {"CertificateString": other, "CertificateType": "PEM", "CertificateUri": {"@odata.id": st.cert_uri}})
    check("a certificate that does not match the pending key is refused (400)", s == 400 and "match" in json.dumps(b), (s, b))
    s, _, b = c.req("POST", CS + "ReplaceCertificate", {"CertificateString": "not a certificate", "CertificateType": "PEM", "CertificateUri": {"@odata.id": st.cert_uri}})
    check("garbage instead of a certificate is refused (400)", s == 400, s)
    s, _, _ = c.req("POST", CS + "ReplaceCertificate", {"CertificateString": signed, "CertificateType": "PEM", "CertificateUri": {"@odata.id": st.cert_uri}})
    check("ReplaceCertificate with the CA-signed certificate works (200)", s == 200, s)
    c2 = Client(base, "admin", "adminpass", ca=pki["ca.pem"])
    check("a NEW connection now verifies against the lab CA with no -k", c2.req("GET", "/redfish/v1/")[0] == 200)
    cert = c2.req("GET", st.cert_uri)[2]
    check("the Certificate resource now names the lab CA as issuer", cert["Issuer"]["CommonName"] == "Lab Root CA" and cert["Subject"]["CommonName"] == "bmc-lab", cert["Issuer"])
    check("an operator without ConfigureManager cannot touch certificates (403)",
          Client(base, "operator", "operpass", ca=pki["ca.pem"]).req("POST", CS + "GenerateCSR", {"CertificateCollection": {"@odata.id": coll}, "CommonName": "x"})[0] == 403)

    # --- audit and fix
    F = rf_harden.audit(c2, policy, now=lambda: 1_800_000_000)
    kinds = {k: sum(1 for f in F if f[1] == k) for k in ("FIX", "MANUAL")}
    texts = " | ".join(f[2] for f in F)
    check("the audit finds the open management protocols, no NTP, Basic auth, weak password policy", all(w in texts for w in ("Telnet", "IPMI", "SSDP", "NTP", "Basic", "MinPasswordLength")), texts[:300])
    check("the audit flags the factory account that still must change its password, and a default-style administrator name",
          "PasswordChangeRequired" in texts and "'factory'" in texts, texts[-300:])
    check("the audit flags Secure Boot as not active", "Secure Boot is not active" in texts)
    out = []
    done, refused = rf_harden.apply_fixes(c2, F, "https", yes=False, out=out.append)
    check("apply without --yes only prints the planned changes", done == 0 and out and all(l.startswith("DRY RUN") for l in out) and st.tree[f"{st.mgr_uri}/NetworkProtocol"]["Telnet"]["ProtocolEnabled"] is True)
    out.clear()
    done, refused = rf_harden.apply_fixes(c2, F, "https", yes=True, out=out.append)
    np = st.tree[f"{st.mgr_uri}/NetworkProtocol"]
    check("apply --yes switches off HTTP, Telnet, IPMI and SSDP, turns NTP on with the policy servers",
          not any(np[k]["ProtocolEnabled"] for k in ("HTTP", "Telnet", "IPMI", "SSDP")) and np["NTP"]["ProtocolEnabled"] and np["NTP"]["NTPServers"] == policy["ntp_servers"], np)
    acs = st.tree["/redfish/v1/AccountService"]
    check("apply --yes disables Basic auth and sets the password length 12 (lockout already set)", acs["HTTPBasicAuth"] == "Disabled" and acs["MinPasswordLength"] == 12, acs)
    left = [f for f in rf_harden.audit(c2, policy, now=lambda: 1_800_000_000) if f[1] == "FIX"]
    check("a second audit finds nothing left that the tool can fix", not left, left)
    s, _, _ = c2.req("GET", "/redfish/v1/Systems/System_0", headers={})
    check("the session keeps working after Basic auth is switched off", s == 200, s)

    # --- self lock-out protection
    F2 = [("HIGH", "FIX", "HTTP is enabled", ("PATCH", f"{st.mgr_uri}/NetworkProtocol", {"HTTP": {"ProtocolEnabled": False}}, "HTTP"))]
    out = []
    d, r = rf_harden.apply_fixes(c2, F2, "http", yes=True, out=out.append)
    check("the tool refuses to switch off the protocol it is connected over (would lock you out)", r == 1 and d == 0 and "lock you out" in out[0], out)

    # --- Secure Boot
    SB = "/redfish/v1/Systems/System_0/SecureBoot"
    SYSRESET = "/redfish/v1/Systems/System_0/Actions/ComputerSystem.Reset"
    s, _, b = c2.req("PATCH", SB, {"SecureBootEnable": True})
    check("enabling Secure Boot changes the setting but not the running state (CurrentBoot stays Disabled)", s == 200 and b["SecureBootEnable"] is True and b["SecureBootCurrentBoot"] == "Disabled", b)
    c2.req("POST", SYSRESET, {"ResetType": "GracefulRestart"})
    check("after a restart it is STILL not enforced because no platform key is enrolled (SetupMode)", c2.req("GET", SB)[2]["SecureBootCurrentBoot"] == "Disabled" and c2.req("GET", SB)[2]["SecureBootMode"] == "SetupMode")
    s, _, _ = c2.req("POST", SB + "/Actions/SecureBoot.ResetKeys", {"ResetKeysType": "ResetAllKeysToDefault"})
    check("ResetKeys to the default keys puts the system in UserMode", s == 200 and c2.req("GET", SB)[2]["SecureBootMode"] == "UserMode", s)
    c2.req("POST", SYSRESET, {"ResetType": "GracefulRestart"})
    check("after the next restart Secure Boot is enforced", c2.req("GET", SB)[2]["SecureBootCurrentBoot"] == "Enabled")
    check("the audit no longer lists Secure Boot", "Secure Boot is not active" not in " ".join(f[2] for f in rf_harden.audit(c2, policy, now=lambda: 1_800_000_000)))
    s, _, _ = c2.req("POST", SB + "/Actions/SecureBoot.ResetKeys", {"ResetKeysType": "Banana"})
    check("an unknown ResetKeysType is refused (400)", s == 400, s)

    # --- TLS 1.1 is refused
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(pki["ca.pem"])
    try:
        ctx.maximum_version = ssl.TLSVersion.TLSv1_1
        import socket
        with socket.create_connection(("127.0.0.1", srv.server_address[1]), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname="127.0.0.1"):
                tls11 = True
    except (ssl.SSLError, OSError, ValueError):
        tls11 = False
    check("a TLS 1.1 client cannot connect (the service requires TLS 1.2 or newer)", not tls11)
    try:
        import socket
        sock = socket.create_connection(("127.0.0.1", srv.server_address[1]), timeout=5)
        sock.sendall(b"GET /redfish/v1/ HTTP/1.1\r\nHost: x\r\n\r\n"); sock.settimeout(2)
        data = sock.recv(100)
        plain_ok = data.startswith(b"HTTP/")
    except (OSError, ssl.SSLError):
        plain_ok = False
    check("plain HTTP sent to the HTTPS port gets no Redfish answer", not plain_ok)

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
