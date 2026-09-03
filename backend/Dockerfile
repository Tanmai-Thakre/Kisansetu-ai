FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2 and curl (for healthcheck)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create uploads directory for quality image storage
RUN mkdir -p /app/uploads/quality

EXPOSE 8000

# Default: production (no --reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
