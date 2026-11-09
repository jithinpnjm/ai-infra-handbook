#!/usr/bin/env python3
"""Idle-timeout demo: a middlebox forgets an idle connection, then resets it.
Localhost only. The 'middlebox' is a small server that closes any connection
idle for IDLE seconds, like a load balancer idle timeout. A streaming client
that stays silent longer than IDLE loses the stream. A client that sends a
heartbeat every IDLE/2 seconds keeps it."""
import socket, threading, time

IDLE = 0.6

def middlebox(srv, log):
    srv.settimeout(5)
    conn, _ = srv.accept()
    conn.settimeout(IDLE)
    while True:
        try:
            if not conn.recv(64):
                log.append("peer closed"); break
        except socket.timeout:
            log.append("idle timeout, closing")
            conn.close(); break

def client(heartbeat, quiet_for):
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
    log = []
    t = threading.Thread(target=middlebox, args=(srv, log)); t.start()
    c = socket.create_connection(srv.getsockname())
    end = time.time() + quiet_for
    while time.time() < end:
        if heartbeat:
            c.sendall(b"ping")
        time.sleep(IDLE / 2)
    try:
        c.sendall(b"token")      # first write after the close may succeed
        time.sleep(0.1)
        c.sendall(b"token")      # second write sees the reset or broken pipe
        outcome = "still alive"
    except OSError as e:
        outcome = type(e).__name__
    c.close(); t.join(); srv.close()
    return outcome, log

if __name__ == "__main__":
    print("silent  :", client(heartbeat=False, quiet_for=IDLE * 2))
    print("heartbeat:", client(heartbeat=True, quiet_for=IDLE * 2))
