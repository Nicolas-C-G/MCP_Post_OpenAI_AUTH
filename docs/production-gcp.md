# Production Deployment on GCP

This guide describes a production-oriented deployment using two Google Cloud VM instances:

```text
ChatGPT
  -> HTTPS MCP URL
  -> nginx on MCP VM
  -> Dockerized MCP server on MCP VM
  -> private VPC connection
  -> PostgreSQL on separate PostgreSQL VM
```

All values below are placeholders. Do not put real domains, IP addresses, passwords, Bearer tokens, or certificate material in this repository.

## VMs

Create two VMs in the same GCP project, VPC, region, and preferably the same zone:

- MCP VM: runs Docker, Docker Compose, nginx, Certbot, and the MCP server container.
- PostgreSQL VM: runs PostgreSQL only.

Recommended network posture:

- MCP VM has a public IP only if it needs to receive HTTPS traffic directly.
- PostgreSQL VM has no public IP.
- MCP VM connects to PostgreSQL using the PostgreSQL VM private IP.
- PostgreSQL listens only on its private interface.

Use placeholders when documenting your environment:

```text
MCP VM private IP: <MCP_VM_PRIVATE_IP>
PostgreSQL VM private IP: <POSTGRES_VM_PRIVATE_IP>
Public HTTPS hostname: <MCP_PUBLIC_HOSTNAME>
```

## Private PostgreSQL Connection

On the MCP VM, set:

```text
POSTGRES_HOST=<POSTGRES_VM_PRIVATE_IP>
POSTGRES_PORT=5432
```

On the PostgreSQL VM, configure PostgreSQL to accept connections on the private interface only. The exact files vary by distribution, but the settings are commonly in `postgresql.conf` and `pg_hba.conf`.

Example intent:

```text
listen_addresses = '<POSTGRES_VM_PRIVATE_IP>'
```

Allow the read-only MCP database user from only the MCP VM private IP:

```text
hostssl <POSTGRES_DB> <POSTGRES_USER> <MCP_VM_PRIVATE_IP>/32 scram-sha-256
```

If you are not using PostgreSQL TLS on the private network, use the equivalent `host` rule instead of `hostssl`, but keep the source restricted to `<MCP_VM_PRIVATE_IP>/32`.

## GCP Firewall Rule

Create a firewall rule that allows PostgreSQL only from the MCP VM private IP.

Example shape:

```text
Direction: ingress
Target: PostgreSQL VM only, preferably by network tag or service account
Source IPv4 range: <MCP_VM_PRIVATE_IP>/32
Protocol/port: tcp:5432
Action: allow
```

Do not allow `0.0.0.0/0` to port `5432`.

For the MCP VM, allow inbound HTTPS:

```text
Direction: ingress
Target: MCP VM only, preferably by network tag or service account
Source IPv4 range: 0.0.0.0/0
Protocol/port: tcp:443
Action: allow
```

Port `80` may be needed temporarily or permanently for Certbot HTTP validation and HTTP-to-HTTPS redirects.

## MCP Server Environment

Create a production environment file on the MCP VM, outside source control. Use [production.env.example](examples/production.env.example) as a template.

Typical path on the VM:

```text
/opt/mcp-post-openai-auth/.env
```

Required values:

```text
MCP_SERVER_NAME=<MCP_SERVER_NAME>
HOST=0.0.0.0
PORT=8000
MAX_ROWS=<MAX_ROWS>
ALLOWED_TABLES=<TABLE_1>,<TABLE_2>
MCP_BEARER_TOKEN=<LONG_RANDOM_BEARER_TOKEN>

POSTGRES_HOST=<POSTGRES_VM_PRIVATE_IP>
POSTGRES_PORT=5432
POSTGRES_DB=<POSTGRES_DB>
POSTGRES_USER=<POSTGRES_READONLY_USER>
POSTGRES_PASSWORD=<POSTGRES_READONLY_PASSWORD>
```

Protect the environment file:

```bash
chmod 600 /opt/mcp-post-openai-auth/.env
```

## Docker Container Restart Policy

For a simple VM deployment, run Docker Compose under systemd so the MCP container starts after reboot.

Use [systemd-docker-compose.service.example](examples/systemd-docker-compose.service.example) as a template. Install it on the MCP VM as:

```text
/etc/systemd/system/mcp-post-openai-auth.service
```

Then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-post-openai-auth
sudo systemctl start mcp-post-openai-auth
sudo systemctl status mcp-post-openai-auth
```

The service uses Docker Compose. Keep production PostgreSQL separate; do not run the local development PostgreSQL service in production.

If you create a production-specific Compose file, include a restart policy like:

```yaml
restart: unless-stopped
```

## nginx Reverse Proxy

nginx should terminate HTTPS and proxy MCP traffic to the local container.

Use [nginx-mcp.conf.example](examples/nginx-mcp.conf.example) as a template. Install it on the MCP VM as an nginx site config, replacing placeholders with local deployment values:

```text
server_name <MCP_PUBLIC_HOSTNAME>;
proxy_pass http://127.0.0.1:8000/mcp;
```

The MCP server expects the Bearer token in the `Authorization` header. Preserve that header through nginx:

```nginx
proxy_set_header Authorization $http_authorization;
```

## HTTPS With Certbot

Install nginx and Certbot on the MCP VM using your operating system package manager.

Typical flow:

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d <MCP_PUBLIC_HOSTNAME>
sudo certbot renew --dry-run
```

Do not commit certificates, private keys, Certbot account material, or generated nginx files containing real hostnames.

## ChatGPT MCP Configuration

Configure ChatGPT or another MCP client with the HTTPS endpoint:

```text
URL: https://<MCP_PUBLIC_HOSTNAME>/mcp
Authorization: Bearer <LONG_RANDOM_BEARER_TOKEN>
```

The Bearer token must match `MCP_BEARER_TOKEN` on the MCP VM.

## Production Checklist

- PostgreSQL VM has no public PostgreSQL exposure.
- GCP firewall allows `tcp:5432` only from `<MCP_VM_PRIVATE_IP>/32`.
- PostgreSQL user is read-only and is not the `postgres` superuser.
- `ALLOWED_TABLES` includes only tables ChatGPT may inspect or read.
- `MAX_ROWS` is set to a conservative value.
- `.env` exists only on the VM or in a secret manager, not in git.
- nginx forwards `/mcp` to the local MCP container.
- HTTPS is active and certificate renewal is tested.
- Docker Compose service starts on reboot.
- ChatGPT MCP configuration uses HTTPS and a Bearer token.

