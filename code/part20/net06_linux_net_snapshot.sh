#!/usr/bin/env bash
# Read-only network snapshot for a sick Linux host. Changes nothing.
# Needs: ss, sysctl, nstat (iproute2). conntrack lines need nf_conntrack loaded.
set -u
echo "== socket summary";      ss -s
echo "== listeners (Recv-Q is accept queue length, Send-Q is its limit)"
ss -ltn
echo "== state counts"
ss -tan | awk 'NR>1 {c[$1]++} END {for (s in c) print s, c[s]}'
echo "== queue and port limits"
sysctl net.core.somaxconn net.ipv4.tcp_max_syn_backlog \
       net.ipv4.ip_local_port_range net.ipv4.tcp_fin_timeout 2>&1
echo "== keepalive"
sysctl net.ipv4.tcp_keepalive_time net.ipv4.tcp_keepalive_intvl \
       net.ipv4.tcp_keepalive_probes 2>&1
echo "== conntrack"
sysctl net.netfilter.nf_conntrack_count net.netfilter.nf_conntrack_max 2>&1
echo "== drops and retransmits (counters since boot)"
nstat -az TcpExtListenOverflows TcpExtListenDrops TcpExtTCPSynRetrans \
          TcpRetransSegs TcpExtTCPTimeouts 2>&1
