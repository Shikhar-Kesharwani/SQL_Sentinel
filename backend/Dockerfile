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

# Expose the FastAPI port
EXPOSE 8080

# Run Uvicorn in production mode (no reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
