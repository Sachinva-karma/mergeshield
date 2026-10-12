# 🛡️ MergeShield

> **Evidence-Backed PR Risk Intelligence & Diff Grounding**  
> An open-source, automated auditor for public GitHub Pull Requests powered by hosted open-weight models.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![React + Vite](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61dafb.svg)](https://vitejs.dev)

---

## 🎯 Product Overview

MergeShield ingests a public GitHub Pull Request URL, fetches its live metadata and bounded diff using the GitHub REST API, and uses an open-weight foundation model to produce a structured, evidence-grounded risk audit.

### Core User Flow
1. **Paste URL**: User enters a public GitHub PR link (e.g. `https://github.com/fastapi/fastapi/pull/11000`).
2. **Fetch & Bound**: Backend validates the URL and fetches PR title, description, modified files, and diff. Diffs are strictly bounded (by line and byte limits) to eliminate token exhaustion and latency spikes.
3. **Open-Weight Analysis**: A hosted open-weight model analyzes the code changes with strict grounding prompts.
4. **Evidence Grounding Verification**: The diff parser validates that cited snippets and lines actually exist in the retrieved diff. Any ungrounded or hallucinated lines are flagged as unverified caveats.
5. **Interactive Risk Report**: The app presents overall risk level (`HIGH`, `MEDIUM`, `LOW`), technical explanations, explicit uncertainty boundaries, supporting verbatim code excerpts, and actionable verification tests.

---

## 🤖 Model & Provider Information

| Property | Details |
| :--- | :--- |
| **Default Model** | `llama-3.3-70b-versatile` |
| **Alternative Fast Model** | `llama-3.1-8b-instant` |
| **Default Hosted Provider** | [Groq Cloud](https://groq.com) |
| **Alternative Providers** | [OpenRouter](https://openrouter.ai), [Together AI](https://together.ai), or any OpenAI-compatible API (`OPENAI_BASE_URL`) |
| **Model License** | [Meta Llama 3.3 Community License](https://github.com/meta-llama/llama-models/blob/main/models/llama3_3/LICENSE) (Open Weights) |
| **Application License** | [MIT License](LICENSE) (Permissive Open Source) |

---

## 📐 Architecture

```
┌────────────────────────────────┐
│      React + Vite Frontend     │
│   (Port 5173 / Proxy to /api)  │
└───────────────┬────────────────┘
                │ HTTP POST /api/analyze
┌───────────────▼────────────────┐
│      FastAPI Backend (Py 3.11) │
│                                │
│  ┌───────────────────────────┐ │
│  │     GitHub PR Client      │─┼──► GitHub REST API (Public PRs)
│  │   (URL parser & bounder)  │ │    Auto-detects gh auth or GITHUB_TOKEN
│  └─────────────┬─────────────┘ │
│                │ Bounded Diff  │
│  ┌─────────────▼─────────────┐ │
│  │        Diff Parser        │ │
│  │  (Hunk/line ground truth) │ │
│  └─────────────┬─────────────┘ │
│                │ Grounding Map │
│  ┌─────────────▼─────────────┐ │
│  │    Model Adapter Engine   │─┼──► Groq / OpenRouter / Together API
│  │  (Strict JSON + Grounding)│ │    Hosted Open-Weight Models
│  └───────────────────────────┘ │
└────────────────────────────────┘
```

---

## 🚀 Quickstart & Setup Requirements

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** and **npm**
- (Optional) **GitHub CLI (`gh`)** or `GITHUB_TOKEN` for higher GitHub rate limits.

### 1. Clone & Environment Configuration
```bash
git clone https://github.com/Sachinva-karma/mergeshield.git
cd mergeshield

# Copy environment template
cp .env.example .env
```

Edit `.env` and set your model provider API key:
```env
MODEL_PROVIDER=groq
MODEL_NAME=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run backend server (Port 8000)
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## 🧪 Testing & Verification

Run the automated backend test suite:
```bash
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests -v
```

All 8 tests verify:
- GitHub PR URL validation and redirect handling
- Diff size and line bounding
- Unified diff hunk parsing
- Evidence grounding and hallucination detection
- Error reporting when provider keys are omitted

---

## 🔒 Security & Grounding Guarantees
- **No Repository Code Execution**: Code from PRs is analyzed statically and never executed.
- **Read-Only**: MergeShield requests no GitHub write permissions, creates no commits, and merges no code.
- **Strict Grounding**: Cited lines and code snippets are cross-checked against actual retrieved diff hunks. If a model cites non-existent code, it is flagged as unverified.
- **Zero Hallucinated Findings**: If no provider credentials are configured, the app returns a clear 503 setup guide rather than fake mock findings.
