# Dev environment bootstrap

After `go build` passes, build the image and bring up the full stack via Docker Compose.

```bash
# Build image (go mod download fetches go-lib from the public proxy) and start all services:
docker compose up -d --build

# Wait until every service is healthy (DB, cache, and app itself):
until ! docker compose ps | grep -q "health: starting"; do sleep 2; done
```

The generated `docker-compose.yml` wires the app service to use Docker network hostnames (`postgres`, `redis`, etc.) via `environment:` overrides, while `env_file: .env` supplies all other settings. The `.env` file keeps `localhost` addresses so `go run` still works from the host for debugging.

```bash
# Seed the database (runs on the host against the mapped DB port — .env uses localhost):
source .env && go run ./cmd/seed

# Check everything is up:
curl http://localhost:8080/healthz
curl http://localhost:8080/version
```

> **Tip:** if you need to iterate on code without rebuilding the image, you can still run the service directly:
>
> ```bash
> source .env && go run ./cmd/{name}
> ```
>
> To avoid re-sourcing after each new terminal tab, install `direnv` (`brew install direnv`) and put `dotenv` in `.envrc`.

Swagger UI → `http://localhost:8080/docs`  
API base → `http://localhost:8080/api/v1`
