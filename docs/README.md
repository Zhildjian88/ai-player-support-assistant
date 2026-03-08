## Player UI — GitHub Pages

The player-facing chat UI is a **zero-build static HTML file** (`docs/index.html`) deployed via GitHub Pages.  
No Node.js, no webpack, no build step.

### Live URL
```
https://Zhildjian88.github.io/ai-player-support-assistant/
```

### How it works
- The UI is pure HTML + React (loaded via CDN) — no build step needed
- Chat messages POST to the FastAPI backend hosted on Render
- API keys live on Render only — never in the browser, never in this file

### Changing the backend URL
Edit `docs/index.html`, find:
```js
const API_BASE = window.SIDOBET_API_URL || "https://YOUR-APP.onrender.com";
```
Replace with your Render URL after deployment.

### GitHub Pages setup (one time)
1. Push repo to GitHub
2. Settings → Pages → Deploy from branch → `main` → `/docs`
3. Save — live in ~60 seconds

### Full deployment guide
See [DEPLOY.md](../DEPLOY.md) for Render + GitHub Pages end-to-end instructions.
