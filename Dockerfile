# Runtime image for the scrape -> delta-detect -> ingest pipeline.
# Single stage: Debian-based Python image with Node.js/pnpm layered on top,
# since the daily job needs both runtimes available at execution time
# (the scraper is TypeScript, the ingester is Python).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODE_ENV=production \
    PNPM_HOME="/pnpm" \
    PATH="/pnpm:$PATH"

# Node.js 20.x + pnpm (via corepack), kept in the same layer as its own
# install/cleanup so no intermediate build tooling is left in the final image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && corepack enable \
    && corepack prepare pnpm@10.33.0 --activate \
    && apt-get purge -y --auto-remove curl gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies (separate layer so code changes don't invalidate this cache).
COPY AIAssistant/requirements.txt ./AIAssistant/requirements.txt
RUN pip install --no-cache-dir -r AIAssistant/requirements.txt

# Node dependencies (separate layer, keyed only on the lockfile/manifest).
COPY Scrape/package.json Scrape/pnpm-lock.yaml ./Scrape/
RUN cd Scrape && pnpm install --frozen-lockfile

# Application source.
COPY Scrape ./Scrape
COPY AIAssistant ./AIAssistant

WORKDIR /app/AIAssistant

# Default manifest location inside the container; override with a
# volume-mounted path (e.g. /data/manifest.json) in production so state
# survives across ephemeral job runs. See DEPLOYMENT.md.
ENV MANIFEST_PATH=/app/AIAssistant/manifest.json

CMD ["python", "main.py"]
