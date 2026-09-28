# ⚡ Energy AI Factory — Universal Energy Transition Assistant

> **An intelligent, source-agnostic energy data orchestration and RAG intelligence platform** helping stakeholders accelerate the clean energy transition, optimize efficiency, and lower carbon footprints.

---

## 🌟 Vision & Overview

Energy data is fragmented across proprietary vendor APIs (Solar, Wind, BESS), SCADA systems, IoT sensors, local databases, and policy/regulatory documents. 

**Energy AI Factory** unifies these heterogeneous streams into a **Universal Internal Energy Schema (15 metrics)**. It allows enterprises to dynamically connect any source, optionally persist time-series data or stream in live-only mode, and leverage LLM-driven RAG pipelines for real-time telemetry analysis, predictive forecasting, and strategic decision-making.

---

## 🏛️ System Architecture

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           Data & Knowledge Ingestion                   │
  │                                                                        │
  │  [REST APIs]         [IoT / SCADA]         [SQL DBs]      [Documents]  │
  │  (Solar, Wind, Grid) (Sensors, MQTT)       (Timescale/PG) (PDF/Reports)│
  └───────┬────────────────────┬───────────────────┬──────────────┬────────┘
          │                    │                   │              │
          ▼                    ▼                   ▼              │
  ┌────────────────────────────────────────────────┐              │
  │         Dynamic Field Mapping Engine           │              │
  │    (Raw Vendor Metrics ➔ Universal Schema)     │              │
  └───────────────────────┬────────────────────────┘              │
                          │                                       │
            ┌─────────────┴──────────────┐                        │
            ▼                            ▼                        ▼
  [Live-Only Mode]             [SQLite / Time-Series]     [Vector Store RAG]
  (Zero storage stream)        (Multi-tenant DB storage)  (Chroma / FAISS)
            │                            │                        │
            └─────────────┬──────────────┘                        │
                          ▼                                       │
            ┌──────────────────────────────────────────────┐      │
            │          Smart Context Dispatcher            │◄─────┘
            │  - Intent & Temporal Parsing (LangChain)     │
            │  - Dynamic Context Injection & Layering      │
            └─────────────────────┬────────────────────────┘
                                  ▼
            ┌──────────────────────────────────────────────┐
            │          LLM Intelligence Agent              │
            │   (Local Ollama / Mistral / Qwen / Llama)    │
            └─────────────────────┬────────────────────────┘
                                  ▼
            ┌──────────────────────────────────────────────┐
            │             Modern React Frontend            │
            │  - Mission Control Dashboard                 │
            │  - Intelligent Multi-Source Onboarding       │
            │  - Enterprise Data Sovereignty & Settings    │
            │  - Interactive AI Energy Analyst Chat        │
            └──────────────────────────────────────────────┘
```

---

## ⚡ Universal Internal Energy Schema

Every external payload is dynamically mapped into our 15 standardized metrics:

| Metric | Field Key | Unit | Description |
|---|---|---|---|
| **Demand** | `consumption_mw` | MW | Total energy consumption / system load |
| **Solar Generation** | `solar_mw` | MW | Solar PV production |
| **Wind Generation** | `wind_mw` | MW | Wind turbine output |
| **Hydro Generation** | `hydro_mw` | MW | Hydroelectric plant production |
| **Gas Generation** | `gas_mw` | MW | Natural gas / CCGT output |
| **Nuclear Generation** | `nuclear_mw` | MW | Nuclear power generation |
| **Biomass Generation** | `biomass_mw` | MW | Bioenergy and waste-to-energy output |
| **Battery Storage** | `storage_mw` | MW | Battery/pumped storage (+ charge / - discharge) |
| **Grid Exchanges** | `grid_exchange_mw` | MW | Cross-border physical imports/exports |
| **Carbon Intensity** | `carbon_intensity_g_kwh` | g/kWh | Lifecycle carbon intensity |
| **Total Production** | `total_production_mw` | MW | Aggregate generation across all units |
| **Installed Capacity** | `capacity_mw` | MW | Rated capacity |
| **Availability** | `availability_pct` | % | % of capacity online and dispatchable |
| **Peak Demand** | `peak_load_mw` | MW | Maximum recorded load in the period |
| **Forecast** | `forecast_mw` | MW | Day-ahead generation / demand forecast |

---

## 🚀 Key Capabilities

### 1. 🔌 Multi-Modal Source Integration
* **Dynamic REST APIs**: Connect any vendor API. Supports custom authentication headers (`Authorization`, API keys).
* **SCADA & Databases**: Dedicated `DynamicDBProvider` for SQLite, PostgreSQL, TimescaleDB, or InfluxDB with custom queries.
* **Knowledge RAG**: Semantic vector retrieval over energy policy papers, regulatory docs, and PDFs via `PDFKnowledgeProvider`.
* **Zero-Friction Discovery**: Automatic endpoint field scanning (`/sources/discover`) that heuristically suggests field mappings.

### 2. 🛡️ Data Sovereignty & Persistence Control
* **Flexible Storage**: Toggle `persist_data` per source.
  * **Persisted**: Stored in isolated tables for historical charts, trends, and baselines.
  * **Live-Only**: Transformed in-memory and injected directly into LLM context without DB storage.
* **Multi-Tenant Isolation**: Hard isolation via `company_id` for enterprise security.

### 3. 🧠 Smart RAG Dispatcher & Agents
* **Temporal & Intent Parsing**: Parses natural language expressions ("today's peak", "last 7 days solar vs wind", "yesterday vs now") to query only relevant time slices.
* **Topic Focus Injection**: Selects optimal data layers (realtime, today, 7-day baseline, policy knowledge) before prompt formulation.
* **Data-Aware Response Caching**: MD5 query hashing with instant invalidation upon new telemetry ingestion.

### 4. 💻 Full-Stack Web Application (`ecobot-app`)
* **Interactive Onboarding**: Step-by-step wizard to register company, connect the first telemetry stream, auto-scan fields, and map to the universal schema.
* **Mission Control Dashboard**: Live load tracking, renewable mix area charts, CO₂ savings counters, and source status indicators.
* **Enterprise Settings & Health Monitor**: Real-time connection testing (`Online`/`Offline`), source pausing/enabling, and deletion.
* **AI Energy Analyst Chat**: Real-time conversation with conversation history and deep insight generation.

---

## 🛠️ Tech Stack

* **Backend**: FastAPI, Python 3.10+, Uvicorn, SQLite, SQLAlchemy, Pydantic v2
* **AI / RAG**: LangChain, Ollama (local offline models), ChromaDB/FAISS
* **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons, Redux Toolkit Query
* **Telemetry Simulator**: Built-in FastAPI mock server (`mock_server.py`) mimicking vendor APIs (Solar, Wind, Grid SCADA)

---

## 🏁 Quickstart Guide

### 1. Prerequisites
* Python 3.10+ (Conda recommended)
* Node.js 18+ & npm
* [Ollama](https://ollama.ai/) running locally (e.g. `ollama run mistral` or `qwen2.5`)

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/HalimDeboub/energy-factory.git
cd energy-factory

# Create and activate environment
conda create -n energy-ai python=3.10 -y
conda activate energy-ai

# Install dependencies
pip install -r requirements.txt

# Start the mock telemetry server (port 9001, optional for testing)
python mock_server.py

# Start the FastAPI backend (port 9000)
python -m app.fast_api
```

### 3. Frontend Setup
```bash
cd ecobot-app
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Testing with Mock Telemetry

A built-in mock telemetry server (`mock_server.py`) runs at `http://localhost:9001` and simulates realistic non-standard vendor APIs:
* **All-in-One**: `http://127.0.0.1:9001/api/sources/combined`
* **Solar Plant**: `http://127.0.0.1:9001/api/sources/solar-farm`
* **Wind Fleet**: `http://127.0.0.1:9001/api/sources/wind-farm`
* **Grid SCADA**: `http://127.0.0.1:9001/api/sources/grid-scada`

Enter any of these URLs in the **Onboarding** or **Settings > Connect Source** modal to test field discovery and schema mapping.

---

## 📈 Roadmap

- [x] Multi-tenant universal schema architecture (15 metrics)
- [x] Dynamic API & Database provider layer with custom auth
- [x] Heuristic field scanner & automated mapping UI
- [x] Real-time connection testing & health check dashboard
- [ ] Automated anomaly detection & alert dispatch (Slack / Webhook)
- [ ] Multi-document vector embedding pipeline with auto-sync
- [ ] Exportable ESG compliance and decarbonization PDF reports

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
