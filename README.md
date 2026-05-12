# 🌍 Universal Energy RAG Framework
### Standardized AI Analyst for Structured Grid Data & Unstructured Documentation

This project is a modular **Retrieval-Augmented Generation (RAG) Framework** designed to bridge the gap between real-time energy grid data (Numbers) and complex energy policy documentation (Words).

Unlike standard chatbots, this system is **source-agnostic** and **intent-aware**, optimized for local inference (Ollama) with a focus on low latency and architectural precision.

---

## 🏗️ Core Architecture: The Provider Pattern

The system is built on a **Modular Provider Architecture**, allowing it to be adapted to any energy data source or document set.

### 1. Data Providers (`app/providers/data/`)
Handles **Structured Data** (APIs, SQL, IoT).
*   **Standardized Interface**: Every source follows a unified contract (`BaseDataProvider`).
*   **Active Source**: Currently implemented for **RTE France (eco2mix)**.
*   **Plug-and-Play**: Easily add new sources (SolarEdge, Home Assistant, etc.) without touching the RAG logic.

### 2. Knowledge Providers (`app/providers/knowledge/`)
Handles **Unstructured Information** (PDFs, Whitepapers, Web Search).
*   **Vector RAG**: Performs semantic search across energy reports and policy documents.
*   **Hybrid Blend**: Allows the LLM to explain *why* data is moving based on historical or strategic context found in documents.

### 3. The Context Dispatcher (`app/core/dispatcher.py`)
The "Hub" of the system. It analyzes user queries and orchestrates the retrieval:
*   **Data vs. Knowledge**: Automatically decides which providers to consult.
*   **Multi-Source Merging**: Combines different streams into a single, clean context for the LLM.

---

## 🧠 Advanced Features

### ⚡ Temporal & Topic Intent Parsing
*   **Temporal Logic**: Automatically detects time ranges ("now", "yesterday", "last 7 days") and retrieves only the relevant data layers.
*   **Topic Focus**: Identifies specific metrics in the query (Nuclear, Wind, CO2) and injects "Focus Hints" into the prompt to ensure concise, expert-level answers.
*   **Hybrid Keywords**: Uses a micro-latency keyword fast-path for common queries to avoid unnecessary LLM calls.

### 💾 Data-Aware Caching
*   **Smart Invalidation**: Responses are cached based on a hash of the query and the current data version.
*   **Data Freshness**: The cache is automatically invalidated the moment a new record is detected in the data source.

### 📝 Observability & Logging
*   **Detailed Analytics**: Every query is logged in NDJSON format with metrics for latency (ms), cache hit/miss, and layers retrieved.
*   **Performance Monitoring**: Built-in support for P95 latency tracking and layer usage statistics.

---

## 🚀 Technical Stack
*   **LLM Orchestration**: LangChain + Ollama (optimized for local CPU inference).
*   **Database**: SQLite (Time-series optimization).
*   **Backend**: FastAPI.
*   **Logic**: Python 3.10+ with asynchronous retrieval.

---

## 🛠️ Getting Started

### 1. Setup Environment
```bash
pip install -r requirements.txt
```

### 2. Configure Providers
Edit `app/tools/rag_pipeline.py` to add or remove data/knowledge providers in the `ContextDispatcher`.

### 3. Run the Analyst
```bash
python run_api.py
```

---

## 📊 Roadmap
- [ ] **Vector Store Integration**: Fully wire the PDF knowledge provider to a local ChromaDB/FAISS instance.
- [ ] **Anomaly Detection**: Add an automated layer to flag grid anomalies before the LLM step.
- [ ] **Forecast Layer**: Enable predictive analysis using D-1 forecast data.

---
*Built for the Energy Transition.* ⚡🌿
