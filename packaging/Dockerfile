# Fichier : packaging/Dockerfile
# Image de serving optimisée. Contexte de build = RACINE du repo :
#   docker build -f packaging/Dockerfile -t scoring-api:optimized .
# Le modèle est exporté AVANT le build (étape 1, packaging/model/) puis copié :
# l'image est autonome, ni le build ni le conteneur n'ont besoin d'accéder à MLflow.

# --- Stage 1 : builder — installe les dépendances dans /deps ---------------------------
FROM python:3.12-slim AS builder
WORKDIR /build
COPY packaging/requirements.txt .
# pip 25.2 reprend les téléchargements interrompus ; outil du builder uniquement.
RUN pip install --timeout=180 --retries=8 --no-cache-dir pip==25.2
RUN pip install --timeout=180 --retries=8 --resume-retries=10 --no-cache-dir --target=/deps -r requirements.txt
# Le runtime interdit déjà le bytecode : ne pas embarquer les caches du builder.
RUN python -c "from pathlib import Path; [p.unlink() for p in Path('/deps').rglob('*.pyc')]"

# --- Stage 2 : runtime — uniquement ce qui sert à répondre aux requêtes ---------------
FROM python:3.12-slim AS runtime
# UID fixe : Kubernetes (runAsNonRoot) exige un USER numérique pour vérifier le non-root.
RUN groupadd --gid 10001 ml \
    && useradd --uid 10001 --gid ml --no-create-home --shell /usr/sbin/nologin ml

WORKDIR /app
COPY --from=builder /deps /deps
ENV PYTHONPATH=/deps \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Même arborescence que le repo : serve.py trouve dataset.yaml, src/ et le modèle sans
# configuration. Les fichiers restent à root : l'utilisateur ml ne peut que les lire.
COPY dataset.yaml ./
COPY src/__init__.py src/dataset_config.py src/
COPY packaging/app/__init__.py packaging/app/serve.py packaging/app/
# Le modèle change plus souvent que le code : dernière couche, pour profiter du cache.
COPY packaging/model/model.onnx packaging/model/metadata.json packaging/model/

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --start-interval=2s \
    CMD ["python", "-c", \
         "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

# Métadonnées (docker inspect) : passées au build, voir l'étape 4.2.
ARG VERSION=1.0.0
ARG MODEL_VERSION=unknown
LABEL org.opencontainers.image.title="scoring-api" \
      org.opencontainers.image.version="${VERSION}" \
      mlflow.model_name="scoring-model" \
      mlflow.model_alias="champion" \
      mlflow.model_version="${MODEL_VERSION}"

ENV APP_VERSION=${VERSION}

CMD ["python", "-m", "uvicorn", "app.serve:app", "--app-dir", "packaging", \
     "--host", "0.0.0.0", "--port", "8000"]
