# 🌾 KisanSetu AI

> **AI-Powered Cotton & Groundnut Market Linkage Platform for Gujarat Farmers**
> *IBM Hackathon — Challenge 13*

---

## Problem Statement

Gujarat is a major producer of cotton and groundnut, but farmers face:
- ❌ No real-time mandi price visibility
- ❌ Price exploitation by middlemen
- ❌ Difficulty finding direct buyers
- ❌ Limited bargaining power
- ❌ Uncertainty about when to sell or store

## Solution

KisanSetu AI is an **Agentic AI platform** powered by IBM Granite that helps farmers:

1. 📈 Understand real-time mandi prices
2. 🔮 Forecast price trends (7/14/30 days)
3. 🤝 Find and connect with direct buyers
4. 💡 Decide when to sell vs store
5. 🌾 Assess crop quality via AI
6. 💰 Understand expected income

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Frontend   | Next.js 14, TypeScript, Tailwind CSS, Recharts |
| Backend    | Python 3.11, FastAPI, SQLAlchemy  |
| Database   | PostgreSQL 15                     |
| AI (Phase 2) | IBM Granite (watsonx.ai)        |
| Cloud      | IBM Cloud                         |
| Containers | Docker, docker-compose            |

---

## Project Structure

```
kisansetu-ai/
├── frontend/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx            # Landing page
│   │   ├── login/              # Login page
│   │   ├── register/           # Register page
│   │   ├── farmer/             # Farmer portal
│   │   │   ├── dashboard/      # Main farmer dashboard
│   │   │   ├── market/         # Market prices
│   │   │   ├── buyers/         # Find buyers
│   │   │   ├── advisor/        # Sell or store advisor
│   │   │   ├── quality/        # Crop quality grading
│   │   │   ├── income/         # Income dashboard
│   │   │   └── profile/        # Farmer profile
│   │   ├── buyer/              # Buyer portal
│   │   └── admin/              # Admin panel
│   ├── components/
│   │   ├── ui/                 # Button, Card, Badge
│   │   ├── layout/             # Header, Navigation
│   │   └── dashboard/          # MarketSnapshot, PriceTrendChart, etc.
│   ├── hooks/                  # useLanguage hook
│   ├── lib/                    # api.ts, utils.ts
│   ├── locales/                # en.json, gu.json, hi.json
│   └── types/                  # TypeScript type definitions
│
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── app/
│   │   ├── api/                # Route handlers (market, buyers, farmer)
│   │   ├── agents/             # AI agent placeholders
│   │   ├── ai/                 # IBM Granite integration (Phase 2)
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # demo_data.py service
│   │   └── database/           # DB config, migrate.py
│   └── tests/
│
├── data/
│   └── seed/seed.py            # Database seeding script
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15 (or Docker)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd kisansetu-ai
cp .env.example .env
# Edit .env with your database credentials
```

### 2. Start PostgreSQL

**Option A — Docker (recommended):**
```bash
docker-compose up db -d
```

**Option B — Local PostgreSQL:**
```bash
createdb kisansetu_db
```

---

## Running the Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python app/database/migrate.py

# Seed demo data
python ../data/seed/seed.py

# Start the API server
uvicorn main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000
API docs (Swagger): http://localhost:8000/docs

---

## Running the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

---

## Running with Docker (Full Stack)

```bash
# From project root
docker-compose up --build
```

This starts:
- PostgreSQL at port 5432
- Backend API at port 8000
- Frontend at port 3000

---

## API Documentation

### Health
```
GET /health
```
Returns system status and agent integration status.

### Market Prices
```
GET /api/market/prices?district=Rajkot
GET /api/market/districts
GET /api/market/crops
```

### Buyers
```
GET /api/buyers
GET /api/buyers?crop=cotton
GET /api/buyers/best?crop=cotton
```

### Farmer Dashboard
```
GET /api/farmer/dashboard?district=Rajkot&farmer_name=Rameshbhai+Patel
```

Full interactive docs: http://localhost:8000/docs

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend |
| `IBM_CLOUD_API_KEY` | IBM Cloud API key (Phase 2) |
| `WATSONX_URL` | IBM watsonx.ai endpoint (Phase 2) |
| `WATSONX_PROJECT_ID` | watsonx.ai project ID (Phase 2) |
| `WATSONX_MODEL_ID` | Granite model ID (Phase 2) |

See `.env.example` for full list.

---

## Database Models

| Model | Description |
|-------|-------------|
| `User` | Farmers, buyers, admins with role-based access |
| `FarmerProfile` | Farmer location and land details |
| `Crop` | Farmer's crop listings with quality grades |
| `MarketPrice` | Historical mandi prices per district |
| `Buyer` | Buyer profiles with verification |
| `BuyerRequirement` | Buyer purchase requirements |

---

## Future AI Agent Architecture (Phase 2)

```
AgentOrchestrator
       │
       ├── MandiForecastAgent      → Price trend forecasting (IBM Granite)
       ├── BuyerMatchingAgent      → Semantic buyer-farmer matching
       ├── StorageAdvisorAgent     → Sell vs store recommendations
       ├── QualityGradingAgent     → Crop quality assessment
       └── IncomeDashboardAgent    → Financial projections
                │
                ▼
          IBM Granite (granite-13b-chat-v2)
          IBM watsonx.ai
          IBM Cloud
```

### Phase 2 Plan
- [ ] Integrate IBM watsonx.ai / IBM Granite
- [ ] Implement MandiForecastAgent with 30-day price data
- [ ] Implement BuyerMatchingAgent with semantic matching
- [ ] Implement StorageAdvisorAgent with sell/store decision logic
- [ ] Implement QualityGradingAgent with image analysis
- [ ] Implement IncomeDashboardAgent with financial projections
- [ ] JWT authentication and role-based access
- [ ] Real mandi price API (AgMarkNet / eNAM)
- [ ] SMS/WhatsApp notifications for price alerts
- [ ] Deploy on IBM Cloud

---

## Multilingual Support

KisanSetu AI supports three languages:
- 🇬🇧 English (`en`)
- 🇮🇳 ગુજરાતી / Gujarati (`gu`)
- 🇮🇳 हिन्दी / Hindi (`hi`)

Translations are in `frontend/locales/`. AI-powered translation coming in Phase 2.

---

## Demo Data

All Phase 1 data is **DEMO DATA** and clearly labeled as such in the UI and API.

Supported Gujarat districts:
- Rajkot, Amreli, Junagadh, Bhavnagar, Ahmedabad, Surendranagar, Jamnagar

Supported crops:
- Cotton (Bt Cotton, Desi Cotton)
- Groundnut (Bold, Java)

---

> ⚠️ **This is Phase 1 — Foundation Only.**
> No real market data. No IBM Granite integration yet.
> Phase 2 will implement all AI agents and live data.
