# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install them
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Download the spaCy NLP model required by Presidio
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application files
COPY backend /app/backend
COPY frontend /app/frontend
COPY vault /app/vault
COPY nlp /app/nlp
COPY regex_pipeline /app/regex_pipeline

EXPOSE 5001

# Command to run the Flask application
CMD ["python", "backend/app.py"]
