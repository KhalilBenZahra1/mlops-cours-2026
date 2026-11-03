#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source infra/versions.env
port=${KFP_UI_PORT:-8082}
host="http://localhost:$port"
log=/tmp/mlops-port-forward/kfp-ui.log
mkdir -p "$(dirname "$log")"
# Reuse a healthy forward, including one started manually. No broad pkill:
# Make runs recipes through bash -c, whose command line contains the pattern.
if curl -fsS --max-time 3 "$host/apis/v2beta1/healthz" >/dev/null; then
  echo "KFP UI/API déjà accessible -> $host"
  exit 0
fi
nohup kubectl --context "kind-$KIND_CLUSTER_NAME" -n kubeflow \
  port-forward svc/ml-pipeline-ui "$port:80" >"$log" 2>&1 &
pid=$!
echo "$pid" >/tmp/mlops-port-forward/kfp-ui.pid
for _ in $(seq 1 15); do
  if curl -fsS --max-time 2 "$host/apis/v2beta1/healthz" >/dev/null; then
    echo "KFP UI/API -> $host"
    exit 0
  fi
  kill -0 "$pid" 2>/dev/null || { cat "$log"; exit 1; }
  sleep 1
done
echo "API indisponible ; consulter $log" >&2
exit 1
