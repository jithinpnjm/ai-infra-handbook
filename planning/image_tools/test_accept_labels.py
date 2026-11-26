import re

labels = [
    "Socket activation: Accept=true versus Accept=false",
    "Client connects to port 22222",
    "echo.socket: ListenStream=22222 (systemd holds the listening socket)",
    "Accept=true",
    "systemd itself calls accept() for each connection",
    "it starts a NEW instance per connection named 'echo@<n>-<local>-<peer>.service'",
    "the service file is a template 'echo@.service' with 'StandardInput=socket' and 'ExecStart=/bin/cat'",
    "the connection is the service's standard input and output so it does not need to know it is a network",
    "suits only simple services",
    "Accept=false (default)",
    "systemd passes the LISTENING socket to one service 'echo.service' (not a template)",
    "the service calls accept() itself and keeps control until it exits",
    "it receives the descriptor in $LISTEN_FDS starting at descriptor 3 through sd_listen_fds()",
    "real servers that understand socket activation use this form",
    "sudo systemctl start echo.socket",
    "ss -ltn | grep 22222",
    "echo hi | nc localhost 22222",
    "systemctl list-sockets",
    "With Accept=false the service must support the handoff"
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. {l}")
