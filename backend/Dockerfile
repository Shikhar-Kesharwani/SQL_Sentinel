FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install fastapi uvicorn sqlalchemy python-dotenv anthropic sentence-transformers sqlglot requests

# Copy application code
COPY . .

# Run schema extractor first to make sure it's ready and schema.json is built
RUN python schema_extractor.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
