# Ardit BioCore - AI-Powered Molecular Intelligence Platform
# Dockerfile for reproducible containerized environment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libxrender1 \
    libxext6 \
    libsm6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
# CRITICAL: NumPy must be <2.0 for RDKit compatibility
RUN pip install --no-cache-dir \
    "numpy>=1.24,<2.0" \
    rdkit-pypi>=2022.9.5 \
    streamlit>=1.51.0 \
    fastapi>=0.121.2 \
    uvicorn>=0.38.0 \
    scikit-learn>=1.7.2 \
    xgboost>=3.1.1 \
    umap-learn>=0.5.9 \
    pandas>=2.3.3 \
    scipy>=1.16.3 \
    matplotlib>=3.10.7 \
    seaborn>=0.13.2 \
    plotly>=6.4.0 \
    networkx>=3.5 \
    pyvis>=0.3.2 \
    biopython>=1.86 \
    pydantic>=2.12.4 \
    pillow>=12.0.0 \
    joblib>=1.5.2 \
    requests>=2.32.5

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
