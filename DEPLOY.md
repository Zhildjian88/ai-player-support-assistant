# Deployment Guide — Render (Backend) + GitHub Pages (Frontend)

This gets the full demo live for hirers in about 15 minutes.  
No local installs needed by anyone visiting — they just open the URL.

---

## Architecture

```
Hirer's browser
    │
    │  visits
    ▼
GitHub Pages  (docs/index.html — free, always on, no expiry)
    │
    │  POST /chat
    ▼
Render  (FastAPI backend — free tier, no expiry)
    │
    │  API call
    ▼
Groq  (LLM — free tier, no credit card needed)
```

> **Cold start note:** Render's free tier spins down after 15 minutes of inactivity.  
> The first visitor after an idle period waits ~30–60 seconds for the server to wake.  
> After that, all responses are fast. This is normal and acceptable for a portfolio demo.

---

## Step 1 — Get a free Groq API key

1. Go to **https://console.groq.com**
2. Sign up (free, no credit card needed)
3. Click **API Keys → Create API Key**
4. Copy the key — you will need it in Step 2

---

## Step 2 — Deploy backend to Render

1. Go to **https://render.com** and sign up with GitHub
2. Click **New → Web Service**
3. Connect your GitHub repo: `ai-player-support-assistant`
4. Configure the service:

| Setting | Value |
|---|---|
| **Name** | `ai-player-support-assistant` |
| **Region** | Singapore (or closest to your users) |
| **Branch** | `main` |
| **Runtime** | **Docker** |
| **Dockerfile path** | `Dockerfile.render` |
| **Instance type** | Free |

5. Scroll down to **Environment Variables** → add these:

| Variable | Value |
|---|---|
| `GROQ_API_KEY` | `gsk_...` (your Groq key from Step 1) |
| `LLM_MODEL` | `llama-3.1-8b-instant` |
| `ENABLE_LLM_FALLBACK` | `true` |
| `USE_NEURAL_EMBEDDINGS` | `false` |
| `ENABLE_AUDIT_LOG` | `true` |
| `ENABLE_ESCALATION` | `true` |
| `PORT` | `8000` |

> **Never** put these in `.env` and push to GitHub. Render's Environment Variables panel is the secure way.

6. Click **Create Web Service** — Render will build and deploy automatically (~3–5 min first time)
7. Once live, your Render URL will look like:  
   `https://ai-player-support-assistant.onrender.com`

---

## Step 3 — Point GitHub Pages at your Render URL

Edit `docs/index.html`, find this line near the top of the `<script>` block:

```js
const API_BASE = window.SIDOBET_API_URL || "https://YOUR-APP.onrender.com";
```

Replace `YOUR-APP.onrender.com` with your actual Render URL:

```js
const API_BASE = window.SIDOBET_API_URL || "https://ai-player-support-assistant.onrender.com";
```

---

## Step 4 — Push to GitHub

```bash
cd ai-player-support-assistant
git add docs/index.html
git commit -m "deploy: set Render backend URL"
git push origin main
```

GitHub Pages updates automatically. Render also auto-redeploys on every push.

---

## Step 5 — Enable GitHub Pages

1. Go to your GitHub repo → **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` — Folder: `/docs`
4. Click **Save**
5. Wait ~60 seconds — your live URL will be:  
   `https://Zhildjian88.github.io/ai-player-support-assistant/`

---

## Step 6 — Test end-to-end

1. Open your GitHub Pages URL in a browser
2. Select a player → **Enter Support Chat**
3. Click a Quick Action — should respond via Render → Groq
4. Type a free-text message — LLM fallback should engage
5. Check Render dashboard → **Logs** tab to confirm requests are arriving

---

## Sharing with hirers

Just send them:
```
https://Zhildjian88.github.io/ai-player-support-assistant/
```

They click, they see the UI, they interact. No setup needed on their end.

---

## Free tier limits

| Service | Free tier | Expiry | Sufficient for portfolio? |
|---|---|---|---|
| GitHub Pages | Unlimited static hosting | None | ✅ Yes |
| Render | 750 hrs/month, 512 MB RAM | None — renews monthly | ✅ Yes |
| Groq | ~14,400 req/day | None | ✅ Yes |

Render's free tier gives 750 hours per month on a single service — enough to run continuously, no expiry.

---

## Local development (unchanged)

```bash
cp .env.example .env          # fill in GROQ_API_KEY
python -m app.db_init
uvicorn api.main:app --reload  # backend on http://localhost:8000
```

For local testing, temporarily change `docs/index.html`:
```js
const API_BASE = "http://localhost:8000";
```

---

## Ops console (local only)

The Streamlit ops console is for your internal use, not for hirers:

```bash
streamlit run ui/streamlit_app.py
```

---

## Updates

Every `git push origin main` automatically:
- Redeploys Render backend (if backend files changed)
- Updates GitHub Pages frontend (if `docs/index.html` changed)
