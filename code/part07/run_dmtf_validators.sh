#!/bin/bash
# Run DMTF's official validators against a Redfish service (here: the lab mock over HTTPS).
#   pip install redfish_service_validator redfish_interop_validator
#   needs a clone of github.com/DMTF/Redfish-Publications (set REDFISH_PUBLICATIONS) for the CSDL schemas
# usage: run_dmtf_validators.sh https://127.0.0.1:8443 user password [cafile]
set -u
URL=$1; U=$2; P=$3; CA=${4:-}
[ -n "$CA" ] && export REQUESTS_CA_BUNDLE=$CA SSL_CERT_FILE=$CA
H=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:-$(mktemp -d)}
echo "== schema validation (rf_service_validator)"
rf_service_validator -r "$URL" -u "$U" -p "$P" --authtype Session --schema_directory "$REDFISH_PUBLICATIONS/csdl" --logdir "$OUT/service" --nooemcheck 2>&1 | grep -E "^\|  +[0-9]"
for prof in gpu_node_acceptance bmc_hardening; do
  echo "== profile $prof (rf_interop_validator)"
  rf_interop_validator -r "$URL" -u "$U" -p "$P" --authtype Session --logdir "$OUT/$prof" "$H/profiles/$prof.json" 2>&1 | grep -E "^\|  +[0-9]"
  grep -h "FAIL -" "$OUT/$prof"/*/RedfishInteropValidatorDebug*.log 2>/dev/null | sed 's/^.*- ERROR - //'
done
echo "reports in $OUT"
