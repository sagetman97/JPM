FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright and build tools
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary=all -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
