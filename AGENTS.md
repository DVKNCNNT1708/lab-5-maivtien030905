# AI Agent Instructions – FIT4110 Lab 05 Docker Compose

**Project:** FIT4110 Lab 05 – Smart Campus Operations Platform (Docker Compose & Readiness)  
**Team:** Core Business (B6) with Multi-Service Integration  
**Stack:** Docker Compose, PostgreSQL, FastAPI, OpenAPI Contracts, Postman/Newman

---

## 1. Quick Start for Agents

### First Time Setup
```bash
# Copy environment file
cp .env.example .env

# Build and start all services
make compose-up

# Verify all containers running
docker compose ps

# Check health endpoints
curl http://localhost:8000/health        # core-business
curl http://localhost:9000/health        # ai-service
docker compose exec db pg_isready -U ${POSTGRES_USER}  # database

# Run test suite
make test-compose
```

### Common Development Workflow
```bash
# After code changes in src/
make compose-up          # Rebuild and restart services

# View logs
make logs               # Follow all service logs
docker compose logs -f core-business    # Specific service

# Stop services
make compose-down       # Full cleanup

# Test API endpoints
make test-compose       # Runs Newman test suite
npm run lint:openapi    # Validate OpenAPI specs
```

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│           Docker Compose Stack (team-internal)          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐ │
│  │ PostgreSQL   │   │  AI Service  │   │  Core      │ │
│  │  Container   │   │  (Mock/Real) │   │ Business   │ │
│  │  Port 5432   │   │  Port 9000   │   │ Port 8000  │ │
│  └──────────────┘   └──────────────┘   └────────────┘ │
│         │                  │                    │      │
│         └──────────────────┴────────────────────┘      │
│              all connected via team-internal           │
└─────────────────────────────────────────────────────────┘

External Access:
- Core Business API: http://localhost:8000
- AI Service: http://localhost:9000
- Database: localhost:5432
```

### Services
- **PostgreSQL (db)**: Persistent storage, Tables: `policies`, `events`. Health check: `pg_isready`
- **AI Service (ai-service)**: Offers `/health` and `/predict` endpoints. Mock YOLO/ML service.
- **Core Business (core-business)**: Main FastAPI app. Calls AI service and DB internally.

### Network
- All services communicate via `team-internal` Docker network using container names (e.g., `http://db:5432`, `http://ai-service:9000`)
- No need to use `localhost` for inter-service communication – use container names

---

## 3. Service-Specific Details

### Core Business Service (`src/core_business/main.py`)
- **FastAPI** application serving Smart Campus operations
- **Key endpoints:**
  - `GET /health` – Service health check
  - `POST /policy/evaluate` – Evaluate policies against events
  - `POST /event/process` – Process events and trigger actions
  - `GET /policy` – List all policies
  - `GET /events` – List recent events

- **Environment variables used:**
  ```
  SERVICE_NAME=core-business
  SERVICE_VERSION=0.5.0
  AUTH_TOKEN=local-dev-token
  DB_HOST=db                    # Use container name, not localhost
  DB_PORT=5432
  POSTGRES_USER=lab05_user
  POSTGRES_PASSWORD=lab05_password
  POSTGRES_DB=lab05_db
  AI_VISION_URL=http://ai-service:9000
  ```

- **Database operations:** Connects via `psycopg2`. Tables auto-created if using migration scripts.
- **Calls AI service**: Uses `requests.get/post` to `http://ai-service:9000/predict`

### AI Service (`src/ai_service/main.py`)
- Mock or real ML service (YOLO v8 or similar)
- Must expose `/health` endpoint
- Exposes `/predict` endpoint for Core Business to call
- Port: 9000 (inside container)

### IoT App (`src/iot_app/main.py`)
- Can remain as secondary service or extended in future labs

---

## 4. Environment Configuration

### .env File (Not Committed)
- Copy from `.env.example` to `.env`
- Define runtime secrets: `POSTGRES_PASSWORD`, `AUTH_TOKEN`
- Override service ports, database credentials, service URLs
- Used by `docker-compose.yml` via `env_file: .env`

### Critical Variables (Must Match docker-compose.yml)
```
POSTGRES_USER=lab05_user
POSTGRES_PASSWORD=lab05_password  # Keep secret!
POSTGRES_DB=lab05_db
AI_SERVICE_PORT=9000
```

**Do NOT commit `.env` to git.** Use `.env.example` as template.

---

## 5. Key Files & Conventions

| File/Folder | Purpose |
|-------------|---------|
| `docker-compose.yml` | Service definitions, networking, healthchecks |
| `.env.example` | Template for `.env` (reference for required vars) |
| `Dockerfile` | Build Core Business image (also `src/ai_service/Dockerfile`) |
| `Makefile` | Shortcuts: `make compose-up`, `make test-compose`, `make logs` |
| `src/core_business/main.py` | Main FastAPI app logic |
| `contracts/iot-ingestion.openapi.yaml` | OpenAPI specification |
| `postman/collections/iot_collection.postman_collection.json` | Integration test suite |
| `postman/environments/FIT4110_lab05_local.postman_environment.json` | Postman env vars (base_url, tokens, etc.) |
| `checklists/readiness-checklist.md` | Pre-Session-6 verification checklist |
| `CORE_BUSINESS_README.md` | Team-specific documentation |
| `CONTRACT.md` | REST/MQTT contracts with other teams |
| `INTEGRATION_GUIDE.md` | Step-by-step integration testing |
| `SESSION_6_CHECKLIST.md` | Session 6 preparation requirements |
| `reports/` | Test reports, Newman output, evidence |

---

## 6. Development Workflow

### Making Code Changes
1. **Modify source files** in `src/core_business/` or `src/ai_service/`
2. **Rebuild containers:**
   ```bash
   make compose-up    # Rebuilds only changed services
   ```
3. **Test immediately:**
   ```bash
   curl http://localhost:8000/health
   make test-compose
   ```

### Adding New Endpoints
1. Add route to `src/core_business/main.py`
2. Update `contracts/iot-ingestion.openapi.yaml`
3. Add test in `postman/collections/iot_collection.postman_collection.json`
4. Rebuild and test:
   ```bash
   make compose-up
   npm run lint:openapi    # Validate spec
   make test-compose       # Run tests
   ```

### Working with Database
- **Migrations**: If adding tables, ensure scripts are idempotent (safe to rerun)
- **Test data**: Insert via `src/core_business/main.py` startup or migration scripts
- **Access database:**
  ```bash
  docker compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
  ```

---

## 7. Testing Strategy

### Unit & Integration Tests
```bash
# Validate OpenAPI spec
npm run lint:openapi

# Run full Postman collection (includes all endpoints)
make test-compose

# View detailed test report
open reports/newman-lab05-compose.html    # macOS
start reports\newman-lab05-compose.html   # Windows
```

### Manual Testing
```bash
# Test specific endpoint
curl -X POST http://localhost:8000/policy/evaluate \
  -H "Content-Type: application/json" \
  -d '{"event_type": "motion_detected", "camera_id": "cam-01"}'

# Check logs while testing
make logs    # In another terminal
```

### Debugging
```bash
# See container startup logs
docker compose logs core-business

# Enter container shell
docker compose exec core-business /bin/bash

# Check inter-service connectivity
docker compose exec core-business \
  curl http://ai-service:9000/health
```

---

## 8. Common Pitfalls & Solutions

| Issue | Solution |
|-------|----------|
| **Container exits immediately** | Check logs: `docker compose logs <service>`. Verify all env vars in `.env`. |
| **"Connection refused" to database** | Ensure `db` service healthcheck passes (`docker compose ps`). Use container name `db`, not `localhost`. |
| **"Cannot reach AI service"** | Verify `ai-service` is running. Inside core-business, use `http://ai-service:9000`, not `http://localhost:9000`. |
| **Port already in use (8000, 5432, 9000)** | Change `.env` or kill process: `lsof -i :8000` (macOS/Linux) or Task Manager (Windows). |
| **".env not found"** | Copy `.env.example` to `.env` first. |
| **Stale container state** | Run `make compose-down` then `make compose-up --build`. |
| **Newman tests fail with 404** | Check Postman environment file has correct base URL and port. |

---

## 9. Tools & Scripts

### Makefile Commands
```bash
make compose-up       # Build and start services in background
make compose-down     # Stop and remove containers
make logs             # Follow logs from all services
make test-compose     # Run Newman test suite
```

### NPM Scripts
```bash
npm run mock:iot           # Start mock IoT server (Prism)
npm run lint:openapi       # Lint OpenAPI spec with Spectral
npm run test:compose       # Alternative to `make test-compose`
```

### Docker Commands
```bash
docker compose ps           # List running services
docker compose logs <svc>   # View logs for a service
docker compose exec <svc> <cmd>   # Run command inside container
docker image ls             # List built images
```

---

## 10. Readiness Checklist (Pre-Session 6)

Before integrating with other teams, verify:

- [ ] All containers start without errors: `docker compose ps` shows all `running`
- [ ] Health endpoints return 200:
  - `curl http://localhost:8000/health`
  - `curl http://localhost:9000/health`
- [ ] Database is up: `docker compose exec db pg_isready -U ${POSTGRES_USER}`
- [ ] Core Business endpoints tested via Postman: `make test-compose` passes
- [ ] `.env.example` documented (new team members can set up quickly)
- [ ] Docker images built and cached on demo machine
- [ ] RAM & disk sufficient for running all services

See [SESSION_6_CHECKLIST.md](SESSION_6_CHECKLIST.md) for detailed requirements.

---

## 11. Integration Points

### Core Business ↔ AI Service
- Core Business calls `POST http://ai-service:9000/predict` with event data
- AI Service returns predictions (mock or real)
- See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for contract details

### Core Business ↔ Database
- Uses `psycopg2` with `DB_DSN` from environment
- Tables: `policies`, `events`
- Connection pooling if needed (future optimization)

### Core Business ↔ External Services (Plugathon)
- Defined in [CONTRACT.md](CONTRACT.md)
- Access Gate, Notification, Analytics services
- Use Service Discovery or IP-based routing in Session 6

---

## 12. Reference Documentation

- **[README.md](README.md)** – Project overview and goals
- **[CORE_BUSINESS_README.md](CORE_BUSINESS_README.md)** – Team-specific docs
- **[RUN_COMPOSE.md](RUN_COMPOSE.md)** – Detailed Docker Compose guide
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** – Service integration testing
- **[CONTRACT.md](CONTRACT.md)** – REST/MQTT contracts
- **[SESSION_6_CHECKLIST.md](SESSION_6_CHECKLIST.md)** – Pre-session requirements
- **[contracts/iot-ingestion.openapi.yaml](contracts/iot-ingestion.openapi.yaml)** – API contract

---

## 13. AI Agent Guidance

### When Modifying Core Business Logic
- Update `src/core_business/main.py`
- Consider database impact (new fields → new columns)
- Add corresponding Postman tests
- Rebuild and test: `make compose-up && make test-compose`

### When Integrating New Services
1. Add service to `docker-compose.yml` (update `version`, `services`, `networks`)
2. Create `.env` entries for credentials/ports
3. Update `CONTRACT.md` with endpoint definitions
4. Add health check to docker-compose.yml
5. Document in [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
6. Add Postman tests

### When Debugging Service Communication
- Use container names (not localhost) for inter-service calls
- Check `docker compose logs` for error messages
- Verify healthchecks: `docker compose ps` should show healthy status
- Test connectivity: `docker compose exec <svc> curl http://<other-svc>:<port>/health`

### When Preparing for Session 6
- Run [SESSION_6_CHECKLIST.md](SESSION_6_CHECKLIST.md) completely
- Generate reports: `make test-compose` outputs to `reports/`
- Ensure `.env` is documented (not committed) but `.env.example` is complete
- Verify WiFi connectivity: will use iPhone hotspot for cross-team communication

---

**Last Updated:** 2026-06  
**Version:** 0.5.0  
**Status:** Ready for Session 6 Integration Testing
