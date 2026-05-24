# ImageLab

**Cloud-native, full-stack image processing platform built with 12-Factor App principles.**

ImageLab lets users upload, manage, and process images through a modern web interface backed by a production-grade infrastructure running on AWS EC2. The application is fully containerized with Docker Compose and includes integrated monitoring, centralized logging, caching, and automated CI/CD.

---

## Table of Contents

1. [Overview](#-overview)
2. [Features](#-features)
3. [Architecture](#-architecture)
4. [Tech Stack](#-tech-stack)
5. [Project Structure](#-project-structure)
6. [Environment Variables](#-environment-variables)
7. [API Endpoints](#-api-endpoints)
8. [Local Development Setup](#-local-development-setup)
9. [Running with Docker Compose](#-running-with-docker-compose)
10. [Production Deployment on AWS EC2](#-production-deployment-on-aws-ec2)
11. [Monitoring with Prometheus and Grafana](#-monitoring-with-prometheus-and-grafana)
12. [Logging with Loki and Promtail](#-logging-with-loki-and-promtail)
13. [Caching with Redis](#-caching-with-redis)
14. [CI/CD with GitHub Actions](#-cicd-with-github-actions)
15. [12-Factor App Compliance](#-12-factor-app-compliance)
16. [Useful Commands](#-useful-commands)
17. [Troubleshooting](#-troubleshooting)
18. [Security Notes](#-security-notes)
19. [Future Improvements](#-future-improvements)

---

## Overview

ImageLab is organized into five main layers:

| Layer | Purpose |
|---|---|
| **Backend** | Flask/Gunicorn REST API for authentication, image CRUD, and image processing |
| **Frontend** | React SPA built with Vite, served through Nginx with API reverse proxy |
| **Monitoring** | Prometheus, Node Exporter, cAdvisor, and Grafana for metrics collection and visualization |
| **Logging** | Grafana Loki and Promtail for centralized log aggregation |
| **Caching** | Redis for response caching and performance optimization |

All services run as Docker containers orchestrated by Docker Compose and are deployed to an **AWS EC2** instance running **Ubuntu 24.04 LTS** (2 vCPU, 4 GB RAM, 50 GB disk).

---

## Features

- **Image Upload** — Drag & drop or file picker with multi-file upload support
- **Image Processing** — Histogram equalization, noise reduction, blur, sharpen, edge detection, grayscale, sepia, color inversion, resize, crop, and rotate
- **Processing Pipeline** — Chain multiple operations in a single request
- **Format Conversion** — Convert between PNG, JPG, WebP, BMP, and TIFF
- **Image Compression** — JPEG compression with adjustable quality (1–100)
- **EXIF Metadata** — Extract or strip EXIF/ICC metadata from images
- **Secure Authentication** — JWT-based registration and login
- **Modern UI** — Dark mode, glassmorphism, responsive design
- **Monitoring** — Real-time metrics dashboards with Prometheus and Grafana
- **Centralized Logging** — Container logs aggregated with Loki and queryable via LogQL
- **Caching** — Redis-backed response caching with TTL support
- **CI/CD** — Automated testing, Docker image build, and deployment via GitHub Actions

---

## Architecture

```
┌─────────────┐         ┌──────────────────────────────────────────────────────┐
│   Browser   │────────▶│  Nginx (port 80)                                     │
│             │         │  ┌─────────────┐   ┌──────────────────────────────┐  │
└─────────────┘         │  │ React SPA   │   │ /api/* → reverse proxy       │  │
                        │  │ (static)    │   │        to backend:5000       │  │
                        │  └─────────────┘   └──────────────┬───────────────┘  │
                        └───────────────────────────────────┼──────────────────┘
                                                            │
                                          ┌─────────────────▼─────────────────┐
                                          │  Flask / Gunicorn (port 5000)      │
                                          │  ┌──────────┐  ┌───────────────┐  │
                                          │  │ SQLite   │  │ /metrics      │  │
                                          │  │ (volume) │  │ (Prometheus)  │  │
                                          │  └──────────┘  └───────────────┘  │
                                          │         │              │          │
                                          │         ▼              │          │
                                          │   Upload Volume        │          │
                                          └────────────────────────┼──────────┘
                                                                   │
              ┌────────────────────────────────────────────────────┼────────┐
              │  Monitoring & Logging                               │        │
              │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │        │
              │  │Prometheus│  │ cAdvisor │  │  Node    │◀────────┘        │
              │  │ :9090    │  │ (8080)   │  │ Exporter │                  │
              │  └────┬─────┘  └──────────┘  │ (9100)   │                  │
              │       │                      └──────────┘                  │
              │       ▼                                                    │
              │  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
              │  │ Grafana  │  │  Loki    │◀─┤ Promtail │                 │
              │  │ :3000    │  │  :3100   │  │ (Docker  │                 │
              │  └──────────┘  └──────────┘  │  logs)   │                 │
              │                              └──────────┘                 │
              └───────────────────────────────────────────────────────────┘
                                       │
                            ┌──────────▼──────────┐
                            │   Redis (6379)       │
                            │   Cache Service      │
                            └─────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, Flask 3.1, Gunicorn 23 |
| **Frontend** | React 19, Vite 8, Nginx (Alpine) |
| **Database** | SQLite (persistent Docker volume) |
| **Upload Storage** | Docker volume (`uploads_data`) |
| **Authentication** | Flask-JWT-Extended (JWT tokens) |
| **Image Processing** | Pillow 11, OpenCV (headless) |
| **Caching** | Redis 7 (Alpine) |
| **Monitoring** | Prometheus, Node Exporter, cAdvisor, Grafana |
| **Logging** | Grafana Loki 3.7, Promtail 2.9 |
| **CI/CD** | GitHub Actions |
| **Containerization** | Docker, Docker Compose |
| **Cloud** | AWS EC2 — Ubuntu 24.04 LTS (2 vCPU, 4 GB RAM, 50 GB disk) |

---

## Project Structure

```
image-lab/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Flask application factory
│   │   ├── models.py                # SQLAlchemy models (User, Image)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # Registration, login, current user
│   │   │   ├── images.py            # Upload, list, get, delete, serve file
│   │   │   ├── processing.py        # Process, compress, pipeline, convert, metadata
│   │   │   └── cache_demo.py        # Redis cache demonstration endpoint
│   │   └── services/
│   │       ├── __init__.py
│   │       └── image_processor.py   # Pillow/OpenCV processing operations
│   ├── config.py                    # Environment-based configuration
│   ├── wsgi.py                      # Gunicorn WSGI entry point
│   ├── requirements.txt             # Python dependencies
│   ├── test_all_endpoints.py        # Endpoint test suite
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Root component with routing
│   │   ├── main.jsx                 # React entry point
│   │   ├── index.css                # Global styles
│   │   ├── api/                     # Axios API client
│   │   ├── components/              # Shared UI components
│   │   ├── context/                 # React Context (AuthContext)
│   │   ├── pages/                   # Page components
│   │   └── assets/                  # Static assets
│   ├── nginx.conf                   # Nginx config with API reverse proxy
│   ├── vite.config.js               # Vite configuration
│   ├── package.json                 # Node.js dependencies
│   └── Dockerfile                   # Multi-stage build (Node → Nginx)
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml           # Scrape targets configuration
│   ├── grafana/
│   │   └── provisioning/
│   │       └── datasources/
│   │           ├── prometheus.yml    # Prometheus datasource
│   │           └── loki.yml         # Loki datasource
│   ├── loki/
│   │   └── loki-config.yml          # Loki storage and retention config
│   └── promtail/
│       └── promtail.yml             # Docker log collection config
├── .github/
│   └── workflows/
│       └── deploy.yml               # CI/CD pipeline
├── docker-compose.yml               # Service orchestration
├── .env.example                     # Environment variable template
├── .gitignore
└── README.md
```

---

## Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description | Example |
|---|---|---|
| `FLASK_ENV` | Flask environment (`development` or `production`) | `production` |
| `SECRET_KEY` | Flask secret key for session signing | `change-me-to-a-long-random-string` |
| `JWT_SECRET_KEY` | Secret key for JWT token signing | `change-me-to-another-long-random-string` |
| `JWT_EXPIRE_HOURS` | JWT token expiration time in hours | `24` |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///instance/imagelab.db` |
| `UPLOAD_FOLDER` | Directory for uploaded files inside the container | `/app/uploads` |
| `MAX_CONTENT_LENGTH` | Maximum upload size in bytes (16 MB default) | `16777216` |
| `VITE_API_URL` | Backend API URL used during frontend build | `http://localhost:5000` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |

**Example `.env` file:**

```env
# -- Environment --
FLASK_ENV=production
SECRET_KEY=change-me-to-a-long-random-string
JWT_SECRET_KEY=change-me-to-another-long-random-string
JWT_EXPIRE_HOURS=24

# -- Database --
DATABASE_URL=sqlite:///instance/imagelab.db

# -- Upload --
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=16777216

# -- Frontend --
VITE_API_URL=http://localhost:5000

# -- Cache --
REDIS_URL=redis://redis:6379/0
```

> **Never commit the `.env` file.** It is listed in `.gitignore`.

---

## 🔌 API Endpoints

### Health & Metrics

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/health` | No | Health check — returns `{"status": "ok"}` |
| `GET` | `/metrics` | No | Prometheus metrics (scraped by Prometheus) |

### Authentication (`/api/auth`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | No | Register a new user |
| `POST` | `/api/auth/login` | No | Login and receive a JWT access token |
| `GET` | `/api/auth/me` | JWT | Get current authenticated user info |

### Images (`/api/images`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/images/upload` | JWT | Upload one or more images |
| `GET` | `/api/images` | JWT | List images (paginated: `?page=1&per_page=20`) |
| `GET` | `/api/images/:id` | JWT | Get image metadata (`?download=true` to download) |
| `DELETE` | `/api/images/:id` | JWT | Delete an image |
| `GET` | `/api/images/files/:filename` | No | Serve an uploaded file by UUID filename |

### Processing (`/api/images`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/images/:id/process` | JWT | Apply a single processing operation |
| `POST` | `/api/images/:id/compress` | JWT | JPEG compression with adjustable quality |
| `POST` | `/api/images/:id/pipeline` | JWT | Apply a chain of processing operations |
| `POST` | `/api/images/:id/convert` | JWT | Convert image format (PNG, JPG, WebP, BMP, TIFF) |
| `GET` | `/api/images/:id/metadata` | JWT | Extract EXIF metadata |
| `POST` | `/api/images/:id/remove_metadata` | JWT | Strip all EXIF/ICC metadata |

**Available processing operations:**

`histogram_equalization`, `noise_reduction`, `blur`, `sharpen`, `edge_detection`, `grayscale`, `sepia`, `invert`, `resize`, `crop`, `rotate`

### Cache Demo (`/api`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/cache-demo` | No | Redis cache demonstration (MISS → HIT with 60s TTL) |

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Redis (optional, for caching features)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

```bash
flask run --debug
```

The backend will be available at `http://localhost:5000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server will be available at `http://localhost:5173`.

---

## Running with Docker Compose

### Prerequisites

- Docker Engine 20+
- Docker Compose v2+

### Start All Services

```bash
cp .env.example .env
# Edit .env with your values

docker compose up -d --build
```

### Verify Services

```bash
docker compose ps
```

All 9 services should show as **running**:

| Service | Container | Port | Description |
|---|---|---|---|
| `backend` | `imagelab-backend` | `5000` | Flask/Gunicorn API |
| `frontend` | `imagelab-frontend` | `80` | React SPA via Nginx |
| `redis` | `imagelab-redis` | `6379` (internal) | Cache service |
| `prometheus` | `imagelab-prometheus` | `9090` | Metrics collection |
| `node-exporter` | `imagelab-node-exporter` | `9100` (internal) | Host metrics |
| `cadvisor` | `imagelab-cadvisor` | `8080` (internal) | Container metrics |
| `grafana` | `imagelab-grafana` | `3000` | Dashboards |
| `loki` | `imagelab-loki` | `3100` (localhost only) | Log storage |
| `promtail` | `imagelab-promtail` | — | Log collector |

### Docker Volumes

| Volume | Purpose |
|---|---|
| `uploads_data` | Persistent image upload storage |
| `db_data` | SQLite database persistence |
| `redis_data` | Redis AOF persistence |
| `prometheus_data` | Prometheus TSDB (15-day retention, 5 GB max) |
| `grafana_data` | Grafana dashboards and settings |
| `loki_data` | Loki log chunks and indexes |

### Stop Services

```bash
docker compose down
```

To also remove volumes (!!! deletes all data):

```bash
docker compose down -v
```

---

## Production Deployment on AWS EC2

### Server Specifications

- **Instance type:** 2 vCPU, 4 GB RAM, 50 GB disk
- **OS:** Ubuntu 24.04 LTS
- **Docker & Docker Compose** must be installed on the instance

### Initial Setup

1. **SSH into the EC2 instance:**

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

2. **Install Docker:**

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
newgrp docker
```

3. **Clone and configure:**

```bash
git clone https://github.com/<your-username>/image-lab.git
cd image-lab
cp .env.example .env
nano .env   # Set strong SECRET_KEY and JWT_SECRET_KEY
```

4. **Launch:**

```bash
docker compose up -d --build
```

5. **Verify:**

```bash
curl http://localhost:5000/api/health
# {"status":"ok"}

curl http://localhost/api/health
# {"status":"ok"}  (through Nginx)
```

### AWS Security Group Configuration

| Port | Protocol | Source | Purpose |
|---|---|---|---|
| `22` | TCP | Admin IP only | SSH access |
| `80` | TCP | `0.0.0.0/0` | HTTP (frontend) |
| `443` | TCP | `0.0.0.0/0` | HTTPS (if SSL is configured) |
| `9090` | TCP | Admin IP only | Prometheus dashboard |
| `3000` | TCP | Admin IP only | Grafana dashboard |

> **Do not expose ports 9090, 3000, or 3100 publicly.** Loki (port 3100) is already bound to `127.0.0.1` in `docker-compose.yml`.

---

## Monitoring with Prometheus and Grafana

### Prometheus

Prometheus scrapes metrics every **30 seconds** from the following targets:

| Job Name | Target | Metrics |
|---|---|---|
| `prometheus` | `prometheus:9090` | Prometheus internal metrics |
| `node-exporter` | `node-exporter:9100` | EC2 host CPU, memory, disk, network |
| `cadvisor` | `cadvisor:8080` | Docker container resource usage |
| `imagelab-backend` | `backend:5000/metrics` | Flask request metrics via `prometheus-flask-exporter` |

**Verify Prometheus targets:**

```bash
curl http://localhost:9090/api/v1/targets | python3 -m json.tool
```

In the Prometheus Targets page (`http://<EC2_IP>:9090/targets`), all four jobs — `prometheus`, `node-exporter`, `cadvisor`, and `imagelab-backend` — should appear as **UP**.

**Storage configuration:**
- Retention time: 15 days
- Retention size: 5 GB
- Data stored in the `prometheus_data` Docker volume

### Grafana

Grafana is accessible at `http://<EC2_IP>:3000`.

**Default credentials:**
- Username: `admin`
- Password: `admin123`

**Pre-provisioned datasources:**

| Datasource | Type | URL |
|---|---|---|
| Prometheus | `prometheus` | `http://prometheus:9090` |
| Loki | `loki` | `http://loki:3100` |

Use the **Explore** page in Grafana to run PromQL queries against Prometheus or LogQL queries against Loki.

---

## Logging with Loki and Promtail

All containers follow the **12-Factor App** logging principle: application logs are emitted to `stdout`/`stderr` and are captured by Docker's logging driver.

### How It Works

1. **Containers** write logs to `stdout`/`stderr`
2. **Promtail** discovers running Docker containers via the Docker socket, collects their log streams, and forwards them to Loki
3. **Loki** stores logs with 7-day retention (`168h`)
4. **Grafana** provides a UI to query logs using LogQL

### LogQL Query Examples

Query logs in Grafana → **Explore** → select **Loki** datasource:

```logql
{job="docker"}
```

```logql
{container="imagelab-backend"}
```

```logql
{container="imagelab-frontend"}
```

```logql
{container="imagelab-prometheus"}
```

```logql
{container="imagelab-grafana"}
```

Filter for errors in backend logs:

```logql
{container="imagelab-backend"} |= "ERROR"
```

### Verify Loki

```bash
curl http://localhost:3100/ready
# ready
```

---

## Caching with Redis

Redis 7 (Alpine) runs as an internal service with **AOF persistence** enabled.

### Configuration

- **Container:** `imagelab-redis`
- **Port:** `6379` (exposed only within the Docker network, not publicly)
- **Persistence:** Append-only file stored in the `redis_data` volume
- **Connection URL:** `redis://redis:6379/0` (set via `REDIS_URL` environment variable)

### Cache Demo Endpoint

```
GET /api/cache-demo
```

| Request | Response |
|---|---|
| First request (cold) | `"cache": "MISS"` — data is generated and stored in Redis with a 60-second TTL |
| Subsequent requests (within 60s) | `"cache": "HIT"` — data is served from Redis |
| After TTL expires | `"cache": "MISS"` — cycle repeats |

**Test it:**

```bash
# First request — MISS
curl http://localhost:5000/api/cache-demo

# Second request — HIT
curl http://localhost:5000/api/cache-demo
```

**Verify Redis connectivity:**

```bash
docker exec -it imagelab-redis redis-cli ping
# PONG
```

---

## CI/CD with GitHub Actions

The CI/CD pipeline is defined in `.github/workflows/deploy.yml` and runs on **push** and **pull request** events targeting the `main` branch.

### Pipeline Stages

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    1. Test        │────▶│  2. Docker Build  │────▶│   3. Deploy      │
│  (all branches)  │     │  (main only)      │     │  (main only)     │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

#### Stage 1 — Test (`test`)

Runs on every **push** and **pull request** to `main`:

- **Backend:** Python 3.11 setup → `pip install -r backend/requirements.txt` → `pytest tests/ -v`
- **Frontend:** Node.js 20 setup → `npm ci` → `npm run build`

#### Stage 2 — Docker Build & Push (`docker`)

Runs only on **push to `main`** (after tests pass):

- Logs into **GitHub Container Registry** (`ghcr.io`)
- Builds and pushes `backend` image → `ghcr.io/esatc/image-lab/backend:latest`
- Builds and pushes `frontend` image → `ghcr.io/esatc/image-lab/frontend:latest`

#### Stage 3 — Deploy (`deploy`)

Runs only on **push to `main`** (after Docker build):

- Connects to the AWS EC2 instance via SSH using repository secrets
- Executes:

```bash
cd ~/image-lab
git pull origin main
docker compose up -d --build --remove-orphans
docker image prune -f
```

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `AWS_HOST` | EC2 public IP or hostname |
| `AWS_USER` | SSH username (e.g., `ubuntu`) |
| `AWS_SSH_KEY` | Private SSH key for EC2 access |

---

## 12-Factor App Compliance

| Factor | Principle | Implementation |
|---|---|---|
| **I. Codebase** | One codebase, many deploys | Single GitHub repository |
| **II. Dependencies** | Explicitly declare and isolate | `requirements.txt`, `package.json`, Dockerfiles |
| **III. Config** | Store config in the environment | `.env` file, `os.environ` in `config.py` |
| **IV. Backing Services** | Treat backing services as attached resources | SQLite volume, upload volume, Redis, Prometheus, Loki |
| **V. Build, Release, Run** | Strictly separate build and run stages | Docker image build → Docker Compose deployment |
| **VI. Processes** | Execute the app as stateless processes | Backend is stateless; state stored in SQLite/Redis/volumes |
| **VII. Port Binding** | Export services via port binding | Backend `:5000`, Frontend `:80`, Prometheus `:9090`, Grafana `:3000` |
| **VIII. Concurrency** | Scale out via the process model | Gunicorn workers (`--workers 2`), horizontally scalable |
| **IX. Disposability** | Maximize robustness with fast startup and graceful shutdown | `restart: always` policy, fast container startup |
| **X. Dev/Prod Parity** | Keep dev, staging, and production as similar as possible | Same `docker-compose.yml` used locally and on AWS EC2 |
| **XI. Logs** | Treat logs as event streams | `stdout`/`stderr` → Docker logs → Promtail → Loki |
| **XII. Admin Processes** | Run admin/management tasks as one-off processes | `flask db migrate`, `flask db upgrade`, cleanup via `docker exec` |

---

## Useful Commands

### Docker Compose

```bash
# Build and start all services
docker compose up -d --build

# View running services
docker compose ps

# View backend logs (last 100 lines)
docker compose logs backend --tail=100

# View frontend logs (last 100 lines)
docker compose logs frontend --tail=100

# Follow logs in real time
docker compose logs -f backend

# Restart a specific service
docker compose restart backend

# Stop all services
docker compose down

# Stop and remove volumes (data loss)
docker compose down -v

# Rebuild and restart without orphan containers
docker compose up -d --build --remove-orphans
```

### Health Checks

```bash
# Backend health
curl http://localhost:5000/api/health

# Prometheus metrics endpoint
curl http://localhost:5000/metrics

# Prometheus readiness
curl http://localhost:9090/-/ready

# Loki readiness
curl http://localhost:3100/ready

# Redis connectivity
docker exec -it imagelab-redis redis-cli ping
```

### Database

```bash
# Run Flask migrations (inside container)
docker exec -it imagelab-backend flask db migrate -m "description"
docker exec -it imagelab-backend flask db upgrade

# Open SQLite shell
docker exec -it imagelab-backend python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print('DB ready')"
```

### Cleanup

```bash
# Prune unused Docker images
docker image prune -f

# Prune unused volumes (careful)
docker volume prune -f

# Prune everything (stopped containers, unused networks, images, build cache)
docker system prune -af
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| **Backend container keeps restarting** | Check logs: `docker compose logs backend --tail=200`. Common causes: missing `.env`, incorrect `DATABASE_URL`, or Python dependency issues. |
| **Frontend returns 502 Bad Gateway** | The backend may not be ready yet. Wait a few seconds and retry. Check that the `backend` service is healthy: `docker compose ps`. |
| **Prometheus target is DOWN** | Verify the target container is running. Check network connectivity: `docker exec imagelab-prometheus wget -qO- http://backend:5000/metrics`. |
| **Grafana shows "No data"** | Ensure the Prometheus or Loki datasource is configured. Check Grafana → Settings → Data Sources. |
| **Loki not receiving logs** | Verify Promtail is running and has access to the Docker socket: `docker compose logs promtail --tail=50`. |
| **Redis connection error** | Ensure the `redis` service is running and `REDIS_URL` is set correctly in `.env`. Test with: `docker exec -it imagelab-redis redis-cli ping`. |
| **cAdvisor fails to start** | cAdvisor requires `privileged: true` and access to `/dev/kmsg`. Ensure the host supports these capabilities. |
| **Upload fails with 413** | The default max upload size is 16 MB. Adjust `MAX_CONTENT_LENGTH` in `.env` and `client_max_body_size` in `nginx.conf`. |
| **JWT token expired** | Default expiry is 24 hours. Adjust `JWT_EXPIRE_HOURS` in `.env` or request a new token via `/api/auth/login`. |
| **Port conflict on :80** | Another service may be using port 80. Check with `sudo lsof -i :80` and stop the conflicting service, or change the frontend port mapping in `docker-compose.yml`. |

---

## Security Notes

- **`.env` file must not be committed** to version control. It is listed in `.gitignore`.
- **`SECRET_KEY` and `JWT_SECRET_KEY`** must be long, random strings in production. Generate with:

  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(64))"
  ```

- **Prometheus (`:9090`) and Grafana (`:3000`)** should not be publicly accessible. Restrict access to the admin IP via AWS Security Group rules.
- **Loki (`:3100`)** is already bound to `127.0.0.1` in `docker-compose.yml` and is not publicly accessible.
- **Node Exporter (`:9100`) and cAdvisor (`:8080`)** use `expose` instead of `ports` in `docker-compose.yml`, so they are only accessible within the Docker network.
- **AWS Security Group** recommended rules:

  | Port | Source | Purpose |
  |---|---|---|
  | `22` | Admin IP only | SSH |
  | `80` | `0.0.0.0/0` | HTTP |
  | `443` | `0.0.0.0/0` | HTTPS (if configured) |
  | `9090` | Admin IP only | Prometheus |
  | `3000` | Admin IP only | Grafana |

- **Grafana default credentials** (`admin` / `admin123`) should be changed immediately after first login. Sign-up is disabled (`GF_USERS_ALLOW_SIGN_UP=false`).
- **CORS** is configured to allow all origins for `/api/*` routes. Consider restricting this in production.

---

## Future Improvements

| Area | Improvement |
|---|---|
| **Database** | Migrate from SQLite to PostgreSQL or Amazon RDS for production scalability |
| **Upload Storage** | Move file storage from Docker volumes to Amazon S3 for durability and scalability |
| **HTTPS/SSL** | Add TLS termination with Let's Encrypt (Certbot) or AWS ACM behind a load balancer |
| **Monitoring** | Integrate Amazon CloudWatch for infrastructure-level monitoring and alarms |
| **Alerting** | Configure Prometheus Alertmanager or Grafana alerting for critical metric thresholds |
| **Secret Management** | Use AWS Secrets Manager or HashiCorp Vault instead of `.env` files |
| **Database Migrations** | Automate Flask-Migrate (`flask db upgrade`) as part of the CI/CD deploy step |
| **Horizontal Scaling** | Deploy behind an AWS Application Load Balancer with multiple EC2 instances |
| **CDN** | Add Amazon CloudFront for static asset delivery and image caching |
| **Rate Limiting** | Add API rate limiting with Flask-Limiter or Nginx `limit_req` to prevent abuse |

---

## 📜 License

<!-- Add your license here -->
MIT