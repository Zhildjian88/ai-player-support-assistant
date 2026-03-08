# ── AI Player Support Assistant — Dockerfile ──────────────────
# Containerises the FastAPI backend service.
# The Streamlit UI runs as a separate container (see docker-compose.yml).
#
# Persistence note:
#   The SQLite database lives at data/app.db. Mount a volume at /app/data
#   to persist state across container restarts. Without a volume, the
#   database is ephemeral and reset on every container start.
#
# Build:
#   docker build -t ai-player-support .
#
# Run (ephemeral demo):
#   docker run -p 8000:8000 -e GROQ_API_KEY=your_key ai-player-support
#
# Run (with persistent DB):
#   docker run -p 8000:8000 -v $(pwd)/data:/app/data \
#     -e GROQ_API_KEY=your_key ai-player-support

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first — maximises layer cache reuse
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Database initialisation runs at container start so the SQLite file
# can live in a mounted volume and persist across container restarts.
CMD ["sh", "-c", "python -m app.db_init && uvicorn api.main:app --host 0.0.0.0 --port 8000"]
