# Tampines Estate Reporter

> AI-powered estate issue reporting and municipal dispatch for Tampines, Singapore.

**[Live Demo in  Render cloud→](https://tampines-estate-reporter.onrender.com)**
**[Live Demo in Vercel cloud →](https://tampines-estate-reporter.vercel.app/)**

---

## Why This Matters

When a pipe bursts at 2 AM, a resident shouldn't need to know whether PUB or the Town Council handles it — or how to describe the urgency to the right person. In practice, most residents either give up, call the wrong agency, or submit vague reports that sit unactioned.

Tampines Estate Reporter removes this friction. Residents speak or photograph an issue in any language; AI classifies, prioritises, and routes it to the right agency in seconds — with a case ID and expected response time returned immediately.

On the municipal side, officers get structured, pre-prioritised caseloads with full context, automated assignments, and one-click resolution. No manual triage. No missed reports.

---

## Application Screenshots

### Resident Portal

<p align="center">
  <img src="static/resident-portal.png" width="60%">
</p>

### Agency Dashboard

<p align="center">
  <img src="static/agency-dashboard.png" width="60%">
</p>

---

## Features

### Resident Portal
- **AI-powered multimodal reporting** — speak or photograph an issue; AI transcribes, classifies, and routes it automatically
- **Multi-language support** — reports accepted in English, Mandarin, Malay, Tamil, and more (auto-translated to English)
- **Smart issue labelling** — Gemini 2.5 Flash identifies issue types from 61 categories (e.g. `burst_pipe`, `overflowing_bin`, `broken_playground`)
- **Instant confirmation** — case ID, priority level, assigned agency, and estimated response time returned immediately
- **Report history** — residents can look up all past submissions

### Agency Portal
- **Unified dashboard** — all assigned cases with priority badges and status filters
- **AI chat assistant** — officers can query cases and get AI-generated summaries via a built-in chat interface
- **Workforce view** — live officer availability and open-case workload per officer
- **Analytics** — case volume by agency, priority breakdown, and SLA compliance over configurable time windows
- **Email notifications** — officers notified per case; residents notified on resolution
- **One-click resolve** — cases resolved via a signed email link, no login required

---

## AI Resilience

The platform uses a multi-provider architecture so processing continues even during individual API outages:

| Task | Primary | Fallback |
|---|---|---|
| Issue classification (text + images) | Gemini 2.5 Flash | — |
| Audio transcription | Groq Whisper | — |
| Chat / conversational AI | Gemini 2.5 Flash | Groq Llama 3.3 70B |
| Structured output | Pydantic schema validation | Retry with explicit prompting |

Pydantic schemas enforce structured JSON on every Gemini response — malformed outputs are caught and retried before they reach the database.

---

## Agency Routing

Issues auto-route to one of seven real Singapore agencies based on issue type:

| Agency | Handles |
|---|---|
| **Tampines Town Council** | Structural, electrical, general estate maintenance |
| **NEA** | Cleanliness, pest control, noise, e-waste |
| **PUB** | Water, drainage, flooding |
| **SCDF** | Fire safety, emergency hazards |
| **Singapore Police Force** | Noise complaints, public order |
| **LTA** | Vehicles, traffic, road infrastructure |
| **NParks** | Greenery, parks, fallen trees |

Each issue type carries a configured **SLA** (from `IMMEDIATE` to `5 working days`) and **priority** (`CRITICAL / HIGH / MEDIUM / LOW`).

---

## Scalability

The system is built for growth:

- **Database**: SQLite for local/demo use; drop-in PostgreSQL migration via `DATABASE_URL`
- **Deployment**: Cloud-native on Render; stateless Flask app scales horizontally
- **Agency expansion**: New agencies and issue types added via config — no code changes
- **Model flexibility**: AI providers are swappable; the pipeline is provider-agnostic by design
- **Future path**: Each `agents.py` function is a natural microservice boundary for eventual decomposition

---

## Tech Stack

**Backend**
- Python 3 / Flask
- SQLite (default) — drop-in upgrade path to PostgreSQL via `DATABASE_URL`
- Google Gemini SDK (`google-genai`)
- Groq SDK (Whisper STT + Llama LLM fallback)
- SendGrid — email dispatch and resolution links
- Twilio — SMS notifications
- Pillow — image compression before AI analysis

**Frontend**
- Vanilla HTML/CSS/JS (no build step)
- Chart.js — analytics charts
- Google Fonts (Syne, DM Sans)
- PWA-ready (`sw.js` service worker)

---

## Getting Started

### Prerequisites

- Python 3.10+
- API keys for: Gemini, Groq, SendGrid (and optionally Twilio)

### Installation

```bash
git clone https://github.com/KyawSuThway01/tampines-estate-reporter.git
cd tampines-estate-reporter
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
# AI
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key

# Email
SENDGRID_API_KEY=your_sendgrid_key
FROM_EMAIL=your_sender@email.com

# SMS (optional)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_FROM_PHONE=+6512345678

# App
APP_BASE_URL=https://your-domain.com

# Database (optional — defaults to SQLite)
SQLITE_PATH=tampines.db
# DATABASE_URL=postgresql://user:pass@host:5432/tampines

# Feature flags
DEMO_MODE=false
TEST_MODE=false
TEST_EMAIL=
TEST_PHONE=
```

### Run

```bash
python main.py
```

The app starts on `http://localhost:5000`.

---

## Demo & Test Modes

- `DEMO_MODE=true` — bypasses real AI calls and returns synthetic data; safe for UI demos
- `TEST_MODE=true` — routes all emails/SMS to `TEST_EMAIL` / `TEST_PHONE` instead of real recipients

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze` | Submit a report (audio, image, or text) — main AI pipeline |
| `GET` | `/cases` | List all cases |
| `GET` | `/cases/agency/<name>` | Cases filtered by agency |
| `PATCH` | `/cases/<id>/status` | Update case status |
| `GET` | `/cases/<id>/resolve` | Resolve a case via signed email link |
| `POST` | `/cases/<id>/notify-resident` | Send resolution email/SMS to resident |
| `POST` | `/cases/<id>/dispatch-email` | Dispatch case email to assigned officer |
| `GET` | `/workforce` | Live officer availability for all agencies |
| `GET` | `/workforce/capacity` | Capacity analysis for a specific incoming case |
| `GET` | `/analytics` | Case statistics by agency and priority (supports `?days=` filter) |
| `GET` | `/leaderboard` | Agency resolution leaderboard |
| `POST` | `/api/chat` | Groq LLM chat (agency assistant) |
| `POST` | `/api/gemini-chat` | Gemini chat with Groq fallback |
| `POST` | `/agency/login` | Agency authentication |
| `POST` | `/officer/contact` | Officer sends message to resident |
| `GET` | `/health` | Health check |

---

## Workforce & Capacity

Each of the 7 agencies has 2 named officers. When a new case comes in, `workforce.py`:

1. Queries the database for each officer's current open-case count
2. Derives a status: `free` / `on_case` / `at_capacity`
3. Picks the best-fit officer (fewest open cases)
4. Returns a capacity verdict (`Sufficient` / `Stretched` / `Understaffed`) and an estimated response time

---

## Agency Login

Agency portal access is password-protected. Default credentials (change before deploying):

| Agency | Password |
|---|---|
| council | `tampines2025` |

Additional agencies can be added to `AGENCY_PASSWORDS` in `main.py`.

---

## 🏆 Hackathon Showcase — Tampines Hackathon

> Tampines Estate Reporter was built and presented at the **Tampines Hackathon**, where teams were challenged to develop technology-driven solutions that improve estate living and municipal service delivery for residents. Our team designed, built, and deployed the full-stack AI pipeline — from resident-facing voice reporting to automated agency dispatch — within the hackathon window, and presented the live system to a judging panel that included government officials and industry experts.

---

### Event Gallery

<br>

**🎤 Project Presentation**

![Project Presentation](static/presentation.jpg)

> Presenting the Tampines Estate Reporter live to the judging panel — walking through the end-to-end AI pipeline, from multimodal resident input to structured agency dispatch and real-time case tracking.

<br>

---

** Discussion with Minister**

![Discussion with Minister](/static/minister_discussion.jpeg)

> A conversation with the Minister about the project's real-world impact on estate management, its potential for broader adoption across Singapore's towns, and how AI can meaningfully reduce friction between residents and municipal agencies.

<br>

---

** Team Photo with Judges & Mentors**

![Team Photo with Judges and Mentors](/static/team_photo.jpeg)

> The full team with judges and mentors following the final presentation. Grateful for the feedback, the challenge, and the opportunity to build something with genuine civic value.

<br>

---

### Key Takeaways

| Area | What We Demonstrated |
|---|---|
| **Technical depth** | Multi-provider AI pipeline with Gemini, Groq Whisper, and structured Pydantic validation |
| **Domain knowledge** | Accurate routing across 7 real Singapore agencies with 61 issue types and configurable SLAs |
| **Execution speed** | Full-stack system — backend, AI pipeline, agency portal, and notifications — built and live-demoed within the hackathon |
| **Communication** | Presented a technical product to a mixed audience of government officials, engineers, and non-technical judges |
| **Teamwork** | Parallel development across AI, backend, and frontend under time pressure |

---

> *"The best civic tech doesn't just solve a problem — it removes the friction between people and the help they need."*

---

## License

MIT# TampinesReporter
