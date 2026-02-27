# ⚡ Angular Component Architect

> An agentic AI pipeline that transforms natural language descriptions into valid, design-system-compliant Angular components — powered by GROQ's ultra-fast LLM inference.

🌐 **Live Demo:** [https://angular-architect.netlify.app](https://angular-architect.netlify.app)
⚙️ **Backend API:** [https://angular-component-architect.onrender.com](https://angular-component-architect.onrender.com)
📖 **API Docs:** [https://angular-component-architect.onrender.com/docs](https://angular-component-architect.onrender.com/docs)
💻 **GitHub:** [https://github.com/lalit2244/angular-component-architect](https://github.com/lalit2244/angular-component-architect)

---

## 📸 What It Does

You type: *"A glassmorphism login card with email and password fields"*

The system:
1. **Generates** a complete Angular TypeScript component using GROQ LLM
2. **Validates** it against your design system tokens (colors, fonts, border-radius)
3. **Self-corrects** automatically if errors are found — up to 2 retry attempts
4. **Outputs** a clean, exportable `.ts` file ready to drop into any Angular project

---

## 🏗️ Agentic Loop Architecture

```
User Prompt
     │
     ▼
┌─────────────────────────────────────────────┐
│  1. GENERATOR  (GROQ LLM)                   │
│     • Prompt + full Design System injected  │
│     • Outputs raw Angular TypeScript code   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  2. LINTER-AGENT  (architect.py)            │
│     ✔ Bracket / brace balance (syntax)      │
│     ✔ Hex color token compliance            │
│     ✔ Border-radius token compliance        │
│     ✔ Font-family compliance                │
│     ✔ @Component decorator structure        │
└──────────────────┬──────────────────────────┘
                   │
          ┌────────┴────────┐
          │                 │
       PASS ✅          FAIL ❌
          │                 │
          │    ┌────────────▼──────────────┐
          │    │  3. SELF-CORRECTION       │
          │    │     Error logs → LLM      │
          │    │     Re-generates code     │
          │    │     (max 2 retries)       │
          │    └────────────┬──────────────┘
          │                 │
          └────────┬────────┘
                   │
                   ▼
           Final .ts Component
```

---

## 📁 Project Structure

```
angular-architect/
│
├── 📁 design-system/
│   └── tokens.json          ← All design tokens (colors, spacing, fonts, shadows)
│
├── 📁 backend/
│   ├── architect.py         ← Core agentic pipeline (generate → validate → correct)
│   ├── server.py            ← FastAPI REST server with multi-turn session memory
│   ├── tokens.json          ← Design tokens copy for Render deployment
│   ├── .python-version      ← Python 3.11.14 for Render
│   └── requirements.txt     ← Python dependencies
│
├── 📁 frontend/
│   └── index.html           ← Web UI (zero build step — open directly in browser)
│
├── .gitignore
└── README.md
```

---

## 🚀 Local Setup & Installation

### Prerequisites
- [Anaconda](https://www.anaconda.com/download) installed
- A free [GROQ API key](https://console.groq.com) (takes 2 minutes to get)
- VS Code or any text editor

---

### Step 1 — Get Your GROQ API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for free
3. Navigate to **API Keys** → **Create API Key**
4. Copy and save the key

---

### Step 2 — Create the Conda Environment

```bash
conda create -n architect python=3.11 -y
conda activate architect
```

---

### Step 3 — Install Dependencies

```bash
cd path/to/angular-architect/backend
pip install -r requirements.txt
```

---

### Step 4 — Set Your GROQ API Key

**Windows:**
```cmd
set GROQ_API_KEY=gsk_your_key_here
```

**Mac / Linux:**
```bash
export GROQ_API_KEY=gsk_your_key_here
```

---

### Step 5 — Start the Backend Server

```bash
cd path/to/angular-architect/backend
uvicorn server:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

### Step 6 — Open the Frontend

Open `frontend/index.html` directly in your browser — no build step needed.

---

## 🌐 Deployment

| Service | Platform | URL |
|---------|----------|-----|
| Frontend | Netlify | https://angular-architect.netlify.app |
| Backend | Render | https://angular-component-architect.onrender.com |

### Backend deployed on Render
- Runtime: Python 3.11.14
- Start command: `uvicorn server:app --host 0.0.0.0 --port 10000`
- Environment variable: `GROQ_API_KEY` set in Render dashboard

### Frontend deployed on Netlify
- Base directory: `frontend`
- Publish directory: `frontend`
- No build command needed

---

## 💡 Example Prompts

```
A glassmorphism login card with email/password fields and a sign-in button
```
```
A dashboard stats row with 4 metric cards and icons
```
```
A pricing card with 3 tiers, features list, and a highlighted recommended plan
```
```
A notification toast with success, error, and warning variants
```
```
A user profile card with avatar, name, role badge, and a follow button
```
```
A search bar with a magnifier icon and a search button styled with primary color
```

---

## 🔄 Multi-Turn Editing

The system maintains conversation history per session:

```
You:    "A login card with glassmorphism effect"
System: [generates component]

You:    "Now make the button pill-shaped"
System: [updates only the button border-radius]

You:    "Add a Google sign-in option below the form"
System: [adds Google SSO button to existing component]
```

---

## 🎨 Design System Tokens

All generated components must use tokens from `design-system/tokens.json`.

| Category | Key Tokens |
|----------|------------|
| **Colors** | `primary: #6366f1`, `secondary: #06b6d4`, `accent: #f59e0b`, `success: #10b981`, `error: #ef4444` |
| **Fonts** | `Inter` (sans), `JetBrains Mono` (mono) |
| **Border Radius** | `4px`, `8px`, `12px`, `16px`, `24px`, `9999px` |
| **Shadows** | `shadow-sm` through `shadow-xl`, `shadow-glass` |
| **Spacing** | `0.25rem` to `6rem` (8-point scale) |

---

## 🔌 API Reference

Base URL: `https://angular-component-architect.onrender.com`

### `POST /generate`
Generate an Angular component from a prompt.

**Request:**
```json
{
  "prompt": "A login card with glassmorphism effect",
  "session_id": "my-session"
}
```

**Response:**
```json
{
  "code": "import { Component } from '@angular/core'; ...",
  "success": true,
  "attempts": 1,
  "errors": [],
  "warnings": [],
  "hard_errors": [],
  "session_id": "my-session"
}
```

### `GET /tokens`
Returns the full design system token JSON.

### `GET /health`
Health check — confirms server is running and API key is set.

**Response:**
```json
{"status": "ok", "groq_key_set": true}
```

### `DELETE /session/{session_id}`
Clears the conversation history for a session.

### `GET /docs`
Interactive API documentation (Swagger UI) — test all endpoints in browser.

---

## 🖥️ CLI Usage

```bash
conda activate architect
cd backend/
python architect.py "A pricing card with 3 tiers using primary color #6366f1"
```

---

## 🧩 How the Validation Works

The Linter-Agent in `architect.py` runs 5 checks on every generated component:

| Check | Method | What it catches |
|-------|--------|-----------------|
| **Syntax** | Stack algorithm | Unbalanced `{}`, `()`, `[]` |
| **Color compliance** | Regex + whitelist | Any hex color not in tokens.json |
| **Border-radius** | Regex + comparison | Pixel values not in allowed set |
| **Font compliance** | Regex | Any font-family not Inter or JetBrains Mono |
| **Angular structure** | String search | Missing `@Component`, `selector`, `template`, `export class` |

If any hard error is found → error log fed back to LLM → regenerates → re-validates → up to **2 automatic retries**.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **GROQ API** | Ultra-fast LLM inference (400+ tokens/sec) |
| **LLaMA 3.3 70B** | Code generation model |
| **FastAPI** | Python async REST API framework |
| **Pydantic** | Request/response validation |
| **Python 3.11** | Backend runtime |
| **Vanilla JS/HTML/CSS** | Frontend (zero build step) |
| **Render** | Backend cloud deployment |
| **Netlify** | Frontend cloud deployment |

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `GROQ_API_KEY not configured` | Run `set GROQ_API_KEY=...` in the same terminal as uvicorn |
| CORS error in browser | Confirm backend URL in `index.html` matches your Render URL exactly |
| `Could not load tokens` in UI | Backend not running — check Render logs |
| First request takes 30 seconds | Normal — Render free tier sleeps after 15 min inactivity |
| Port 8000 already in use | Use `uvicorn server:app --reload --port 8001` and update `API_BASE` in `index.html` |

---

## 🔐 Security — Prompt Injection Prevention

1. **System prompt is server-side only** — never exposed to client
2. **User input always passed as `user` message** — structurally cannot override system instructions
3. **Linter-Agent as output firewall** — non-code output fails validation immediately
4. **Typed Pydantic responses** — output is always a structured object, never raw execution

---

## 📄 License

MIT — free to use, modify, and distribute.
