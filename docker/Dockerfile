# syntax=docker/dockerfile:1

# Builder stage
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy all files for pip install .
COPY . .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir setuptools wheel && \
    pip install --no-cache-dir .

# Final stage
FROM python:3.13-slim

WORKDIR /app

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
EXPOSE 8000

# Run FastAPI server
CMD ["uvicorn", "aitester.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
