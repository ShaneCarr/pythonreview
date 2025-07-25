#!/usr/bin/env bash

# toxiproxy-network-sim.sh
# Usage:
#   ./toxiproxy-network-sim.sh start <profile>
#   ./toxiproxy-network-sim.sh stop
#   ./toxiproxy-network-sim.sh status
#
# Profiles: 3g, 4g, wifi, ethernet

PROXY_NAME="my-api"
LISTEN="127.0.0.1:6666"
UPSTREAM="127.0.0.1:10883"
TOXIPROXY_CLI="toxiproxy-cli"
TOXIPROXY_SERVER="toxiproxy-server"

function install_toxiproxy_if_needed() {
  if ! command -v toxiproxy-cli >/dev/null || ! command -v toxiproxy-server >/dev/null; then
    echo "Installing Toxiproxy via Homebrew..."
    brew install toxiproxy || {
      echo "Failed to install toxiproxy"; exit 1;
    }
  fi
}

function start_server_if_needed() {
  if ! lsof -i :8474 | grep LISTEN >/dev/null; then
    echo "Starting toxiproxy-server in background..."
    nohup $TOXIPROXY_SERVER >/tmp/toxiproxy.log 2>&1 &
    sleep 2
  fi
}

function define_profile() {
  case "$1" in
    3g)
      LATENCY=300
      BANDWIDTH=400
      ;;
    4g)
      LATENCY=150
      BANDWIDTH=4000
      ;;
    wifi)
      LATENCY=50
      BANDWIDTH=10000
      ;;
    ethernet)
      LATENCY=10
      BANDWIDTH=100000
      ;;
    *)
      echo "Unknown profile: $1"; exit 1;
      ;;
  esac
}

function create_proxy() {
  $TOXIPROXY_CLI delete $PROXY_NAME 2>/dev/null
  $TOXIPROXY_CLI create --listen $LISTEN --upstream $UPSTREAM $PROXY_NAME
}

function apply_toxics() {
  $TOXIPROXY_CLI toxic add \
    --toxicName latency-sim \
    --type latency \
    --attribute "latency=${LATENCY}" \
    --downstream \
    $PROXY_NAME

  $TOXIPROXY_CLI toxic add \
    --toxicName bandwidth-sim \
    --type bandwidth \
    --attribute "rate=${BANDWIDTH}" \
    --downstream \
    $PROXY_NAME
}

function clear_proxy() {
  $TOXIPROXY_CLI delete $PROXY_NAME 2>/dev/null
}

function print_status() {
  $TOXIPROXY_CLI list
  $TOXIPROXY_CLI inspect $PROXY_NAME
}

#### Entry Point ####

install_toxiproxy_if_needed
start_server_if_needed

case "$1" in
  start)
    if [ -z "$2" ]; then echo "Missing profile (3g, 4g, wifi, ethernet)"; exit 1; fi
    define_profile "$2"
    create_proxy
    apply_toxics
    echo "✅ Proxy '${PROXY_NAME}' started with profile '$2' (latency=${LATENCY}ms, bandwidth=${BANDWIDTH} kbps)"
    ;;

  stop)
    clear_proxy
    echo "🧹 Proxy '${PROXY_NAME}' cleared"
    ;;

  status)
    print_status
    ;;

  *)
    echo "Usage: $0 {start <profile>|stop|status}"
    exit 1
    ;;
esac
