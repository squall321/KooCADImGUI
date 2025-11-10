# KooCAD Backend API

FastAPI-based orchestrator for parametric CAD generation with job queue management.

## Features

✓ **Phase 106-120 Complete** (77.2% overall progress)

### Core Features
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL
- **JWT Authentication** - Secure token-based auth
- **Celery** - Distributed task queue with Redis
- **WebSocket** - Real-time job progress updates
- **Prometheus Metrics** - Production-ready observability
- **Rate Limiting** - Token bucket algorithm
- **Health Checks** - Kubernetes-ready liveness/readiness probes

### API Endpoints

#### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `GET /me` - Get current user info

#### Projects (`/api/v1/projects`)
- `POST /` - Create project
- `GET /` - List user's projects
- `GET /{id}` - Get project details
- `PUT /{id}` - Update project
- `DELETE /{id}` - Delete project

#### Jobs (`/api/v1/jobs`)
- `POST /` - Submit CAD generation job
- `GET /` - List jobs
- `GET /{id}` - Get job status
- `POST /{id}/cancel` - Cancel running job
- `DELETE /{id}` - Delete job

#### Parameters (`/api/v1/parameters`)
- `POST /` - Save parameter set
- `GET /` - List parameter sets
- `GET /{id}` - Get parameter set
- `PUT /{id}` - Update parameter set
- `DELETE /{id}` - Delete parameter set

#### WebSocket
- `WS /ws/{user_id}` - Real-time job updates

#### System
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe (checks DB & Redis)
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

## Installation

### Requirements
```bash
pip install fastapi uvicorn[standard]
pip install sqlalchemy asyncpg pydantic-settings
pip install python-jose[cryptography] passlib[bcrypt]
pip install celery redis
pip install prometheus-client
```

### Database Setup
```bash
# PostgreSQL
createdb koocad
export DATABASE_URL="postgresql://user:pass@localhost:5432/koocad"

# Or use docker
docker run -d --name postgres \
  -e POSTGRES_USER=koocad \
  -e POSTGRES_PASSWORD=koocad \
  -e POSTGRES_DB=koocad \
  -p 5432:5432 \
  postgres:15
```

### Redis Setup
```bash
# Redis for Celery broker
docker run -d --name redis -p 6379:6379 redis:7
```

## Running the Application

### 1. Start FastAPI Server
```bash
# Development
uvicorn koocad.backend.main:app --reload

# Production
uvicorn koocad.backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Start Celery Worker
```bash
# Single worker
celery -A koocad.backend.celery_app worker --loglevel=info

# Multiple workers with concurrency
celery -A koocad.backend.celery_app worker --loglevel=info --concurrency=4
```

### 3. Start Flower (optional monitoring)
```bash
celery -A koocad.backend.celery_app flower --port=5555
```

### 4. View API Documentation
Open http://localhost:8000/docs

## Configuration

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://koocad:koocad@localhost:5432/koocad

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# MinIO (optional)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=koocad
```

## Example Usage

### 1. Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Create Project
```bash
TOKEN="your-jwt-token"
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My CAD Project",
    "description": "BGA packages for PCB"
  }'
```

### 4. Submit CAD Generation Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "cad_generation",
    "parameters": {
      "component_type": "BGA",
      "substrate_width": 12.0,
      "substrate_height": 12.0,
      "ball_rows": 15,
      "ball_cols": 15,
      "ball_pitch": 0.8,
      "ball_diameter": 0.4
    }
  }'
```

### 5. Monitor Job Progress (WebSocket)
```python
import asyncio
import websockets
import json

async def monitor_job(user_id, job_id):
    uri = f"ws://localhost:8000/ws/{user_id}"
    async with websockets.connect(uri) as websocket:
        # Subscribe to job updates
        await websocket.send(json.dumps({
            "type": "subscribe_job",
            "job_id": job_id
        }))

        # Receive updates
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Update: {data}")

            if data.get("status") in ["completed", "failed"]:
                break

asyncio.run(monitor_job(user_id=1, job_id=1))
```

## Architecture

```
┌─────────────────┐
│   FastAPI App   │ - REST API
│   (async)       │ - WebSocket
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│ DB   │  │Redis │
│(PG)  │  │      │
└──────┘  └──┬───┘
             │
        ┌────▼────┐
        │ Celery  │ - CAD generation
        │ Worker  │ - Export tasks
        └─────────┘
```

## Job Types

1. **CAD_GENERATION** - Generate CAD model
   - BGA, MLCC, Resistor, etc.
   - Returns STEP/IGES file

2. **EXPORT_STEP** - Export to STEP format
3. **EXPORT_STL** - Export to STL (mesh)
4. **EXPORT_IGES** - Export to IGES
5. **EXPORT_GLB** - Export to GLB/glTF 2.0
6. **MESHING** - Generate FEM mesh

## Monitoring

### Prometheus Metrics

Available at `http://localhost:8000/metrics`

Metrics:
- `koocad_http_requests_total` - Total HTTP requests
- `koocad_http_request_duration_seconds` - Request duration histogram
- `koocad_http_requests_active` - Active requests gauge
- `koocad_http_errors_total` - Error count by status code
- `koocad_jobs_total` - Total jobs by type/status
- `koocad_job_duration_seconds` - Job duration histogram
- `koocad_jobs_active` - Active jobs by type

### Flower (Celery Monitoring)

Visit `http://localhost:5555` after starting Flower

### Health Checks

- `/health` - Always returns 200 (liveness)
- `/ready` - Returns 200 if DB and Redis are accessible (readiness)

## Database Models

### User
- id, username, email, password_hash
- role (admin/user/guest)
- api_key (for programmatic access)
- is_active

### Project
- id, name, description
- owner_id (FK to User)
- created_at, updated_at

### Job
- id, task_id, job_type, status
- user_id, project_id, parameter_set_id
- parameters (JSON)
- result_file, error_message, progress
- created_at, started_at, completed_at

### ParameterSet
- id, name, description
- project_id (FK to Project)
- parameters (JSON)
- component_type

## Security

- **JWT Tokens** - Stateless authentication
- **Password Hashing** - Bcrypt with salt
- **Role-Based Access** - Admin/User/Guest roles
- **API Rate Limiting** - 60 req/min per user (configurable)
- **CORS** - Configurable allowed origins
- **SQL Injection Prevention** - SQLAlchemy ORM

## Next Steps (Phase 121-145)

- [ ] Export pipeline (STEP, STL, IGES, GLB)
- [ ] Gmsh integration for meshing
- [ ] MinIO file storage
- [ ] Slurm HPC integration
- [ ] Apptainer containers
- [ ] Parameter sweeps
- [ ] LS-DYNA keyword generation

## Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Check connection string
echo $DATABASE_URL
```

### Celery Worker Not Processing
```bash
# Check Redis connection
redis-cli ping

# Check Celery worker logs
celery -A koocad.backend.celery_app worker --loglevel=debug
```

### Rate Limit Issues
```bash
# Disable rate limiting in development
# Comment out in main.py:
# app.add_middleware(RateLimitMiddleware)
```

## License

MIT License - See LICENSE file

## Contributing

Pull requests welcome! See CONTRIBUTING.md for guidelines.
