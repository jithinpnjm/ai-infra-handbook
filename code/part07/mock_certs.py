"""CertificateService for redfish_mock.py (chapter 7.15): GenerateCSR keeps the private key inside the 'BMC',
ReplaceCertificate installs a signed certificate and the HTTPS server starts using it for NEW connections.
Uses the openssl command. Lab code: keys are written to a temp folder without protection."""
import os, re, subprocess, tempfile

R = "/redfish/v1"


def openssl(*args, input=None):
    p = subprocess.run(["openssl", *args], input=input, capture_output=True, text=True)
    if p.returncode != 0:
        raise ValueError(p.stderr.strip()[:200])
    return p.stdout


def describe(pem_text):
    out = openssl("x509", "-noout", "-subject", "-issuer", "-startdate", "-enddate", "-serial", "-fingerprint", "-sha256", input=pem_text)
    d = {}
    for line in out.splitlines():
        k, _, v = line.partition("=")
        d[k.strip()] = v.strip() if k.strip() not in ("subject", "issuer") else line.split("=", 1)[1].strip()
    cn = lambda s: (re.search(r"CN\s*=\s*([^,/]+)", s) or [None, ""])[1].strip()
    return dict(subject=cn(d["subject"]), issuer=cn(d["issuer"]), notBefore=d["notBefore"], notAfter=d["notAfter"], serial=d["serial"],
                fingerprint=d["sha256 Fingerprint"], self_signed=cn(d["subject"]) == cn(d["issuer"]))


def pubkey_of_cert(pem_text):
    return openssl("x509", "-noout", "-pubkey", input=pem_text).strip()


def pubkey_of_key(keyfile):
    return openssl("pkey", "-in", keyfile, "-pubout").strip()


def _to_iso(s):
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.strptime(s, "%b %d %H:%M:%S %Y %Z"))


def cert_resource(st, pem):
    d = describe(pem)
    uri = st.cert_uri
    return {"@odata.id": uri, "@odata.type": "#Certificate.v1_9_0.Certificate", "Id": "1", "Name": "HTTPS certificate",
            "CertificateString": pem, "CertificateType": "PEM", "Issuer": {"CommonName": d["issuer"]},
            "Subject": {"CommonName": d["subject"]}, "ValidNotBefore": _to_iso(d["notBefore"]), "ValidNotAfter": _to_iso(d["notAfter"]),
            "SerialNumber": ":".join(d["serial"][i:i + 2] for i in range(0, len(d["serial"]) - len(d["serial"]) % 2, 2)) or "00", "Fingerprint": d["fingerprint"], "FingerprintHashAlgorithm": "TPM_ALG_SHA256",
            "KeyUsage": ["DigitalSignature", "KeyEncipherment", "ServerAuthentication"]}


def install_state(st):
    st.cert_uri = f"{st.mgr_uri}/NetworkProtocol/HTTPS/Certificates/1"
    st.csr_pending = None
    st.tree[f"{R}/CertificateService"] = {
        "@odata.id": f"{R}/CertificateService", "@odata.type": "#CertificateService.v1_2_2.CertificateService", "Id": "CertificateService",
        "Name": "Certificate Service",
        "Actions": {"#CertificateService.GenerateCSR": {"target": f"{R}/CertificateService/Actions/CertificateService.GenerateCSR"},
                    "#CertificateService.ReplaceCertificate": {"target": f"{R}/CertificateService/Actions/CertificateService.ReplaceCertificate",
                                                               "CertificateType@Redfish.AllowableValues": ["PEM"]}}}
    st.tree[R]["CertificateService"] = {"@odata.id": f"{R}/CertificateService"}
    refresh(st)


def refresh(st):
    """(Re)build the certificate resources from the file the server is using, if the mock runs HTTPS."""
    files = getattr(st, "tls_files", None)
    coll = f"{st.mgr_uri}/NetworkProtocol/HTTPS/Certificates"
    st.tree[coll] = {"@odata.id": coll, "@odata.type": "#CertificateCollection.CertificateCollection", "Name": "HTTPS certificates",
                     "Members": [], "Members@odata.count": 0}
    if files:
        st.tree[st.cert_uri] = cert_resource(st, open(files[0]).read())
        st.tree[coll]["Members"] = [{"@odata.id": st.cert_uri}]
        st.tree[coll]["Members@odata.count"] = 1
    np = st.tree[f"{st.mgr_uri}/NetworkProtocol"]
    np["HTTPS"]["Certificates"] = {"@odata.id": coll}


def generate_csr(st, p):
    d = tempfile.mkdtemp(prefix="bmc-csr-")
    key, csr = os.path.join(d, "key.pem"), os.path.join(d, "req.csr")
    subj = "".join(f"/{k}={p[v]}" for k, v in (("C", "Country"), ("ST", "State"), ("L", "City"), ("O", "Organization"), ("OU", "OrganizationalUnit"), ("CN", "CommonName")) if p.get(v))
    args = ["req", "-new", "-newkey", f"rsa:{int(p.get('KeyBitLength', 2048))}", "-nodes", "-keyout", key, "-out", csr, "-subj", subj or "/CN=bmc"]
    for n in p.get("AlternativeNames") or []:
        pass
    if p.get("AlternativeNames"):
        args += ["-addext", "subjectAltName=" + ",".join(p["AlternativeNames"])]
    openssl(*args)
    st.csr_pending = {"key": key, "san": p.get("AlternativeNames")}
    return open(csr).read()


def replace(st, pem):
    if not st.csr_pending:
        raise ValueError("no certificate signing request is pending: run GenerateCSR first so the private key stays in the BMC")
    if pubkey_of_cert(pem) != pubkey_of_key(st.csr_pending["key"]):
        raise ValueError("the certificate does not match the private key of the pending request")
    d = tempfile.mkdtemp(prefix="bmc-cert-")
    cert = os.path.join(d, "cert.pem")
    open(cert, "w").write(pem)
    st.tls_ctx.load_cert_chain(cert, st.csr_pending["key"])        # new connections use the new certificate at once
    st.tls_files = (cert, st.csr_pending["key"])
    st.csr_pending = None
    refresh(st)
