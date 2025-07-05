FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY Src/Requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r Requirements.txt

# Copy application files
COPY Src/ .

# Command to run the application
CMD ["uvicorn", "Service:app", "--host", "0.0.0.0", "--port", "80"]