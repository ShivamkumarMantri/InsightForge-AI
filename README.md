<div align="center">

# ⚡ InsightForge AI

**Next-Generation Conversational Data Intelligence Workspace**

*Transform complex datasets into interactive visualizations and executive insights through safe, agentic natural language analysis.*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.x-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.x-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%20/%20Pro-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

</div>

---

## 📖 Overview

**InsightForge AI** is an enterprise-ready AI analyst platform designed to bridge raw tabular data (CSV, XLSX, XLS) and high-impact decision making. Rather than relying on static dashboards or blindly executing untrusted LLM-generated code, InsightForge AI pairs a structured **Google Gemini** reasoning agent with a deterministic, **sandboxed Pandas execution engine**.

Users can upload datasets of any size, explore automatic data health profiling, ask natural language analytical questions, drill down into comparative and driver analyses, and instantly export executive reports.

---

## ✨ Key Features

- 📊 **Automated Dataset Intelligence & Profiling**
  - Instant summary metrics: column classifications, data types, missing value ratios, and cardinality.
  - Automated detection of key dimensions and numeric metrics.
  - Zero-effort initial dataset health and distribution overview.

- 💬 **Conversational AI Analyst**
  - Multi-turn context preservation for fluid data exploration.
  - Generates structured, deterministic analysis plans rather than raw, unsafe shell commands.
  - Dynamic, context-aware follow-up suggestion cards to guide deep analytical exploration.

- 🛡️ **Guarded & Sandboxed Safe Execution**
  - Sandboxed AST-validated Pandas / NumPy analytical execution layer.
  - Strict blocking of dangerous builtins (`eval`, `exec`, `os`, `sys`, file system access, network calls).
  - Robust exception handling and graceful fallback pipelines.

- 📈 **Dynamic Reactive Visualizations**
  - Automatic chart recommendation based on analytical intent (bar, line, area, composed charts).
  - Responsive charts rendered with Recharts and customized styling.
  - Interactive tooltips, data legends, and summary badges.

- 📄 **Executive Reporting & Export**
  - One-click export for datasets, analysis summaries, and formatted reports.
  - Client-side and server-side export options.

---

## 🏗️ System Architecture

```text
                             ┌────────────────────────┐
                             │    React 18 Frontend   │
                             │  Vite + Modern UI/CSS  │
                             └───────────┬────────────┘
                                         │ REST API
                                         ▼
                             ┌────────────────────────┐
                             │    FastAPI Gateway     │
                             │  CORS • Rate Limit     │
                             └───────────┬────────────┘
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
      ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
      │  Dataset Profiler   │ │  Gemini AI Analyst  │ │    Safe Executor    │
      │   Summary & Schema  │ │  Plan & Suggestions │ │  Sandboxed Pandas   │
      └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         ▼
                             ┌────────────────────────┐
                             │ Result Data + Payload  │
                             │ Chart Spec & Insights  │
                             └────────────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Modern, responsive CSS design system with glassmorphism & dark-mode aesthetics
- **Charts & Visuals**: Recharts
- **Icons**: Lucide React
- **Sanitization**: DOMPurify

### Backend
- **Framework**: Python 3.11+, FastAPI
- **Data Engine**: Pandas, NumPy
- **AI / LLM**: Google Gemini (`gemini-2.5-flash` / configurable)
- **Validation**: Pydantic v2
- **Server**: Uvicorn

### DevOps & Infrastructure
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Multi-stage production container builds

---

## 📁 Repository Structure

```text
InsightForge_AI/
├── backend/
│   ├── app/
│   │   ├── agents/          # Gemini analyst & conversational context manager
│   │   ├── api/             # FastAPI routers (upload, profile, analyze, chat, export)
│   │   ├── core/            # Logging, security guardrails, custom error handlers
│   │   ├── data/            # In-memory and transient dataset storage
│   │   ├── execution/       # Sandboxed Pandas executor with AST verification
│   │   ├── models/          # Pydantic schemas and analysis plan contracts
│   │   ├── services/        # Automated profiling, insights, report generator
│   │   └── main.py          # FastAPI application entrypoint & lifespan
│   ├── Dockerfile
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components (Chat, Dashboard, Visualizations, etc.)
│   │   ├── utils/           # Export helpers and formatting utilities
│   │   ├── App.jsx          # Main application workflow
│   │   ├── main.jsx         # Vite entrypoint
│   │   └── styles.css       # Design tokens, gradients, and custom themes
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── sample_data/
│   └── sales.csv            # Sample dataset for immediate testing
├── docs/
│   ├── ARCHITECTURE.md      # Deep dive into execution boundaries & safety
│   └── NEXT_STEPS.md        # Feature roadmap & extension ideas
├── docker-compose.yml       # Full stack container configuration
├── .env.example             # Template for required environment variables
├── .gitignore               # Strict exclusion of secrets, keys, and dependencies
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- [Node.js](https://nodejs.org/) (v18 or higher)
- [Python](https://www.python.org/) (v3.11 or higher)
- [Google Gemini API Key](https://aistudio.google.com/)

---

### Method 1: Local Development

#### 1. Clone the Repository
```bash
git clone https://github.com/ShivamkumarMantri/InsightForge-AI.git
cd InsightForge-AI
```

#### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your configuration:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
MAX_UPLOAD_MB=25
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

#### 3. Backend Setup
```bash
cd backend
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000`. Interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

#### 4. Frontend Setup
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Frontend workspace will be live at `http://localhost:5173`.

---

### Method 2: Docker Compose

Spin up the entire stack with a single command:
```bash
docker-compose up --build
```
- Access the web interface: `http://localhost:5173`
- Access the backend API: `http://localhost:8000`

---

## 🔒 Security & Privacy

- **No Remote Code Execution**: The executor operates with a restricted AST whitelist and forbids unsafe imports, arbitrary shell execution, and filesystem write access.
- **Credential Protection**: API keys and secrets reside strictly in server-side environment variables and are never forwarded to the client.
- **Ephemeral Dataset Lifecycle**: Datasets uploaded during sessions are purged automatically after a configurable TTL.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
