# Image de l'application Python : ingestion + API FastAPI + serveur MCP.
# (Le front Next.js a son propre Dockerfile dans front/.)
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# Dépendances d'exécution uniquement (couche mise en cache tant que requirements.txt ne change pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'application
COPY ingestion/ ./ingestion/
COPY vigie/ ./vigie/
COPY api/ ./api/
COPY vigie_mcp/ ./vigie_mcp/
COPY data/fixtures/ ./data/fixtures/

EXPOSE 8000

# Par défaut : sert l'API. L'ingestion est lancée par le service `ingest` de docker-compose.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
