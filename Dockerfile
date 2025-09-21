FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY backend/ backend/
COPY .env .env

# Cloud Run expects the app on port 8080
EXPOSE 8080

# Use $PORT instead of hardcoded 8000
# CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8080"]
CMD exec uvicorn backend.api:app --host 0.0.0.0 --port $PORT

