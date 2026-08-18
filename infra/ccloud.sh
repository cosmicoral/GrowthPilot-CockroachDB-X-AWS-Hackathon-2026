#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# infra/ccloud.sh — CockroachDB Cloud CLI wrapper for GrowthPilot
#
# Provides a small, non-destructive set of commands so every team member
# can check cluster status, retrieve connection parameters, and open an
# interactive SQL shell against the shared CockroachDB Cloud cluster.
#
# Usage:
#   ./infra/ccloud.sh <command> [args...]
#
# Commands:
#   status          Check CLI installation, authentication, and cluster state
#   connection      Display connection parameters for the cluster
#   connection-url  Display a single connection URL for the cluster
#   sql             Open an interactive SQL shell
#   help            Show this help message
#
# Environment:
#   CCLOUD_CLUSTER  Override the default cluster name (default: gtm-agent)
#
# Prerequisites:
#   1. Install the CockroachDB Cloud CLI:
#      https://www.cockroachlabs.com/docs/cockroachcloud/ccloud-get-started
#   2. Authenticate:
#      ccloud auth login
# ---------------------------------------------------------------------------

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────
CLUSTER="${CCLOUD_CLUSTER:-gtm-agent}"

# ── Colours (disabled when stdout is not a terminal) ──────────────────────
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BOLD=''
    RESET=''
fi

# ── Helper functions ──────────────────────────────────────────────────────

info()  { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}⚠${RESET} %s\n" "$*"; }
error() { printf "${RED}✗${RESET} %s\n" "$*" >&2; }
header(){ printf "\n${BOLD}%s${RESET}\n" "$*"; }

# ── Prerequisite checks ──────────────────────────────────────────────────

require_ccloud() {
    if ! command -v ccloud &>/dev/null; then
        error "ccloud CLI is not installed."
        echo
        echo "Install it from:"
        echo "  https://www.cockroachlabs.com/docs/cockroachcloud/ccloud-get-started"
        echo
        echo "After installation, authenticate with:"
        echo "  ccloud auth login"
        exit 1
    fi
}

require_auth() {
    if ! ccloud auth whoami &>/dev/null; then
        error "You are not authenticated with CockroachDB Cloud."
        echo
        echo "Please run:"
        echo "  ccloud auth login"
        echo
        echo "Then try again."
        exit 1
    fi
}

# ── Commands ──────────────────────────────────────────────────────────────

cmd_help() {
    cat <<'EOF'
CockroachDB Cloud CLI wrapper for GrowthPilot

Usage:
  ./infra/ccloud.sh <command> [args...]

Commands:
  status          Check CLI installation, authentication, and cluster state
  connection      Display connection parameters for the cluster
  connection-url  Display a single connection URL for the cluster
  sql             Open an interactive SQL shell
  help            Show this help message

Environment:
  CCLOUD_CLUSTER  Override the default cluster name (default: gtm-agent)

Prerequisites:
  1. Install the CockroachDB Cloud CLI:
     https://www.cockroachlabs.com/docs/cockroachcloud/ccloud-get-started
  2. Authenticate:
     ccloud auth login

Examples:
  ./infra/ccloud.sh status
  ./infra/ccloud.sh connection
  ./infra/ccloud.sh connection-url
  ./infra/ccloud.sh sql
  CCLOUD_CLUSTER=my-cluster ./infra/ccloud.sh status
EOF
}

cmd_status() {
    header "CockroachDB Cloud — Cluster Status"
    echo "Target cluster: ${CLUSTER}"
    echo

    # 1. Check ccloud is installed
    require_ccloud
    info "ccloud CLI is installed ($(ccloud version 2>/dev/null || echo 'unknown version'))"

    # 2. Check authentication
    require_auth
    info "Authenticated as: $(ccloud auth whoami 2>/dev/null | head -n 1)"

    # 3. Show cluster info
    header "Cluster Info"
    if ! ccloud cluster info "${CLUSTER}" 2>/dev/null; then
        error "Could not retrieve info for cluster '${CLUSTER}'."
        echo
        echo "Check that the cluster name is correct. You can list available"
        echo "clusters with:"
        echo "  ccloud cluster list"
        exit 1
    fi

    echo
    info "Cluster '${CLUSTER}' is reachable."
}

cmd_connection() {
    header "Connection Parameters — ${CLUSTER}"
    echo

    require_ccloud
    require_auth

    if ! ccloud cluster sql --connection-params "${CLUSTER}" "$@" 2>/dev/null; then
        error "Could not retrieve connection parameters for '${CLUSTER}'."
        echo
        echo "Check that the cluster name is correct with:"
        echo "  ccloud cluster list"
        exit 1
    fi
}

cmd_connection_url() {
    header "Connection URL — ${CLUSTER}"
    echo

    require_ccloud
    require_auth

    if ! ccloud cluster sql --connection-url "${CLUSTER}" "$@" 2>/dev/null; then
        error "Could not retrieve connection URL for '${CLUSTER}'."
        echo
        echo "Check that the cluster name is correct with:"
        echo "  ccloud cluster list"
        exit 1
    fi
}

cmd_sql() {
    require_ccloud
    require_auth

    echo "Opening SQL shell for cluster '${CLUSTER}'..."
    echo "Type \\q to exit."
    echo

    # Pass through any additional arguments (e.g. --database)
    exec ccloud cluster sql "${CLUSTER}" "$@"
}

# ── Main dispatch ─────────────────────────────────────────────────────────

main() {
    local command="${1:-help}"
    shift 2>/dev/null || true

    case "${command}" in
        status)
            cmd_status
            ;;
        connection)
            cmd_connection "$@"
            ;;
        connection-url)
            cmd_connection_url "$@"
            ;;
        sql)
            cmd_sql "$@"
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            error "Unknown command: '${command}'"
            echo
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
