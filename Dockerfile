FROM python:3.11-slim

WORKDIR /app/Backend

# Install requirements first for better caching
COPY Src/Backend/Requirements.txt .

RUN pip install --no-cache-dir -r Requirements.txt

WORKDIR /app
COPY Src/ .

WORKDIR /app/Backend
CMD ["uvicorn", "Service:app", "--host", "0.0.0.0", "--port", "80"]