#!/usr/bin/env python3
"""Make a throw-away certificate authority and server certificates for lab use (needs the openssl command).

  tls_setup.py DIR        creates DIR/ca.pem, DIR/server.pem + server.key (signed by the CA, valid for 127.0.0.1
                          and localhost) and DIR/selfsigned.pem + selfsigned.key (not signed by anyone)

LAB ONLY. Keys are not protected. A real BMC fleet needs a proper CA process (chapter 7.4 and 7.15).
"""
import os, subprocess, sys, tempfile


def run(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def make_pki(d):
    os.makedirs(d, exist_ok=True)
    def p(n): return os.path.join(d, n)
    run("openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", p("ca.key"), "-out", p("ca.pem"),
        "-days", "30", "-subj", "/CN=Lab Root CA", "-addext", "basicConstraints=critical,CA:TRUE", "-addext", "keyUsage=critical,keyCertSign,cRLSign")
    run("openssl", "req", "-newkey", "rsa:2048", "-nodes", "-keyout", p("server.key"), "-out", p("server.csr"), "-subj", "/CN=bmc-lab")
    ext = p("server.ext")
    open(ext, "w").write("subjectAltName=IP:127.0.0.1,DNS:localhost\nbasicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n")
    run("openssl", "x509", "-req", "-in", p("server.csr"), "-CA", p("ca.pem"), "-CAkey", p("ca.key"), "-CAcreateserial", "-out", p("server.pem"),
        "-days", "30", "-extfile", ext)
    run("openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", p("selfsigned.key"), "-out", p("selfsigned.pem"),
        "-days", "30", "-subj", "/CN=bmc-selfsigned", "-addext", "subjectAltName=IP:127.0.0.1,DNS:localhost")
    return {n: p(n) for n in ("ca.pem", "ca.key", "server.pem", "server.key", "selfsigned.pem", "selfsigned.key")}


def sign_csr(csr_pem, d, days=30, san="IP:127.0.0.1,DNS:localhost"):
    """Sign a CSR with the lab CA made by make_pki(d). Returns the certificate as PEM text."""
    def p(n): return os.path.join(d, n)
    open(p("req.csr"), "w").write(csr_pem)
    ext = p("sign.ext")
    open(ext, "w").write(f"subjectAltName={san}\nbasicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n")
    run("openssl", "x509", "-req", "-in", p("req.csr"), "-CA", p("ca.pem"), "-CAkey", p("ca.key"), "-CAcreateserial", "-out", p("signed.pem"),
        "-days", str(days), "-extfile", ext)
    return open(p("signed.pem")).read()


if __name__ == "__main__":
    print(make_pki(sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()))
