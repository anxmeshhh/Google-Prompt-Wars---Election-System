# ElectaVerse 🗳️⚡

### AI-Powered Election Intelligence Platform

> **"Democracy, Decoded."** — A real-time, agentic AI system that transforms how elections are monitored, understood, and experienced.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-AI-orange.svg)](https://ai.google.dev)

---

## 📌 The Problem — Pain Points in Indian Elections

India conducts the world's largest democratic exercise: **900M+ eligible voters**, **1M+ polling booths**, **543 constituencies**, all compressed into a handful of election days. Yet the voter experience is plagued by systemic, real-time failures:

| Pain Point | Scale of Impact | Current Reality |
|:---|:---|:---|
| **Unpredictable Queue Times** | 15–30% voter drop-off in urban areas | Voters arrive, see a 3-hour queue, and leave without voting. No real-time queue data exists for citizens. |
| **EVM/VVPAT Malfunctions** | ~0.5% of machines fail on election day | A single EVM failure halts an entire booth for 45–90 minutes. Panic spreads. Misinformation fills the vacuum. |
| **Election-Day Misinformation** | 68% of Indians receive election-related fake news (Reuters Institute) | WhatsApp forwards claiming "EVMs are hacked" or "Voting extended to tomorrow" spread unchecked during active polling. No instant, authoritative fact-check exists. |
| **Voter Confusion** | Millions of first-time voters every cycle | "Which booth am I assigned to?", "My name isn't on the list", "What ID do I need?" — answered only by overworked booth officers, if at all. |
| **Zero Situational Awareness** | Election officials react, never predict | Returning Officers get incident reports via phone calls and paper forms. No live dashboard. No predictive analytics. Responses are always *after* the damage. |
| **Accessibility Gaps** | 2.68 crore voters with disabilities (ECI 2024) | No real-time accessible voting assistance. No way to report accessibility issues that get triaged instantly. |

### The Core Insight

> **The Election Commission has digitized the *machinery* of elections (EVMs, voter rolls, results). But the *experience* of election day — the chaos, the queues, the confusion — remains analog.**

ElectaVerse bridges this gap.

---

## 🎯 What The System Needs

For a platform to genuinely solve election-day problems, it must satisfy these requirements:

### Non-Negotiable Requirements

1. **Real-Time Operation** — Not "check back in an hour." Sub-5-second updates on booth status, queue lengths, and incidents.
2. **AI That Reasons, Not Just Responds** — Not a chatbot. An *agentic* system where multiple specialized AI agents collaborate: one triages incidents, another predicts queues, another fights misinformation.
3. **Works Without AI Too** — If the AI API goes down, the simulation engine, dashboards, and data flows must continue. AI enhances; it doesn't gatekeep.
4. **Solves for ALL Stakeholders** — Citizens (voters), Officials (returning officers), and Observers (media, watchdogs) all have different needs from the same data.
5. **Accessible Knowledge** — Election processes are complex. The system must make them understandable through interactive timelines, step-by-step guides, and instant AI Q&A.
6. **Misinformation Defense** — A dedicated fact-checking agent that can analyze claims in real-time with structured verdicts and confidence scores.

### The "Prompt Wars" Challenge Alignment

This project is built for the **Google Prompt Wars** hackathon challenge: *"Create an assistant that helps users understand the election process, timelines, and steps in an interactive and easy-to-follow way."*

ElectaVerse doesn't just *explain* elections — it **monitors, predicts, responds, fact-checks, debates, quizzes, and visualizes** them in real-time.

---

## 🚀 What ElectaVerse Solves

### Architecture: Hybrid (Simulation-First, AI-on-Demand)

ElectaVerse uses a **three-layer hybrid architecture** — the same pattern used by production real-time systems (e.g., Tesla uses deterministic physics for real-time control + neural networks for reasoning):

```
┌─────────────────────────────────────────────────────────────┐
│              LAYER 1: DETERMINISTIC ENGINE                  │
│  Pure Python math. Runs every 3 seconds. Zero API calls.   │
│  • 200 polling booths simulated across 10 constituencies    │
│  • Poisson-modeled queue arrivals with time-of-day curves   │
│  • Stochastic incident injection (EVM faults, crowd issues) │
│  • Election clock: 7 AM → 6 PM (full day in ~17 real min)  │
│  → ALWAYS WORKS. No external dependencies.                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ triggers
┌──────────────────────────▼──────────────────────────────────┐
│              LAYER 2: REACTIVE AI AGENTS                    │
│  Google Gemini. Fires ONLY on user/system triggers.         │
│  • Election Analyst — answers voter questions               │
│  • Fact Checker — verifies claims with verdicts             │
│  • Incident Responder — triages booth incidents             │
│  • Queue Manager — predicts wait times                      │
│  • Debate Moderator — runs Prompt Wars battles              │
│  → ON-DEMAND. ~50-100 API calls/min max.                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ periodic sweep
┌──────────────────────────▼──────────────────────────────────┐
│              LAYER 3: PROACTIVE AI SWEEP                    │
│  Background task every ~30 seconds.                         │
│  • Analyzes top 10 congested booths                         │
│  • Generates redistribution recommendations                 │
│  • Pushes insights to dashboard automatically               │
│  → FEELS AUTONOMOUS without burning API quota.              │
└─────────────────────────────────────────────────────────────┘
```

### 🧩 How It Works (Simple Step-by-Step)

If you are wondering exactly how data flows through ElectaVerse, here is the simple version:

1. **The Heartbeat (Simulation Engine)**: Inside the backend, a clock ticks every 3 seconds. Every tick, it uses math (Poisson distribution) to decide how many people arrive at a booth and how many vote. It also randomly generates "incidents" like a broken EVM machine or a power outage.
2. **The Memory (MySQL Database)**: All this data isn't just floating in the air. Every config setting (like how fast people vote) and every incident is saved into a MySQL database. This means if the server crashes, your election data is safe.
3. **The Broadcast (WebSockets)**: The backend takes the latest booth queues and incidents and blasts them out to the frontend using WebSockets (Socket.IO). This is why the dashboard updates in real-time without you ever clicking "refresh".
4. **The Face (React Frontend)**: The frontend (built with React and Vite) catches these WebSocket broadcasts. It updates the live counters, colors the booths red if the queue is too long, and shows a scrolling feed of incidents.
5. **The Brain (AI Agents)**: When a user asks a question, requests a fact-check, or triggers a Prompt Wars debate, the frontend sends a REST API request to the backend. The backend routes it to one of **5 specialized Google Gemini AI agents**. The agent thinks, formats the answer nicely, and sends it back to the user.

### The 8 Solution Modules

| # | Module | Problem It Solves | How |
|:--|:-------|:------------------|:----|
| 1 | **Hero & Overview** | "I don't know what this platform does" | Animated landing with live stat counters, feature showcase, instant CTA |
| 2 | **Interactive Election Timeline** | "I don't understand the election cycle" | 6 clickable phases (Announcement → Results) with AI-enriched detail panels |
| 3 | **Step-by-Step Voter Guide** | "What do I actually DO on voting day?" | 4-step accordion with checklists, document requirements, "Ask AI" per step |
| 4 | **AI Election Assistant** | "I have a specific question no FAQ covers" | Full chat interface with streaming Gemini responses, routed through 5 specialized agents |
| 5 | **AI Fact Checker** | "Is this WhatsApp forward true?" | Paste a claim → verdict badge (True/Misleading/False) + confidence % + reasoning |
| 6 | **Prompt Battle Arena** | "I want to explore policy debates" *(Prompt Wars feature)* | Enter topic → 2 AI personas debate live with animated scoring (Logic/Evidence/Persuasion) |
| 7 | **Voter IQ Quiz** | "How much do I really know about voting?" | 10-question timed quiz, dynamic scoring, final badge reveal |
| 8 | **Live Operations Dashboard** | "What's happening at booths RIGHT NOW?" | Real-time booth grid, incident ticker, turnout gauge, queue heatmap, AI agent action log |

---

## 🏆 How ElectaVerse Surpasses Existing Solutions

### Existing Solutions & Their Limitations

| Existing Solution | What It Does | Where It Falls Short |
|:---|:---|:---|
| **ECI Voter Helpline (1950)** | Phone-based query resolution | Not real-time. No AI. No situational awareness. Long wait times. |
| **Voter Helpline App** | Check voter registration, find booth | Static data. No queue info. No incident reporting. No AI assistance. |
| **cVIGIL** | Photo/video-based violation reporting | Post-facto reporting only. No AI triage. No real-time dashboard. Manual review. |
| **SVEEP Campaigns** | Voter education pamphlets and events | One-directional. Not interactive. No personalized Q&A. Pre-election only. |
| **News Channel Dashboards** | State-level turnout percentages | Constituency-level only. No booth-level granularity. No queue data. No incidents. |
| **Generic AI Chatbots** | Answer questions about elections | Single-purpose. No multi-agent reasoning. No real-time data. No fact-checking. |

### ElectaVerse's Differentiators

| Differentiator | Detail |
|:---|:---|
| **🧠 Multi-Agent Agentic AI** | Not one chatbot — 5 specialized agents with an orchestrator. The Incident Responder knows EVM repair protocols. The Fact Checker returns structured verdicts. The Queue Manager understands Poisson distributions. |
| **⚡ Real-Time Simulation Engine** | 200 booths generating live data every 3 seconds with Poisson queue dynamics and stochastic incident injection. No other election tool offers booth-level real-time visualization. |
| **🛡️ Offline Resilience** | Dashboard and simulation work without an API key. AI enhances the experience but never gates it. Existing tools break entirely without connectivity. |
| **🔍 Dedicated Fact-Checking Agent** | Not "ask ChatGPT." A purpose-built agent returning structured JSON: `{verdict, confidence, reasoning}`. Displayed with visual verdict badges and confidence meters. |
| **⚔️ Prompt Wars Integration** | Unique to this project: AI-vs-AI policy debates with structured scoring. Makes civic engagement a *game*, not a chore. |
| **📊 Booth-Level Granularity** | Existing solutions show state/constituency-level data. ElectaVerse shows individual booth status: queue length, EVM status, active incidents, wait time estimates. |
| **🤖 Proactive Intelligence** | The system doesn't wait for questions. Every 30 seconds, the Queue Manager agent scans for congestion and pushes recommendations automatically. |

---

## ⚙️ System Mechanics: How It Actually Works

To ensure this platform is robust, scalable, and completely free of "fluff" or hardcoded hallucinations, the system operates on a strict data-driven architecture:

1. **No Hardcoded Values**: Everything—from constituencies and polling booths to user roles and election phases—is fetched dynamically from the MySQL database. There is absolutely no hardcoded mock data in the React components or Python scripts. If the database updates, the UI immediately reflects it.
2. **Real-Time Source of Truth**: AI models are prone to hallucinating facts (e.g., claiming a booth is open when it isn't). To prevent this, every single request to the **AI Election Assistant** or **AI Fact Checker** is injected with a **Live Simulation Context Payload**. The AI doesn't guess the queue length; the backend passes the exact current queue length, active incidents, and clock phase directly into the system prompt. The AI acts purely as an intelligent router and explainer for the *actual* live data.
3. **Deterministic Simulation Engine**: The backend runs a continuous threaded event loop (`engine.py`). It uses probabilistic models (like Poisson distributions for queue arrivals) to simulate election-day traffic across hundreds of database-backed booths. This engine is the beating heart of the platform, broadcasting state changes to the frontend via WebSockets every 3 seconds.

---

## 🏗️ System Architecture

### Backend (Python / Flask / SocketIO)

```
backend/
├── app.py                          # Flask + SocketIO entry point
├── config.py                       # Environment & simulation parameters
├── requirements.txt
├── agents/                         # 🧠 Agentic AI Layer
│   ├── orchestrator.py             # Intent classifier → routes to correct agent
│   ├── election_analyst.py         # Election knowledge Q&A
│   ├── fact_checker.py             # Claim verification → structured verdict
│   ├── incident_responder.py       # Incident triage → severity + actions + ETA
│   ├── queue_manager.py            # Queue prediction → wait time + suggestions
│   └── debate_moderator.py         # Prompt Wars → streaming debate + scores
├── services/
│   ├── gemini_service.py           # Gemini API wrapper (sync + JSON modes)
│   ├── booth_service.py            # Booth state aggregation
│   ├── incident_service.py         # Incident lifecycle management
│   └── analytics_service.py        # Trend computation
├── simulation/                     # 🎮 Deterministic Real-Time Engine
│   ├── engine.py                   # Master controller (background thread)
│   ├── election_clock.py           # Day phases: PRE_POLL → ACTIVE → POST → COUNTING
│   ├── queue_dynamics.py           # Poisson arrivals + throughput drain
│   └── incident_injector.py        # Stochastic incident generation
├── models/
│   ├── booth.py                    # Booth dataclass (queue, EVM, turnout, coords)
│   └── incident.py                 # Incident dataclass (6 types, 4 severities)
└── routes/
    ├── chat_routes.py              # POST /api/chat
    ├── booth_routes.py             # GET /api/booths, /api/booths/stats
    ├── incident_routes.py          # POST /api/incidents, /api/incidents/:id/triage
    ├── battle_routes.py            # POST /api/battle/start
    └── analytics_routes.py         # GET /api/analytics/*
```

### Frontend (React / Vite / TypeScript)

```
frontend/
├── index.html
├── package.json
├── vite.config.ts                  # API proxy → localhost:5000
├── tsconfig.json
└── src/
    ├── main.tsx
    ├── App.tsx                     # Tab router + WebSocket connection
    ├── index.css                   # Design system (dark theme, glassmorphism)
    ├── components/
    │   ├── layout/                 # Navbar, Footer, PageTransition
    │   ├── home/                   # HeroSection, StatsBar, FeatureShowcase
    │   ├── timeline/               # ElectionTimeline (6 interactive phases)
    │   ├── guide/                  # VoterGuide (4-step accordion)
    │   ├── assistant/              # AIAssistant, ChatMessage, SuggestionChips
    │   ├── factcheck/              # FactChecker (verdict + confidence UI)
    │   ├── battle/                 # PromptBattleArena, DebaterCard, ScoringPanel
    │   ├── quiz/                   # VoterIQQuiz, QuizResult
    │   ├── liveops/                # LiveDashboard, BoothGrid, IncidentFeed,
    │   │                             QueueHeatmap, TurnoutTracker, AgentActivityLog
    │   └── shared/                 # GlassCard, AnimatedCounter, StatusBadge,
    │                                 ProgressRing, PulsingDot
    ├── hooks/                      # useSocket, useApi
    ├── services/                   # api.ts, socket.ts
    └── data/                       # timelineData, voterGuideData, quizData
```

---

## 🧠 The Five AI Agents

### Agent Orchestrator
The central router. Takes any user input, makes a lightweight Gemini classification call, and routes to the most relevant agent.

### Agent 1: Election Analyst 🎓
- **Solves**: "How does EVM work?", "What's the MCC?", "Explain NOTA"
- **System Prompt**: Expert on Indian electoral processes — ECI, Lok Sabha, Rajya Sabha, EVM, VVPAT, Model Code of Conduct
- **I/O**: `question → markdown answer`

### Agent 2: Fact Checker 🔍
- **Solves**: "Is this WhatsApp forward about EVMs being hacked true?"
- **System Prompt**: Meticulous fact-checker returning structured verdicts
- **I/O**: `claim → {verdict: True|Misleading|False|Unverifiable, confidence: 0-100%, reasoning}`

### Agent 3: Incident Responder 🚨
- **Solves**: "EVM at Booth #347 is showing error code E-402"
- **System Prompt**: Election incident coordinator with ECI protocol knowledge
- **I/O**: `{incident, booth_context} → {severity, actions[], eta_minutes, escalation_path}`

### Agent 4: Queue Manager 📊
- **Solves**: "When should I vote to avoid the queue?"
- **System Prompt**: Queue analytics expert using throughput data and time-of-day patterns
- **I/O**: `{booth_state, nearby_booths} → {wait_minutes, best_time, alternatives[]}`

### Agent 5: Debate Moderator ⚔️
- **Solves**: "I want to explore the pros and cons of simultaneous elections"
- **System Prompt**: Debate moderator generating structured arguments with scoring
- **I/O**: `{topic, persona_a, persona_b} → streaming debate with Logic/Evidence/Persuasion scores`

---

## 🎮 Real-Time Simulation Engine

The simulation engine is the **deterministic backbone** — pure Python math, zero API calls, always running.

| Component | Model | Detail |
|:---|:---|:---|
| **Election Clock** | Linear progression | 7 AM → 6 PM. 2 simulated minutes per 3 real seconds. Full day in ~17 real minutes. |
| **Queue Arrivals** | Poisson(λ) | λ = base_rate × time_multiplier. Peaks at 9 AM and 5 PM. Lull at 1 PM. |
| **Queue Drain** | Deterministic + variance | 25 voters/hour/booth ±5. Halted if EVM is faulty. 70% speed if EVM replaced. |
| **Incidents** | Bernoulli per booth per tick | 6 types: EVM_MALFUNCTION, VVPAT_JAM, VOTER_ID_DISPUTE, CROWD_CONTROL, ACCESSIBILITY_ISSUE, POWER_OUTAGE |
| **Auto-Resolution** | Timer-based | LOW=15s, MEDIUM=45s, HIGH=90s, CRITICAL=150s (real-time) |
| **Broadcasting** | WebSocket (SocketIO) | Every 3 seconds: booth states, incidents, aggregate stats pushed to all clients |

**200 booths** across **10 Indian constituencies**: New Delhi, Mumbai North, Bangalore South, Chennai Central, Kolkata North, Hyderabad, Pune, Lucknow, Jaipur Rural, Ahmedabad East.

---

## 🔌 API Contracts

### REST Endpoints

| Method | Endpoint | Purpose |
|:---|:---|:---|
| `POST` | `/api/chat` | Send message → orchestrator routes to agent → response |
| `POST` | `/api/battle/start` | Start Prompt Wars debate |
| `GET` | `/api/booths` | All booth states (filterable by constituency) |
| `GET` | `/api/booths/stats` | Aggregate statistics |
| `POST` | `/api/incidents` | Report a new incident |
| `POST` | `/api/incidents/:id/triage` | Trigger AI triage on an incident |
| `GET` | `/api/analytics/turnout` | Turnout timeline data |
| `GET` | `/api/analytics/incidents` | Incident breakdown by type/severity |

### WebSocket Events (SocketIO)

| Event | Payload | Frequency |
|:---|:---|:---|
| `booth_update` | `{booths: Booth[], clock: Clock}` | Every 3 seconds |
| `new_incident` | `{incident: Incident}` | On occurrence |
| `stats_update` | `{turnout, queue_avg, incidents}` | Every 3 seconds |
| `agent_action` | `{agent, action, result}` | On AI sweep (~30s) |

---

## 🎨 Design System

| Token | Value | Usage |
|:---|:---|:---|
| Background | `#080c18` | Deep space navy — page background |
| Surface | `rgba(255,255,255,0.04)` | Glassmorphism card fills |
| Primary | `#6366f1` | Electric indigo — buttons, links |
| Accent | `#f59e0b` | Civic gold — highlights, badges |
| Success | `#10b981` | Healthy booths, correct answers |
| Danger | `#ef4444` | Critical incidents, wrong answers |
| Warning | `#f97316` | Queue warnings, triaging |
| Heading Font | Outfit | All headings |
| Body Font | Inter | All body text |
| Glass Effect | `backdrop-filter: blur(12px)` | Cards, navbar, modals |

---

## ⚙️ Tech Stack

| Layer | Technology | Why |
|:---|:---|:---|
| **Frontend** | React 19 + Vite + TypeScript | Fast HMR, type safety, modern DX |
| **Animations** | Framer Motion | Declarative page transitions, micro-animations |
| **Icons** | Lucide React | Consistent, tree-shakeable icon set |
| **Backend** | Python Flask + SocketIO | Lightweight, WebSocket-native, fast prototyping |
| **AI** | Google Gemini (gemini-2.0-flash) | Fast, multimodal, structured output support |
| **Real-Time** | Flask-SocketIO + socket.io-client | Bidirectional WebSocket for live data |
| **Simulation** | Pure Python (math, random) | Deterministic, zero dependencies, offline-capable |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API Key ([Get one free](https://aistudio.google.com/apikey))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/anxmeshhh/Google-Prompt-Wars---Election-System.git
cd Google-Prompt-Wars---Election-System

# 2. Create environment file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Start the Backend
cd backend
pip install -r requirements.txt
python app.py
# Server starts on http://localhost:5000

# 4. Start the Frontend (new terminal)
cd frontend
npm install
npm run dev
# App opens on http://localhost:5173
```

> **Note:** The real-time dashboard and simulation engine work without an API key. Only AI features (chat, fact-check, battles) require the Gemini API key.

---

## 📄 License

MIT License — Copyright (c) 2026 Animesh Gupta

See [LICENSE](./LICENSE) for full text.
