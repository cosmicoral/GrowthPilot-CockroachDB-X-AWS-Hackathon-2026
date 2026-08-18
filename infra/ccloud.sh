```bash
#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# infra/ccloud.sh — CockroachDB Cloud CLI wrapper for GrowthPilot
#
# Provides a small, non-destructive set of commands so team members can
# check cluster status, retrieve connection parameters, and open an
# interactive SQL shell against the shared CockroachDB Cloud cluster.
#
# Usage:
#   ./infra/ccloud.sh <command> [args...]
#
# Commands:
#   status          Check CLI installation, authentication, and cluster state
#   connection      Display connection parameters for the cluster
#   connection-url  Display the cluster connection URL
#   sql             Open an interactive SQL shell
#   version         Show the installed ccloud CLI version
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
#
# Notes:
#   - This wrapper does not install or download ccloud.
#   - Commands are non-destructive.
#   - Connection URLs may contain sensitive credentials. Handle them securely.
#   - Requires Bash (Linux/macOS/Git Bash/WSL).
# ---------------------------------------------------------------------------

set -euo pipefail

CLUSTER="${CCLOUD_CLUSTER:-gtm-agent}"

if [[ -t 1 ]]; then
    RED=$'\033[0;31m'
    GREEN=$'\033[0;32m'
    YELLOW=$'\033[0;33m'
    BOLD=$'\033[1m'
    RESET=$'\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BOLD=''
    RESET=''
fi

info() {
    printf '%s✓%s %s\n' "${GREEN}" "${RESET}" "$*"
}

warn() {
    printf '%s⚠%s %s\n' "${YELLOW}" "${RESET}" "$*"
}

error() {
    printf '%s✗%s %s\n' "${RED}" "${RESET}" "$*" >&2
}

header() {
    printf '\n%s%s%s\n' "${BOLD}" "$*" "${RESET}"
}

die() {
    error "$*"
    exit 1
}

require_ccloud() {
    if ! command -v ccloud >/dev/null 2>&1; then
        die "ccloud CLI is not installed.

Install it from:
  https://www.cockroachlabs.com/docs/cockroachcloud/ccloud-get-started

Then authenticate with:
  ccloud auth login"
    fi
}

require_auth() {
    if ! ccloud auth whoami >/dev/null 2>&1; then
        die "You are not authenticated with CockroachDB Cloud.

Please run:
  ccloud auth login

Then try again."
    fi
}

cmd_help() {
    cat <<'EOF'
CockroachDB Cloud CLI wrapper for GrowthPilot

Usage:
  ./infra/ccloud.sh <command> [args...]

Commands:
  status          Check CLI installation, authentication, and cluster state
  connection      Display connection parameters for the cluster
  connection-url  Display the cluster connection URL
  sql             Open an interactive SQL shell
  version         Show the installed ccloud CLI version
  help            Show this help message

Environment:
  CCLOUD_CLUSTER  Override the default cluster name
                  (default: gtm-agent)

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
  ./infra/ccloud.sh version
  CCLOUD_CLUSTER=my-cluster ./infra/ccloud.sh status

Security:
  Connection URLs may contain sensitive credentials. Do not paste them into
  logs, pull requests, screenshots, or shared terminals.
EOF
}

cmd_version() {
    require_ccloud
    ccloud version
}

cmd_status() {
    header "CockroachDB Cloud — Cluster Status"
    printf 'Target cluster: %s\n\n' "${CLUSTER}"

    require_ccloud

    local version
    version="$(ccloud version 2>/dev/null || true)"

    if [[ -n "${version}" ]]; then
        info "ccloud CLI is installed (${version})"
    else
        info "ccloud CLI is installed"
    fi

    require_auth

    local identity
    identity="$(ccloud auth whoami 2>/dev/null | head -n 1 || true)"

    if [[ -n "${identity}" ]]; then
        info "Authenticated as: ${identity}"
    else
        info "Authenticated with CockroachDB Cloud"
    fi

    header "Cluster Info"

    if ! ccloud cluster info "${CLUSTER}"; then
        error "Could not retrieve info for cluster '${CLUSTER}'."
        echo
        echo "Check the cluster name with:"
        echo "  ccloud cluster list"
        exit 1
    fi

    echo
    info "Cluster '${CLUSTER}' is reachable."
}

cmd_connection() {
    require_ccloud
    require_auth

    header "Connection Parameters — ${CLUSTER}"
    echo

    if ! ccloud cluster sql --connection-params "${CLUSTER}" "$@"; then
        error "Could not retrieve connection parameters for '${CLUSTER}'."
        echo
        echo "Check the cluster name with:"
        echo "  ccloud cluster list"
        exit 1
    fi
}

cmd_connection_url() {
    require_ccloud
    require_auth

    header "Connection URL — ${CLUSTER}"
    echo

    warn "This output may contain sensitive connection credentials."
    warn "Do not paste it into logs, PRs, screenshots, or shared terminals."
    echo

    if ! ccloud cluster sql --connection-url "${CLUSTER}" "$@"; then
        error "Could not retrieve connection URL for '${CLUSTER}'."
        echo
        echo "Check the cluster name with:"
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

    exec ccloud cluster sql "${CLUSTER}" "$@"
}

main() {
    local cmd_name="${1:-help}"

    if (( $# > 0 )); then
        shift
    fi

    case "${cmd_name}" in
        status)
            cmd_status "$@"
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
        version)
            cmd_version "$@"
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            error "Unknown command: '${cmd_name}'"
            echo
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
```
