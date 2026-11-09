#!/usr/bin/env python3
"""Accept-queue overflow demo. Localhost only, no root, finishes in seconds.
A server calls listen(backlog) but never calls accept(). Clients then connect.
Linux: the first backlog+1 connects succeed, the rest time out (SYN dropped).
Other kernels differ (macOS did not enforce a tiny backlog), so the demo
prints what it saw. An optional third argument holds the sockets open for
that many seconds, so you can run ss -ltn and nstat from a second shell."""
import socket, sys, time

def classify(port, timeout):
    c = socket.socket()
    c.settimeout(timeout)
    try:
        c.connect(("127.0.0.1", port))
        return c, "connected"
    except socket.timeout:
        c.close()
        return None, "timeout"
    except ConnectionRefusedError:
        c.close()
        return None, "refused"
    except ConnectionResetError:
        c.close()
        return None, "reset"

def run(backlog=1, clients=6, timeout=1.0, hold=0.0):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(backlog)          # never accept(): queue fills and stays full
    port = srv.getsockname()[1]
    held, results = [], []
    for i in range(clients):
        sock, outcome = classify(port, timeout)
        results.append(outcome)
        if sock:
            held.append(sock)
    time.sleep(hold)
    for s in held:
        s.close()
    srv.close()
    return results

if __name__ == "__main__":
    backlog = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    clients = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    hold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    res = run(backlog, clients, hold=hold)
    print(f"backlog={backlog} results={res}")
    print("connected:", res.count("connected"), "timeout:", res.count("timeout"),
          "refused:", res.count("refused"), "reset:", res.count("reset"))
