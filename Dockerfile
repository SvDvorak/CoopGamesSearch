FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY Service.py .
COPY Scraper.py .
COPY Game.py .
COPY GameStorage.py .
COPY FilterPage.html .
COPY Logo.svg .
COPY games.json .

# Command to run the application
CMD ["uvicorn", "Service:app", "--host", "0.0.0.0", "--port", "80"]
