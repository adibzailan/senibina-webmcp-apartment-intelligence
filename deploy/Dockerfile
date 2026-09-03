# Apartment Intelligence v2: Python 3.13 + Radiance 6.1a (LBNL-ETA 39b99660) + built web bundle.
# Build:  docker build -f deploy/Dockerfile -t apartment-intelligence:v2 .
FROM node:22-bookworm-slim AS web
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/web/ ./
RUN npm run build

FROM python:3.13-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip ca-certificates && rm -rf /var/lib/apt/lists/*
# Radiance: pinned release + SHA-256 (verified 2026-09-03)
ARG RADIANCE_TAG=39b99660
ARG RADIANCE_SHA256=fe2b0df32acb90e5b03e37039555aea85098f5343f17247bfec700189009b7c7
RUN curl -fsSL -o /tmp/radiance.zip https://github.com/LBNL-ETA/Radiance/releases/download/${RADIANCE_TAG}/Radiance_${RADIANCE_TAG}_Linux.zip \
 && echo "${RADIANCE_SHA256}  /tmp/radiance.zip" | sha256sum -c - \
 && cd /tmp && unzip -q radiance.zip && mkdir -p /usr/local/radiance \
 && tar -xzf /tmp/radiance-*-Linux.tar.gz -C /usr/local/radiance --strip-components=1 \
 && rm -rf /tmp/radiance* && /usr/local/radiance/bin/gendaymtx -version || true
ENV RADIANCE_PATH=/usr/local/radiance RAYPATH=/usr/local/radiance/lib PATH=/usr/local/radiance/bin:$PATH
WORKDIR /app
COPY pyproject.toml requirements.lock.txt ./
COPY packages ./packages
COPY services ./services
RUN pip install -r requirements.lock.txt && pip install --no-deps -e .
COPY data/precinct ./data/precinct
COPY data/recipes ./data/recipes
COPY data/weather ./data/weather
COPY --from=web /web/dist ./apps/web/dist
ENV AI_WEB_DIST=/app/apps/web/dist PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:${PORT}/healthz || exit 1
CMD ["sh", "-c", "uvicorn ai_api.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
