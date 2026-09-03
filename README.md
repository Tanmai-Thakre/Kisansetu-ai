# KisanSetu AI

**AI-Powered Cotton & Groundnut Market Linkage Platform for Gujarat Farmers**

IBM Hackathon — Challenge 13 | Phase 10 (Final) | Version 10.0.0-final

---

## What Is KisanSetu AI?

KisanSetu AI helps Gujarat farmers make informed market decisions. A farmer asks a question in English, Gujarati, or Hindi. Five specialized AI agents analyse market data, find buyers, assess quality, evaluate storage strategies, and calculate income. IBM Granite synthesizes all results into a single, farmer-friendly answer.

```
Farmer Question (English / Gujarati / Hindi)
           ↓
   Agent Orchestrator (Intent Classification)
           ↓
  ┌────────────────────────────────────────┐
  │  Mandi Forecast Agent    (Phase 3)     │
  │  Buyer Matching Agent    (Phase 4)     │
  │  Storage Advisor Agent   (Phase 5)     │
  │  Quality Grading Agent   (Phase 6)     │
  │  Income Dashboard Agent  (Phase 7)     │
  └────────────────────────────────────────┘
           ↓
   Structured JSON Results (grounded data)
           ↓
     IBM Granite (watsonx.ai)
           ↓
  Simple, actionable farmer response
```

Granite **never invents** prices, buyers, forecasts, or income figures.
All numerical facts come from the underlying deterministic agents.

---

## Architecture

```mermaid
graph TD
    subgraph Frontend ["Next.js 15 Frontend"]
        FD[Farmer Dashboard]
        FC[AI Chat Page]
        FQ[Quick Actions]
        DM[Demo Panel]
        Nav[Navigation]
    end

    subgraph Backend ["FastAPI Backend (Python 3.11+)"]
        direction TB
        MAIN[main.py]

        subgraph APIs ["REST API Layer"]
            CHAT[/api/chat]
            ORCH[/api/agents/orchestrate]
            DEMO[/api/demo]
            MKT[/api/market]
            BUY[/api/buyers]
            QUA[/api/quality]
            INC[/api/income]
        end

        subgraph AI ["AI Layer (Phase 8)"]
            ORC[AgentOrchestrator]
            GC[GraniteClient]
            PR[Prompts / Data Grounding]
        end

        subgraph Agents ["Business Logic Agents"]
            A1[MandiForecastAgent]
            A2[BuyerMatchingAgent]
            A3[StorageAdvisorAgent]
            A4[QualityGradingAgent]
            A5[IncomeDashboardAgent]
        end

        DB[(SQLite / PostgreSQL)]
    end

    subgraph IBM ["IBM Cloud"]
        WX[watsonx.ai<br/>IBM Granite 3 8B Instruct]
        IAM[IAM Token Service]
    end

    Frontend --> APIs
    CHAT --> ORC
    ORCH --> ORC
    ORC --> A1 & A2 & A3 & A4 & A5
    ORC --> GC
    GC --> IAM --> WX
    A1 & A2 & A3 & A4 & A5 --> DB
    GC -.->|fallback| PR
```

---

## Project Structure

```
kisansetu-ai/
├── backend/
│   ├── main.py                      # FastAPI app entry point (Phase 10)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── app/
│   │   ├── ai/
│   │   │   ├── granite_client.py    # IBM Granite / watsonx.ai client (Phase 8)
│   │   │   ├── orchestrator.py      # AgentOrchestrator — intent + execution (Phase 8)
│   │   │   └── prompts.py           # Grounded prompt templates (Phase 8+9)
│   │   ├── api/
│   │   │   ├── chat.py              # POST /api/chat  (Phase 8)
│   │   │   ├── agents.py            # POST /api/agents/orchestrate  (Phase 8)
│   │   │   ├── demo.py              # GET/POST /api/demo  (Phase 9)
│   │   │   ├── market.py            # Phases 1–2
│   │   │   ├── buyers.py            # Phase 4
│   │   │   ├── quality.py           # Phase 6
│   │   │   └── income.py            # Phase 7
│   │   ├── agents/
│   │   │   ├── buyer_matching/      # Phase 4
│   │   │   ├── storage_advisor/     # Phase 5
│   │   │   ├── quality/             # Phase 6
│   │   │   └── income/              # Phase 7
│   │   ├── forecasting/             # Phase 3 — Mandi price forecasting
│   │   ├── models/                  # SQLAlchemy models
│   │   ├── schemas/                 # Pydantic schemas
│   │   └── database/                # DB connection, migrations
│   └── tests/
│       ├── test_market_phase2.py    # 45 tests
│       ├── test_market_phase3.py    # Market forecast tests
│       ├── test_market_phase4.py    # Buyer matching tests
│       ├── test_market_phase5.py    # Storage advisor tests
│       ├── test_quality_phase6.py   # Quality grading tests
│       ├── test_income_phase7.py    # Income dashboard tests
│       ├── test_granite_phase8.py   # 48 tests — Granite + orchestrator
│       ├── test_ux_phase9.py        # 38 tests — UX, localization, demo
│       └── test_phase10_final.py    # 44 tests — final regression
│
├── frontend/
│   ├── app/
│   │   ├── farmer/
│   │   │   ├── dashboard/page.tsx   # Main dashboard
│   │   │   ├── chat/page.tsx        # AI Chat page (Phase 8)
│   │   │   ├── buyers/page.tsx      # Buyer matching
│   │   │   ├── quality/page.tsx     # Quality grading
│   │   │   ├── income/page.tsx      # Income dashboard
│   │   │   └── advisor/page.tsx     # Storage advisor
│   │   └── buyer/dashboard/page.tsx
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── AIChatWidget.tsx     # AI chat with agent status (Phase 8+9)
│   │   │   ├── DemoPanel.tsx        # Demo scenario panel (Phase 9)
│   │   │   ├── QuickActions.tsx     # Quick action buttons (Phase 9)
│   │   │   ├── BestBuyerCard.tsx
│   │   │   └── AIRecommendationCard.tsx
│   │   ├── layout/Navigation.tsx    # With AI Chat link
│   │   └── ui/
│   │       ├── DataSourceBadge.tsx  # LIVE / DEMO / ESTIMATE badges (Phase 9)
│   │       └── ResponsibleAINotice.tsx # Responsible AI notice (Phase 9)
│   ├── locales/
│   │   ├── en.json                  # English translations
│   │   ├── gu.json                  # Gujarati translations
│   │   └── hi.json                  # Hindi translations
│   ├── lib/api.ts                   # All API calls (Axios)
│   ├── types/index.ts               # TypeScript types
│   ├── hooks/useLanguage.ts         # Language switcher hook
│   ├── next.config.js               # standalone output for Docker
│   └── Dockerfile
│
├── data/seed/seed.py                # Demo seed data
├── docker-compose.yml
└── .env.example                     # All required environment variables
```

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### 1. Clone & configure

```bash
git clone <repo-url>
cd kisansetu-ai
cp .env.example .env
# Edit .env — add IBM credentials if available (optional for demo mode)
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

API available at: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: http://localhost:3000

### 4. Load demo data (optional)

```bash
cd data/seed
python seed.py
```

---

## Docker Deployment

```bash
# Build and start all services
docker compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Database: PostgreSQL on port 5432
```

### Environment variables for Docker

```bash
# Required for IBM Granite
IBM_API_KEY=your-ibm-cloud-api-key
IBM_PROJECT_ID=your-watsonx-project-id
IBM_GRANITE_MODEL=ibm/granite-3-8b-instruct
IBM_REGION=us-south

# Database
DATABASE_URL=postgresql://kisansetu:kisansetu@db:5432/kisansetu_db

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# CORS (production)
CORS_ORIGINS=https://your-frontend-domain.com
```

Without IBM credentials, the application runs in **deterministic fallback mode** — all agents work normally and structured data is returned without Granite synthesis.

---

## IBM Granite Integration

### Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `IBM_API_KEY` | IBM Cloud IAM API key | — (required for Granite) |
| `IBM_PROJECT_ID` | watsonx.ai project ID | — (required for Granite) |
| `IBM_GRANITE_MODEL` | Model ID | `ibm/granite-3-8b-instruct` |
| `IBM_REGION` | IBM Cloud region | `us-south` |

Legacy names (`WATSONX_URL`, `WATSONX_PROJECT_ID`, `IBM_CLOUD_API_KEY`) are also accepted.

### How Granite is used

Granite handles only **language and reasoning** — never data generation:

| Task | Who does it |
|------|-------------|
| Intent classification | Granite (fallback: keyword heuristic) |
| Final answer synthesis | Granite |
| Multilingual response (en/gu/hi) | Granite |
| Market prices | `MandiForecastAgent` |
| Buyer matching | `BuyerMatchingAgent` |
| Storage advice | `StorageAdvisorAgent` |
| Quality grading | `QualityGradingAgent` |
| Income calculation | `IncomeDashboardAgent` |

### Fallback mode

If IBM Granite is unavailable (no credentials, timeout, rate limit):

1. All five agents still run and return structured data
2. A deterministic rule-based summary is generated in the requested language
3. The response includes `"granite_used": false`
4. The UI shows: *"AI Service Unavailable — Showing rule-based market analysis"*

The application never fabricates data in either mode.

---

## API Reference

### Chat

```
POST /api/chat
```
```json
{
  "message": "Should I sell my cotton now?",
  "language": "en",
  "farmer_id": 1,
  "crop": "cotton",
  "mandi": "Rajkot APMC",
  "quantity": 100.0
}
```
Response:
```json
{
  "answer": "Current price: ₹7,200/q ...",
  "agents_used": ["forecast", "storage"],
  "granite_used": true,
  "data_timestamp": "2024-01-15T10:30:00",
  "confidence": 78
}
```

### Orchestrate

```
POST /api/agents/orchestrate
```
```json
{
  "farmer_id": 1,
  "message": "Find the best buyer and tell me whether I should sell now.",
  "language": "en",
  "crop": "cotton",
  "mandi": "Rajkot APMC",
  "quantity": 100.0
}
```
Response:
```json
{
  "agents_used": ["buyer", "forecast", "storage"],
  "failed_agents": [],
  "results": { "buyer": {}, "forecast": {}, "storage": {} },
  "final_answer": "...",
  "confidence": 75,
  "granite_used": false
}
```

### Demo

```
GET  /api/demo/farmer           — Returns pre-configured demo farmer profile
POST /api/demo/run              — Runs full complex scenario (all 4 agents)
```
```json
{ "language": "en" }   // "en", "gu", or "hi"
```

### Other endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check with version and agent status |
| `GET /api/market/prices/latest?crop=cotton` | Current market prices |
| `GET /api/buyers/matches?crop=cotton` | Buyer matching |
| `GET /api/agents/storage-advisor/preview` | Storage advice |
| `GET /api/agents/income/preview` | Income estimate |
| `GET /api/chat/status` | Granite availability status |

---

## Intent Routing

| Intent | Keywords | Agents invoked |
|--------|----------|----------------|
| `PRICE` | price, rate, mandi | forecast |
| `FORECAST` | forecast, predict, will price | forecast |
| `BUYER` | buyer, who buy, find buyer | buyer |
| `SELL_OR_STORE` | sell now, store, wait, hold | storage, forecast |
| `QUALITY` | quality, grade, test | quality |
| `INCOME` | income, earn, profit, how much | income, forecast, buyer |
| `COMPLEX` | multiple aspects | forecast, buyer, storage, income |
| `GENERAL` | anything else | storage, forecast |

Complex queries (3+ aspects) trigger all four main agents in one pass, with a single Granite call for synthesis.

---

## Language Support

Three languages are fully supported throughout:

| Language | Code | Script |
|----------|------|--------|
| English | `en` | Latin |
| Gujarati | `gu` | ગુજરાતી |
| Hindi | `hi` | हिन्दी |

Numerical values are always in digits (₹7,200), never spelled out.
Granite generates the explanation in the requested language; the backend agents return language-agnostic JSON.

---

## Demo Flow

A pre-configured cotton farmer scenario is available without any manual setup:

1. Open http://localhost:3000/farmer/dashboard
2. Click **Load Demo** in the Demo Panel
3. Click **Run Full Analysis**
4. View results in English, Gujarati, or Hindi

The demo invokes all four main agents and asks:

> *"I have 100 quintals of cotton in Rajkot. Find the best buyer, predict the price for the next 15 days, tell me whether I should sell or store, and estimate my income."*

Expected response fields:
- Current market price
- 15-day price forecast
- Best buyer name and offer
- Sell/store recommendation
- Expected net income
- Risk level and confidence
- One-line disclaimer

---

## Tests

```bash
cd kisansetu-ai/backend

# All 303 tests
python -m pytest tests/ -v

# Individual phases
python -m pytest tests/test_granite_phase8.py -v   # 48 tests
python -m pytest tests/test_ux_phase9.py -v        # 38 tests
python -m pytest tests/test_phase10_final.py -v    # 44 tests
```

| Test file | Tests | What it covers |
|-----------|-------|----------------|
| test_market_phase2.py | 45 | Market data, prices, forecasting |
| test_quality_phase6.py | ~20 | Quality grading agent |
| test_income_phase7.py | ~35 | Income dashboard agent |
| test_granite_phase8.py | 48 | Granite client, orchestrator, intent routing, grounding |
| test_ux_phase9.py | 38 | Translations, demo API, responsible AI, navigation |
| test_phase10_final.py | 44 | Health, backward-compat, exception handler, security, CORS, fallback |

---

## Responsible AI

KisanSetu AI follows these principles:

1. **No invented data** — Granite only references data supplied in the structured prompt
2. **Transparent uncertainty** — Forecasts are labelled `ESTIMATE`, not fact
3. **No profit guarantees** — System never guarantees profit
4. **Data source labelling** — UI shows `LIVE` / `DEMO` / `ESTIMATE` badges
5. **Fallback transparency** — Users are told when AI synthesis is unavailable
6. **No credential exposure** — IBM API keys are server-side only; never returned in API responses
7. **Agent failure disclosure** — If an agent fails, the response notes which data is unavailable

---

## Security

- IBM API keys loaded from environment variables, never hardcoded
- CORS restricted to configured origins (`CORS_ORIGINS` env var)
- Global exception handler prevents stack trace leakage (500 → generic JSON)
- Pydantic validation on all inputs (422 on bad data)
- Farmer data scoped to authenticated user via `farmer_id`
- System prompts never returned in API responses
- No credentials stored in frontend bundle

---

## Known Limitations / Issues

- **Python 3.14 deprecation warnings** — `datetime.utcnow()` is deprecated in 3.12+; does not affect functionality
- **Pydantic V2 config warnings** — Legacy `class Config` style in some schemas; does not affect functionality
- **httpx2 recommendation** — `starlette.testclient` suggests using `httpx2`; tests still pass with `httpx`
- **No real-time market data** — Uses synthetic data in demo mode; connect a live AGMARKNET/eNAM API key for production
- **Image upload quality grading** — Phase 6 quality agent supports manual parameter mode; image-based grading requires a vision model (future work)
- **Voice input** — Placeholder UI exists; not yet functional

---

## Recommended Next Steps (Phase 11+)

1. **Live market data** — Integrate AGMARKNET / eNAM / commodity exchange APIs
2. **Real farmer auth** — Add OTP/Aadhaar-based authentication
3. **Push notifications** — Alert farmers when prices hit target thresholds
4. **Image-based quality** — Integrate a vision model for cotton/groundnut image assessment
5. **Voice input** — Add speech-to-text (Web Speech API / Whisper) for low-literacy farmers
6. **Offline PWA** — Service worker caching for rural low-connectivity use
7. **IBM Code Engine deployment** — Full production deployment on IBM Cloud
8. **A/B testing** — Compare Granite vs rule-based recommendations for farmer outcomes

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| AI / LLM | IBM Granite 3 8B Instruct (watsonx.ai) |
| Backend | FastAPI 0.115, Python 3.11+ |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Next.js 15, React 19, TypeScript |
| Styling | Tailwind CSS |
| Charts | Recharts |
| HTTP client | Axios (frontend), httpx (backend) |
| Containerisation | Docker, Docker Compose |
| Testing | pytest, FastAPI TestClient |

---

## License

MIT — See LICENSE file for details.

---

*KisanSetu AI — Connecting Farmers to Markets with IBM AI*
