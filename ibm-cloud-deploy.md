# KisanSetu AI — IBM Cloud Deployment Guide

**Platform:** IBM Cloud Code Engine (recommended) or IBM Cloud Kubernetes Service  
**Version:** 10.0.0-final

---

## Prerequisites

1. [IBM Cloud CLI](https://cloud.ibm.com/docs/cli) installed and logged in
2. IBM Cloud Container Registry (ICR) access
3. IBM Code Engine project created
4. PostgreSQL on IBM Cloud Databases for PostgreSQL
5. watsonx.ai project (for IBM Granite)

```bash
# Install IBM Cloud CLI plugins
ibmcloud plugin install code-engine
ibmcloud plugin install container-registry

# Login
ibmcloud login --apikey YOUR_IBM_CLOUD_API_KEY -r us-south
ibmcloud cr login
```

---

## 1. Container Registry Setup

```bash
# Create a namespace in IBM Container Registry
ibmcloud cr namespace-add kisansetu

# Tag and push images
# Backend
docker build -t us.icr.io/kisansetu/backend:v10 ./backend
docker push us.icr.io/kisansetu/backend:v10

# Frontend (set API URL to your backend Code Engine app URL)
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://kisansetu-backend.YOUR-HASH.us-south.codeengine.appdomain.cloud \
  -t us.icr.io/kisansetu/frontend:v10 ./frontend
docker push us.icr.io/kisansetu/frontend:v10
```

---

## 2. Code Engine Project

```bash
# Select or create Code Engine project
ibmcloud ce project create --name kisansetu-ai
ibmcloud ce project select --name kisansetu-ai
```

---

## 3. Secrets & ConfigMaps

```bash
# Create backend secrets (never put these in source code)
ibmcloud ce secret create --name kisansetu-secrets \
  --from-literal IBM_API_KEY=YOUR_WATSONX_API_KEY \
  --from-literal IBM_PROJECT_ID=YOUR_WATSONX_PROJECT_ID \
  --from-literal DATABASE_URL=postgresql://user:pass@host:5432/kisansetu_db \
  --from-literal SECRET_KEY=your-random-32-char-secret-key

# Create configmap for non-sensitive config
ibmcloud ce configmap create --name kisansetu-config \
  --from-literal IBM_GRANITE_MODEL=ibm/granite-3-8b-instruct \
  --from-literal IBM_REGION=us-south \
  --from-literal MARKET_DATA_PROVIDER=demo \
  --from-literal ACCESS_TOKEN_EXPIRE_MINUTES=1440 \
  --from-literal JWT_ALGORITHM=HS256
```

---

## 4. Deploy Backend

```bash
ibmcloud ce application create \
  --name kisansetu-backend \
  --image us.icr.io/kisansetu/backend:v10 \
  --registry-secret icr-secret \
  --port 8000 \
  --cpu 1 \
  --memory 2G \
  --min-scale 1 \
  --max-scale 3 \
  --env-from-secret kisansetu-secrets \
  --env-from-configmap kisansetu-config \
  --env CORS_ORIGINS=https://kisansetu-frontend.YOUR-HASH.us-south.codeengine.appdomain.cloud

# Get backend URL
ibmcloud ce application get --name kisansetu-backend --output url
# → https://kisansetu-backend.YOUR-HASH.us-south.codeengine.appdomain.cloud
```

---

## 5. Deploy Frontend

```bash
# Update CORS_ORIGINS in backend with the actual frontend URL first, then:
ibmcloud ce application create \
  --name kisansetu-frontend \
  --image us.icr.io/kisansetu/frontend:v10 \
  --registry-secret icr-secret \
  --port 3000 \
  --cpu 0.5 \
  --memory 1G \
  --min-scale 1 \
  --max-scale 2 \
  --env NODE_ENV=production \
  --env NEXT_PUBLIC_API_URL=https://kisansetu-backend.YOUR-HASH.us-south.codeengine.appdomain.cloud
```

---

## 6. IBM Cloud Databases for PostgreSQL

```bash
# Create PostgreSQL instance (Lite tier available for hackathon)
ibmcloud resource service-instance-create kisansetu-postgres \
  databases-for-postgresql standard us-south

# Get connection credentials
ibmcloud cdb deployment-connections kisansetu-postgres

# Update the DATABASE_URL secret with the actual connection string:
ibmcloud ce secret update --name kisansetu-secrets \
  --from-literal DATABASE_URL=postgresql://ibm_admin:PASSWORD@HOST:PORT/ibmclouddb?sslmode=require
```

---

## 7. Verify Deployment

```bash
# Health check
curl https://kisansetu-backend.YOUR-HASH.us-south.codeengine.appdomain.cloud/health

# Expected response:
# { "status": "ok", "version": "10.0.0-final", "ibm_granite": { "available": true } }

# Run demo
curl -X POST https://kisansetu-backend.YOUR-HASH.us-south.codeengine.appdomain.cloud/api/demo/run \
  -H "Content-Type: application/json" \
  -d '{"language":"en"}'
```

---

## 8. Update CORS After Both Apps Are Running

```bash
FRONTEND_URL="https://kisansetu-frontend.YOUR-HASH.us-south.codeengine.appdomain.cloud"
BACKEND_URL="https://kisansetu-backend.YOUR-HASH.us-south.codeengine.appdomain.cloud"

ibmcloud ce application update \
  --name kisansetu-backend \
  --env CORS_ORIGINS="${FRONTEND_URL},http://localhost:3000"
```

---

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `IBM_API_KEY` | ✅* | — | IBM Cloud IAM API key |
| `IBM_PROJECT_ID` | ✅* | — | watsonx.ai project ID |
| `IBM_GRANITE_MODEL` | No | `ibm/granite-3-8b-instruct` | Granite model ID |
| `IBM_REGION` | No | `us-south` | IBM Cloud region |
| `SECRET_KEY` | ✅ | — | JWT signing key (min 32 chars) |
| `CORS_ORIGINS` | ✅ | `http://localhost:3000` | Comma-separated allowed origins |
| `NEXT_PUBLIC_API_URL` | ✅ | `http://localhost:8000` | Backend URL (baked at build) |
| `MARKET_DATA_PROVIDER` | No | `demo` | `demo` or `live` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | JWT TTL |

*Required for IBM Granite; app works in fallback mode without these.

---

## Local Docker Compose (for testing production-like setup)

```bash
cd kisansetu-ai

# Copy and fill in environment
cp .env.example .env
# Edit .env with your IBM credentials (optional for demo mode)

# Build and start all services
docker compose up --build

# Services:
#   Frontend:  http://localhost:3000
#   Backend:   http://localhost:8000
#   DB:        postgresql://localhost:5432
```

---

## Hackathon Demo Mode (no IBM credentials required)

The application runs fully in **deterministic fallback mode** without any IBM credentials:
- All five agents work and return structured data
- Deterministic rule-based analysis replaces Granite synthesis
- The UI clearly shows "AI Service Unavailable — Showing rule-based market analysis"
- All demo data is clearly labelled as DEMO / ESTIMATE

```bash
# Minimum viable run (SQLite, no PostgreSQL, no IBM credentials):
cd kisansetu-ai/backend
pip install -r requirements.txt
uvicorn main:app --port 8000

# Then:
cd ../frontend
npm install && npm run dev
# → http://localhost:3000
```
