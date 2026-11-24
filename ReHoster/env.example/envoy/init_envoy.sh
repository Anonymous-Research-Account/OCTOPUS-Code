#!/bin/sh
# Waits until the TLS certificate and the generated envoy.yaml are present, then starts envoy.
# envoy.yaml is created by create_docker_startup_scripts.py (one gRPC route per emulator).
while [ ! -s /etc/envoy/certs/certificate.pem ] || [ ! -s /etc/envoy/envoy.yaml ]; do
  echo "init_envoy: waiting for /etc/envoy/certs/certificate.pem and /etc/envoy/envoy.yaml"; sleep 5
done
exec envoy -c /etc/envoy/envoy.yaml
