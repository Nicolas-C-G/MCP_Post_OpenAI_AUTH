# MCP_Post_OpenAI_AUTH

Production-oriented MCP server that lets ChatGPT access selected PostgreSQL data through explicit, read-only tools.

The first version is intentionally narrow: no arbitrary SQL, no write tools, no shell tools, no filesystem tools, and no secret exposure through MCP responses.

## Architecture

```text
ChatGPT
  -> HTTPS MCP endpoint
  -> nginx / reverse proxy
  -> Dockerized FastMCP server at /mcp
  -> private GCP network
  -> PostgreSQL with read-only database user
```

Production PostgreSQL should run separately from this container, preferably on another GCP VM or managed PostgreSQL instance reachable only over private networking.

## Tools

The server exposes these read-only MCP tools:

- `health_check`
- `db_connection_check`
- `list_allowed_tables`
- `describe_table`
- `get_recent_records`
- `search_prospects`
- `get_prospect_by_id`
- `get_campaign_metrics`

It must not expose tools named `run_sql`, `execute_sql`, `raw_query`, `custom_query`, `query_database`, or `execute_query`.

## Local Setup With uv

```bash
cp .env.example .env
uv sync
uv run python -m app.main
```

The MCP endpoint is:

```text
http://localhost:8000/mcp
```

Clients must include:

```text
Authorization: Bearer <MCP_BEARER_TOKEN>
```

## Docker

Build and run the MCP server:

```bash
docker build -t mcp-post-openai-auth .
docker run --env-file .env -p 8000:8000 mcp-post-openai-auth
```

## Docker Compose

Docker Compose is for local development only. It starts the MCP server plus a local PostgreSQL container.

```bash
cp .env.example .env
docker compose up --build
```

For production, point the MCP container at a separate private PostgreSQL host.

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `MCP_SERVER_NAME` | Display name for the FastMCP server |
| `HOST` | Bind host, usually `0.0.0.0` in Docker |
| `PORT` | HTTP port, default `8000` |
| `MAX_ROWS` | Maximum rows any tool may return |
| `ALLOWED_TABLES` | Comma-separated allowlist of readable tables |
| `MCP_BEARER_TOKEN` | Required Bearer token for MCP HTTP requests |
| `POSTGRES_HOST` | Private PostgreSQL host or IP |
| `POSTGRES_PORT` | PostgreSQL port |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Read-only PostgreSQL username |
| `POSTGRES_PASSWORD` | Read-only PostgreSQL password |

Do not commit `.env` or production secrets.

## PostgreSQL Read-Only User

Create a dedicated PostgreSQL user for MCP access. Do not use the `postgres` superuser.

```sql
CREATE USER mcp_readonly WITH PASSWORD 'replace-with-a-strong-password';
GRANT CONNECT ON DATABASE app_database TO mcp_readonly;
GRANT USAGE ON SCHEMA public TO mcp_readonly;
GRANT SELECT ON TABLE public.prospects TO mcp_readonly;
GRANT SELECT ON TABLE public.campaign_metrics TO mcp_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcp_readonly;
```

Only grant tables that are also listed in `ALLOWED_TABLES`.

## Quality Checks

```bash
uv run pytest
uv run ruff check .
```

## Production GCP Notes

- Run this server in Docker on a VM or container platform.
- Keep PostgreSQL on a private IP, private VM, or managed private database.
- Firewall PostgreSQL so only the MCP server can connect.
- Store `MCP_BEARER_TOKEN` and PostgreSQL credentials in secret management.
- Rotate the Bearer token periodically.
- Keep `MAX_ROWS` low enough for predictable latency and response size.

See [docs/production-gcp.md](docs/production-gcp.md) for a GCP VM deployment guide covering:

- separate MCP and PostgreSQL VMs
- private IP PostgreSQL connectivity
- GCP firewall rules for `tcp:5432`
- nginx reverse proxying to `/mcp`
- HTTPS with Certbot
- Docker Compose restart via systemd
- production environment variables
- ChatGPT MCP configuration

Sanitized examples are available in:

- [docs/examples/nginx-mcp.conf.example](docs/examples/nginx-mcp.conf.example)
- [docs/examples/systemd-docker-compose.service.example](docs/examples/systemd-docker-compose.service.example)
- [docs/examples/production.env.example](docs/examples/production.env.example)

## nginx Reverse Proxy Notes

Terminate HTTPS at nginx and proxy to the local MCP server:

```nginx
location /mcp {
    proxy_pass http://127.0.0.1:8000/mcp;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header Authorization $http_authorization;
}
```

Use TLS certificates from a trusted CA, such as Let's Encrypt.

## ChatGPT MCP Configuration Notes

Configure ChatGPT or an MCP-compatible client with:

```text
URL: https://your-domain.example/mcp
Authorization: Bearer <MCP_BEARER_TOKEN>
```

The server rejects missing, malformed, and invalid Bearer tokens.

## Security Limitations

- This server filters sensitive columns by name, but database-level permissions are still the strongest control.
- Only predefined read-only queries are implemented.
- Table names are accepted only after allowlist and identifier validation.
- Tool responses return generic errors instead of raw Python exceptions.
- PostgreSQL must not be publicly exposed.
- This project does not implement OAuth; it uses a shared Bearer token.
