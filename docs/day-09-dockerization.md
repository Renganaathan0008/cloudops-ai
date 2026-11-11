# Day 9: Dockerize the Backend and Target Service

## Architecture

Docker Compose runs the services on its default private bridge network, which
provides service-name DNS such as `postgres`:

| Service | Image source | Host port | Container port | Health endpoint |
| --- | --- | ---: | ---: | --- |
| `postgres` | `postgres:16-alpine` | 5432 | 5432 | PostgreSQL readiness probe |
| `backend` | `cloudops-backend/Dockerfile` | 8000 | 8000 | `/health/db` |
| `target-service` | `target-service/Dockerfile` | 8001 | 8001 | `/health` |

The existing PostgreSQL named volume, `cloudops_postgres_data`, keeps database
data across container restarts and ordinary Compose shutdown. The backend waits
for PostgreSQL's healthy state, applies `alembic upgrade head`, and then starts
Uvicorn. Re-running the upgrade is safe for an already-current database.

Compose supplies database host, port, name, user, and password as environment
variables. The backend uses the Compose service hostname `postgres` and builds a
SQLAlchemy connection URL from those values, so special characters in a password
are escaped correctly. The target service runs independently of the backend and
database.

## Configure and start

From the repository root, ensure `infra/.env` exists and contains the local
PostgreSQL settings from `infra/.env.example`. Keep its values private.

Validate the Compose file without printing resolved environment values:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml config --quiet
```

Build and start all three services:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d --build
```

Build just the application images:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml build backend target-service
```

## Check health and endpoints

Inspect Compose health states:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
```

Check the HTTP endpoints from PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/db
Invoke-RestMethod http://localhost:8001/health
```

The backend database health endpoint executes a database connection check. To
confirm the existing tables remain present, list them inside PostgreSQL:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"'
```

## Logs and rebuilds

Follow service logs:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml logs -f --tail=100 postgres backend target-service
```

Rebuild and recreate the application containers after changing their source or
Dockerfiles:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d --build backend target-service
```

## Run application checks

From the repository root, run the existing test suites and Python style checks
with the installed project tools:

```powershell
& '.\cloudops-backend\.venv\Scripts\pytest.exe' cloudops-backend/tests
& '.\target-service\.venv\Scripts\pytest.exe' target-service/tests
& '.\cloudops-backend\.venv\Scripts\black.exe' --check cloudops-backend/app/core/config.py cloudops-backend/app/db.py cloudops-backend/alembic/env.py
& '.\cloudops-backend\.venv\Scripts\isort.exe' --check-only --profile black cloudops-backend/app/core/config.py cloudops-backend/app/db.py cloudops-backend/alembic/env.py
& '.\cloudops-backend\.venv\Scripts\flake8.exe' --max-line-length=100 --extend-ignore=E203 cloudops-backend/app/core/config.py cloudops-backend/app/db.py cloudops-backend/alembic/env.py
```

## Stop safely

Stop the running containers while retaining them and the database volume:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml stop
```

To remove the containers and Compose network while keeping database data, use:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml down
```

**Do not use `docker compose down -v` for routine shutdown.** The `-v` option
removes the named `cloudops_postgres_data` volume and its database contents.
