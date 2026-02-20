# ⚡ Angular Component Architect

> An agentic AI pipeline that transforms natural language descriptions into valid, design-system-compliant Angular components — powered by GROQ's ultra-fast LLM inference.

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
│   └── requirements.txt     ← Python dependencies
│
├── 📁 frontend/
│   └── index.html           ← Web UI (zero build step — open directly in browser)
│
└── README.md
```

---

## 🚀 Setup & Installation

### Prerequisites
- [Anaconda](https://www.anaconda.com/download) installed
- A free [GROQ API key](https://console.groq.com) (takes 2 minutes to get)
- VS Code (recommended) or any text editor

---

### Step 1 — Get Your GROQ API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for free
3. Navigate to **API Keys** → **Create API Key**
4. Copy and save the key — you'll use it in Step 4

---

### Step 2 — Create the Conda Environment

Open **Anaconda Prompt** (Windows) or **Terminal** (Mac/Linux):

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

`requirements.txt` contains:
```
groq>=0.9.0
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
```

---

### Step 4 — Set Your GROQ API Key

**Windows (Anaconda Prompt):**
```cmd
set GROQ_API_KEY=gsk_your_key_here
```

**Mac / Linux:**
```bash
export GROQ_API_KEY=gsk_your_key_here
```

> 💡 To make it permanent on Mac/Linux, add it to your shell config:
> ```bash
> echo 'export GROQ_API_KEY=gsk_your_key_here' >> ~/.bashrc
> source ~/.bashrc
> ```

---

### Step 5 — Start the Backend Server

```bash
cd path/to/angular-architect/backend
uvicorn server:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

---

### Step 6 — Open the Frontend

Open `frontend/index.html` directly in your browser:

| OS | Command |
|----|---------|
| Windows | Double-click `index.html` or drag into Chrome |
| Mac | `open frontend/index.html` |
| Linux | `xdg-open frontend/index.html` |

> ✅ No npm, no build step, no node_modules — it's plain HTML/CSS/JS.

---

### Step 7 — Generate Your First Component!

1. Type a description in the prompt box
2. Press **Ctrl+Enter** or click the send button
3. Watch the agentic loop run through the steps in real time
4. Click **Export .ts** to download the component file

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

---

## 🔄 Multi-Turn Editing

The system maintains conversation history per session. After generating a component, you can refine it:

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

The Linter-Agent will reject and auto-fix any component that uses colors or values outside these tokens.

---

## 🔌 API Reference

Base URL: `http://localhost:8000`

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

### `DELETE /session/{session_id}`
Clears the conversation history for a session.

### `GET /health`
Health check — confirms server is running and API key is set.

---

## 🖥️ CLI Usage

You can also run the pipeline directly without the web UI:

```bash
conda activate architect
cd backend/

# Make sure GROQ_API_KEY is set first
python architect.py "A pricing card with 3 tiers using primary color #6366f1"
```

Output will be printed directly to the terminal.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `GROQ_API_KEY not configured` | Run `set GROQ_API_KEY=...` in the **same terminal** as uvicorn |
| CORS error in browser | Confirm backend is running on port `8000` |
| `Could not load tokens` in UI | Backend is not running — start it with `uvicorn server:app --reload` |
| `Model not found` error | Check available models at [console.groq.com/docs/models](https://console.groq.com/docs/models) and update `MODEL` in `architect.py` |
| Port 8000 already in use | Use `uvicorn server:app --reload --port 8001` and update `API_BASE` in `index.html` |

---

## 🧩 How the Validation Works

The Linter-Agent in `architect.py` runs 5 checks on every generated component:

1. **Syntax check** — counts all `{`, `}`, `(`, `)`, `[`, `]` to ensure balanced brackets
2. **Color compliance** — extracts all hex codes via regex and cross-references against `tokens.json`
3. **Border-radius compliance** — finds all `border-radius` declarations and checks pixel values
4. **Font compliance** — finds all `font-family` declarations and validates against allowed fonts
5. **Angular structure** — confirms `@Component`, `selector`, `template`, and `export class` are present

If **any hard error** is found, the full error log is fed back to the LLM with the instruction to fix it — up to **2 automatic retries** before returning the best available output.

---

## 📄 License

MIT — free to use, modify, and distribute.
