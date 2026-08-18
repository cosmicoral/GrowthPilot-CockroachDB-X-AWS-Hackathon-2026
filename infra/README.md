# CockroachDB Cloud CLI Wrapper

A small, non-destructive wrapper around the `ccloud` CLI for day-to-day
GrowthPilot development. It provides quick access to cluster status,
connection parameters, and an interactive SQL shell against the shared
CockroachDB Cloud cluster.

> **Scope:** This wrapper is read-only. It does not create, delete, scale,
> or modify clusters, SQL users, or network allowlists. Those operations
> remain manual and admin-controlled.

---

## Prerequisites

### 1. Install the CockroachDB Cloud CLI

Follow the official instructions:

https://www.cockroachlabs.com/docs/cockroachcloud/ccloud-get-started

Verify the installation:

```bash
ccloud version
```

### 2. Authenticate

```bash
ccloud auth login
```

This opens a browser window. After you log in, your local session is
stored by `ccloud` and used by all subsequent commands.

To verify your session:

```bash
ccloud auth whoami
```

---

## Usage

```bash
./infra/ccloud.sh <command> [args...]
```

### Available commands

| Command          | Description                                          |
|------------------|------------------------------------------------------|
| `status`         | Check CLI installation, authentication, cluster info |
| `connection`     | Display connection parameters for the cluster        |
| `connection-url` | Display a single connection URL                      |
| `sql`            | Open an interactive SQL shell                        |
| `help`           | Show usage information                               |

### Examples

```bash
# Check everything is working
./infra/ccloud.sh status

# Get connection parameters for .env setup
./infra/ccloud.sh connection

# Get a connection URL string
./infra/ccloud.sh connection-url

# Open an interactive SQL shell
./infra/ccloud.sh sql

# Show help
./infra/ccloud.sh help
```

---

## Configuration

The default target cluster is `gtm-agent`. To override it without
editing the script, set the `CCLOUD_CLUSTER` environment variable:

```bash
CCLOUD_CLUSTER=my-other-cluster ./infra/ccloud.sh status
```

### Default cluster details

| Setting      | Value         |
|--------------|---------------|
| Cluster name | `gtm-agent`   |
| Cloud        | AWS           |
| Region       | `eu-west-2`   |
| Database     | `defaultdb`   |

---

## Relationship to existing project scripts

This wrapper manages **cluster-level** access (status, connection info,
SQL shell). It does not replace the application-level scripts in
`scripts/`:

| Script                              | Purpose                         |
|-------------------------------------|---------------------------------|
| `infra/ccloud.sh`                   | Cluster access and diagnostics  |
| `scripts/migrate.py`               | Apply database schema migrations |
| `scripts/seed_demo_founder.py`     | Seed demo data for FlowForge AI  |
| `scripts/run_analytics_reflection.py` | Run the analytics demo          |

### Typical new-developer workflow

1. Install `ccloud` and authenticate (`ccloud auth login`).
2. Run `./infra/ccloud.sh status` to verify cluster access.
3. Run `./infra/ccloud.sh connection` to get connection parameters.
4. Copy the connection URL into your local `.env` file as `DATABASE_URL`.
5. Run `python scripts/migrate.py` to apply database migrations.
6. Run `python scripts/seed_demo_founder.py` to seed demo data.

> **Security:** Never commit your `.env` file. The wrapper only displays
> connection information from your authenticated `ccloud` session — it
> does not write to `.env` or store credentials.
