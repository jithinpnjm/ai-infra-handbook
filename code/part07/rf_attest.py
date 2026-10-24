#!/usr/bin/env python3
"""List the integrity (attestation) information a Redfish service exposes. READ-ONLY and only a first step.

  rf_attest.py http://host:port user pw

Finds every ComponentIntegrity resource (SPDM or TPM based) and the manager's SecurityPolicy, and prints what each
reports: the type, whether it is enabled, which component it protects, how many measurements it holds and whether
the identity check succeeded. IMPORTANT: this does NOT verify anything. Real attestation means asking the device to
SIGN its measurements together with a fresh nonce (actions SPDMGetSignedMeasurements and TPMGetSignedMeasurements),
checking the signature against a certificate chain you trust, and comparing the measurements with known-good values
from the vendor. That needs a verifier and golden values this lab does not have.
"""
import sys
from redfish_crawl import Client, links
from rf_inventory import get


def find(c, wanted):
    todo, seen, out = ["/redfish/v1/"], set(), []
    while todo:
        u = todo.pop().split("#")[0]
        k = u.rstrip("/")
        if k in seen or any(s in k for s in ("/LogServices", "/Sensors", "/Registries", "/Certificates", "/Metrics")):
            continue
        seen.add(k)
        r = get(c, u)
        if not r:
            continue
        if (r.get("@odata.type") or "").lstrip("#").split(".")[0] in wanted:
            out.append(r)
        for l in links({a: b for a, b in r.items() if a not in ("@odata.id", "Actions", "Links")}):
            if l.startswith("/redfish/") and l.rstrip("/") not in seen:
                todo.append(l)
    return out


def main(argv):
    c = Client(*argv[1:4])
    try:
        ci = find(c, {"ComponentIntegrity"})
        pol = find(c, {"SecurityPolicy"})
        print(f"{len(ci)} ComponentIntegrity resource(s), {len(pol)} SecurityPolicy resource(s)")
        for r in ci:
            t = r.get("ComponentIntegrityType")
            body = r.get(t) or {}
            ms = (body.get("MeasurementSet") or {}).get("Measurements") or []
            ident = body.get("IdentityAuthentication") or {}
            ver = ident.get("VerificationStatus") or (ident.get("ResponderAuthentication") or {}).get("VerificationStatus")
            print(f"  {r['Id']:12} {t:5} enabled={r.get('ComponentIntegrityEnabled')!s:5} target={r.get('TargetComponentURI', '')[-30:]:30} "
                  f"measurements={len(ms):2} identity={ver} health={r.get('Status', {}).get('Health')}")
        for p in pol:
            spdm, tls = p.get("SPDM") or {}, p.get("TLS") or {}
            print(f"  SecurityPolicy: SPDM enabled={spdm.get('Enabled')} verify_certificate={spdm.get('VerifyCertificate')}; "
                  f"TLS client allowed versions={((tls.get('Client') or {}).get('Allowed') or {}).get('Versions')}")
        print("\nnote: nothing here is verified; see the module text for what real attestation needs")
    finally:
        c.logout()


if __name__ == "__main__":
    main(sys.argv)
