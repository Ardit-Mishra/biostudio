# Ardit BioCore - AI-Powered Molecular Intelligence Platform
# Dockerfile for a version-pinned containerized runtime

# 3.12 because that is what pyproject.toml requires-python declares, what CI
# runs, and what the served ADMET models were trained under. 3.11 here meant
# the image ran a different interpreter from every other environment.
#
# Pinned by digest, not by tag. `python:3.12-slim` is a moving target -- it is
# rebuilt whenever its base or security patches change -- so a tag alone lets
# the base drift under us. This digest is the multi-arch OCI index
# (linux/amd64, linux/arm64v8 and six others), so pinning it does not tie the
# build to one architecture. Re-resolve with:
#   docker buildx imagetools inspect python:3.12-slim
FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies.
#
# libexpat1 is required by RDKit's drawing code: rdkit.Chem.Draw.rdMolDraw2D
# links libexpat.so.1, so without it `from rdkit.Chem import Draw` raises
# ImportError, app.py fails at its top-level imports, and the container
# serves a traceback instead of the UI. This list was originally written for
# the rdkit-pypi 2022.9.5 wheel, which did not need it; the omission only
# became reachable once the image started installing current rdkit.
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libexpat1 \
    libxrender1 \
    libxext6 \
    libsm6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first so the install layer is cached independently of
# application code.
COPY pyproject.toml requirements.txt ./

# Install the exact runtime lock compiled from pyproject.toml: the same locked
# runtime dependency graph CI installs. CI additionally installs
# requirements-dev.txt (pytest and its test client); the image does not, and
# .dockerignore keeps tests/ out of it. So the two environments hold identical
# runtime dependencies and differ only by that test-only tier.
#
# This step was previously a hardcoded package list that had drifted from
# requirements.txt: it installed rdkit-pypi (a community wheel abandoned at
# 2022.9.5) instead of rdkit, and omitted py3Dmol and pyfamsa, both of which
# the app imports. There is now one dependency source, so that divergence
# cannot recur silently.
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p .streamlit

# Create Streamlit config
RUN echo '[server]\nport = 5000\naddress = "0.0.0.0"\nheadless = true\n\n[browser]\ngatherUsageStats = false' > .streamlit/config.toml

# Expose ports
EXPOSE 5000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000')"

# Default command: Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port", "5000", "--server.address", "0.0.0.0"]

# Alternative: Run both Streamlit and FastAPI
# CMD ["sh", "-c", "streamlit run app.py --server.port 5000 & uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000"]
