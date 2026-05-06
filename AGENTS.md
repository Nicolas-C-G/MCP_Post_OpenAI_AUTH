# AGENTS.md

## Project Overview

This repository contains a production-oriented MCP server that connects ChatGPT to a PostgreSQL database through safe, controlled tools.

The MCP server is intended to run inside a Docker container on a GCP virtual machine. PostgreSQL runs separately, preferably on another GCP VM or managed database instance, reachable only through a private network.

The MCP server will be exposed to ChatGPT through HTTPS and protected with Bearer token authentication.

Expected production architecture:

ChatGPT
  -> HTTPS endpoint
  -> nginx / reverse proxy
  -> Dockerized MCP server
  -> private GCP network
  -> PostgreSQL database

## Main Goal

Build a secure MCP server that allows ChatGPT to access selected PostgreSQL data through explicit, read-only tools.

The first production version must be read-only.

Do not implement write operations unless explicitly requested in a future task.

## Tech Stack

Use:

- Python 3.12+
- Official MCP Python SDK
- FastMCP
- PostgreSQL
- asyncpg or psycopg
- pydantic
- pydantic-settings
- python-dotenv
- pytest
- ruff
- Docker
- docker compose for local development only
- nginx for production reverse proxy documentation

Use `uv` for Python dependency management.

## Repository Structure

Follow this structure:

```text
app/
  __init__.py
  main.py
  config.py

  auth/
    __init__.py
    bearer.py

  db/
    __init__.py
    connection.py
    allowlist.py

  tools/
    __init__.py
    health.py
    schema.py
    prospects.py
    analytics.py

  security/
    __init__.py
    query_guard.py

tests/
  test_health.py
  test_auth.py
  test_db_allowlist.py
  test_query_guard.py
  test_tools_schema.py
  test_tools_prospects.py

Dockerfile
docker-compose.yml
.dockerignore
.env.example
.gitignore
pyproject.toml
README.md
AGENTS.md

## Rules for Future Codex Work

- Do not implement arbitrary SQL execution.
- Keep the first production version read-only.
- Do not add write, shell execution, or filesystem access tools.
- Use table allowlists for every tool that accepts a table name.
- Use parameterized queries for all user-provided values.
- Never interpolate user-provided values into SQL except validated allowlisted identifiers.
- Use environment variables for configuration and secrets.
- Do not hardcode or commit secrets.
- Do not expose environment variables through MCP tools.
- Do not return sensitive columns or raw exceptions to MCP clients.
- Update tests and README.md when behavior changes.
