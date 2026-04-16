# Backend

## Local run with Docker Compose (dev)

1. Create local environment file:

PowerShell:

```powershell
Copy-Item .env.example .env
```

Bash:

```bash
cp .env.example .env
```

If you already had `.env`, sync it with `.env.example` to avoid stale keys.

2. Start backend and database:

```bash
docker compose up --build
```

3. API will be available at:

- `http://localhost:8000`

If `8000` is busy on your host, start with another host port:

```powershell
$env:HOST_API_PORT="8001"; docker compose up --build
```

4. Stop services:

```bash
docker compose down
```