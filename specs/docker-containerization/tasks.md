# Docker Containerization Tasks

**Feature**: Docker Containerization for Render Deployment
**Backend**: Python FastAPI Application
**Target Runtime**: Render PaaS
**Port**: 10000

---

## Phase 1: Setup & Infrastructure Preparation

**Goal**: Prepare the backend for containerization by verifying dependencies and creating Docker configuration structure.

**Test Criteria**:
- [ ] `requirements.txt` exists in `/backend` with all dependencies listed
- [ ] Backend application structure verified (main.py, config.py, etc.)
- [ ] Docker configuration directory created with proper structure

### Tasks

- [ ] T001 Verify backend dependencies are complete in `/backend/requirements.txt`
- [ ] T002 Ensure main.py is correctly structured with FastAPI app instance in `/backend/main.py`
- [ ] T003 Create `.dockerignore` file in project root to exclude unnecessary files
- [ ] T004 Create `Dockerfile` in project root for production-ready Python image

---

## Phase 2: Dockerfile Creation & Optimization

**Goal**: Create a production-ready Dockerfile following best practices for FastAPI and Render deployment.

**Test Criteria**:
- [ ] Dockerfile uses Python 3.11 slim base image
- [ ] Working directory properly set to `/app`
- [ ] All dependencies installed from `requirements.txt`
- [ ] .env file NOT included in Docker image
- [ ] Port 10000 exposed for Render
- [ ] uvicorn startup command correctly configured
- [ ] Non-root user created for security

### Tasks

- [ ] T005 Create base image section in `Dockerfile` using `python:3.11-slim`
- [ ] T006 [P] Set working directory to `/app` in `Dockerfile`
- [ ] T006 [P] Create non-root user `appuser` in `Dockerfile` for security
- [ ] T007 Copy only required files (pyproject.toml or requirements.txt) in `Dockerfile`
- [ ] T008 Install Python dependencies from `requirements.txt` in `Dockerfile`
- [ ] T009 Copy entire application code to `/app` in `Dockerfile`
- [ ] T010 Expose port 10000 in `Dockerfile`
- [ ] T011 Set entrypoint to uvicorn with command: `uvicorn main:app --host 0.0.0.0 --port 10000` in `Dockerfile`
- [ ] T012 Verify Dockerfile has no hardcoded environment variables in `Dockerfile`

---

## Phase 3: Docker Image Build & Testing

**Goal**: Build, test, and validate the Docker image locally before deployment.

**Test Criteria**:
- [ ] Docker image builds successfully without errors
- [ ] Image size is reasonable (<500MB)
- [ ] Application starts within container
- [ ] Health check endpoint responds (GET /)
- [ ] Environment variables can be passed at runtime
- [ ] Port 10000 is accessible from host

### Tasks

- [ ] T013 Build Docker image with tag `bookrag:latest` using `docker build -t bookrag:latest .` from project root
- [ ] T014 [P] Check Docker image size with `docker images bookrag:latest`
- [ ] T014 [P] Inspect image layers with `docker inspect bookrag:latest`
- [ ] T015 Run container with `docker run -p 10000:10000 bookrag:latest` and verify startup logs
- [ ] T016 Test health endpoint with `curl http://localhost:10000/` while container is running
- [ ] T017 Verify environment variable passthrough by running: `docker run -e DATABASE_URL=postgresql://... -p 10000:10000 bookrag:latest`
- [ ] T018 Stop and remove test container
- [ ] T019 Document Docker build and run commands in `README.md` under "Docker" section

---

## Phase 4: Render Deployment Configuration

**Goal**: Prepare configuration files for Render deployment with proper environment variable management.

**Test Criteria**:
- [ ] `render.yaml` or deployment manifest created
- [ ] Environment variable placeholders documented
- [ ] Health check configuration added
- [ ] Port correctly set to 10000
- [ ] No hardcoded secrets in deployment config

### Tasks

- [ ] T020 Create `render.yaml` in project root with correct service configuration
- [ ] T021 Set service port to 10000 in `render.yaml`
- [ ] T022 Configure health check endpoint as `GET /` in `render.yaml`
- [ ] T023 Document required environment variables in `render.yaml` (DATABASE_URL, QDRANT_URL, OPENROUTER_API_KEY, etc.)
- [ ] T024 Create `.env.example` file documenting all required environment variables with example values
- [ ] T025 Add deployment instructions to `README.md` under "Deployment" section
- [ ] T026 Create startup script `docker-entrypoint.sh` if custom initialization needed, else use uvicorn directly

---

## Phase 5: Polish & Cross-Cutting Concerns

**Goal**: Finalize containerization with logging, security, and documentation.

**Test Criteria**:
- [ ] Docker image passes security scanning (if available)
- [ ] All documentation is complete and accurate
- [ ] Deployment workflow is documented
- [ ] Container graceful shutdown is configured

### Tasks

- [ ] T027 Add security labels to `Dockerfile` (LABEL maintainer, version, etc.)
- [ ] T028 Configure graceful shutdown handling in FastAPI app startup/shutdown events if not already present
- [ ] T029 Add comprehensive README section "Docker & Deployment" with:
  - [ ] Build instructions
  - [ ] Local testing steps
  - [ ] Environment variables required
  - [ ] Render deployment link and steps
- [ ] T030 Create `DEPLOYMENT.md` with troubleshooting guide for common Docker/Render issues
- [ ] T031 Verify `.gitignore` excludes `.env` and `.env.local` files
- [ ] T032 Add GitHub Actions workflow (optional) in `.github/workflows/docker-build.yml` for automated image builds

---

## Dependencies & Execution Order

```
Phase 1: Setup
    ↓
Phase 2: Dockerfile Creation
    ↓
Phase 3: Build & Test
    ↓
Phase 4: Render Configuration
    ↓
Phase 5: Polish & Documentation
```

### Parallel Execution Opportunities

**Phase 2 Parallelization**:
- Tasks T006 (both) can run in parallel - different Dockerfile sections
- Task T007, T008, T009 are sequential (file copy → install → app copy)

**Phase 3 Parallelization**:
- Task T014 (both) can run in parallel - both are inspection tasks after build
- Task T015 and T016 are sequential (run container first, then test)

---

## Implementation Strategy (MVP First)

### MVP Scope (Phase 1-3)
Complete these tasks for a working containerized backend:
1. T001-T004: Setup & .dockerignore
2. T005-T012: Dockerfile creation
3. T013-T018: Build & local testing

**Deliverable**: Runnable Docker image locally, ready for manual Render deployment

### Phase 2 Additions (Phase 4)
Add these tasks for automated Render integration:
1. T020-T026: Render configuration
2. Documentation updates

### Phase 3 Additions (Phase 5)
Add these tasks for production hardening:
1. T027-T032: Security, monitoring, CI/CD

---

## File Paths Summary

| File | Purpose |
|------|---------|
| `Dockerfile` | Production Docker image definition |
| `.dockerignore` | Exclude files from Docker build context |
| `render.yaml` | Render deployment configuration |
| `.env.example` | Example environment variables |
| `README.md` | Updated with Docker instructions |
| `DEPLOYMENT.md` | Deployment guide and troubleshooting |
| `.github/workflows/docker-build.yml` | Optional CI/CD workflow |

---

## Task Count Summary

- **Total Tasks**: 32
- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Dockerfile)**: 8 tasks
- **Phase 3 (Build & Test)**: 7 tasks
- **Phase 4 (Render Config)**: 7 tasks
- **Phase 5 (Polish)**: 6 tasks

- **Parallelizable Tasks**: 6 tasks (marked with [P])
- **Critical Path**: T001 → T005-T012 → T013 → T015 → T020 (19 tasks sequential)

---

## Success Criteria

✅ Docker image builds successfully
✅ Application runs on port 10000 inside container
✅ Health check endpoint accessible
✅ Environment variables configurable at runtime
✅ Documented deployment process for Render
✅ No hardcoded secrets in image or config
✅ All configuration files committed to Git
✅ README and deployment docs complete
