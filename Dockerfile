# C31-C35: somente inferência e frontend; nenhum CSV é copiado.
FROM python:3.14.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

COPY requirements-deploy.txt ./
RUN python -m pip install --no-cache-dir -r requirements-deploy.txt \
    && python -m pip check

RUN useradd --create-home --uid 10001 appuser
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser frontend/ ./frontend/
COPY --chown=appuser:appuser artifacts/ridge-v1.metadata.json ./artifacts/

RUN --mount=type=secret,id=ridge_v1_joblib_b64,required=true \
    base64 -d /run/secrets/ridge_v1_joblib_b64 \
      > /srv/app/artifacts/ridge-v1.joblib \
    && echo "f362ca5d4b01e834901bb446a5029b1f9fb7a1636c7e87374dfd1fbb5e96bf5f  /srv/app/artifacts/ridge-v1.joblib" \
      | sha256sum -c - \
    && chown appuser:appuser /srv/app/artifacts/ridge-v1.joblib

USER appuser
EXPOSE 10000
# Render define PORT; local usa 10000.
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
