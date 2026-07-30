# backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Run schema extractor first to make sure it's ready and schema.json is built
RUN python schema_extractor.py

# Expose a default port (Render will override this with $PORT)
EXPOSE 8080

# Run Uvicorn and bind to $PORT (fallback to 8080 if not set)
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"
