FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY Service.py .
COPY Game.py .
COPY FilterPage.html .
COPY Logo.svg .
COPY games.json .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "Service:app", "--host", "0.0.0.0", "--port", "8000"]
