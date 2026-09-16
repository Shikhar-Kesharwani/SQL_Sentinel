# ---- Builder ----
FROM python:3.11-slim AS builder
WORKDIR /build
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Production ----
FROM python:3.11-slim AS production
WORKDIR /app
RUN addgroup --system app && adduser --system --group app
COPY --from=builder /root/.local /home/app/.local
COPY backend/ ./backend/
RUN chown -R app:app /app
USER app
ENV PATH=/home/app/.local/bin:$PATH
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
