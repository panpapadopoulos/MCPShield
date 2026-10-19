FROM node:22-alpine AS frontend
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY shield/ ./shield/
COPY scripts/ ./scripts/
COPY data/provenance.json ./data/provenance.json
RUN python scripts/fetch_corpus.py && python -m shield.dataset
COPY --from=frontend /ui/dist ./frontend/dist/
RUN useradd --uid 10001 --create-home shield && mkdir -p results && chown -R shield:shield /app
USER shield
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=2)" || exit 1
CMD ["uvicorn", "shield.api:app", "--host", "0.0.0.0", "--port", "8000"]
