FROM python:3.12-slim

WORKDIR /app

# Install minimal system dependencies (backend doesn't use scientific computing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    # Essential build tools
    pkg-config \
    # Basic dependencies for HTTP client and file processing
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip setuptools wheel

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary=all -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
