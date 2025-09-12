FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and upgrade pip/setuptools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    # Essential build tools
    pkg-config \
    # Scientific computing dependencies for numpy, pandas, scipy, scikit-learn
    libblas-dev \
    liblapack-dev \
    gfortran \
    libgfortran5 \
    libopenblas-dev \
    # Data format libraries
    libhdf5-dev \
    libnetcdf-dev \
    # Additional dependencies for data processing
    libxml2-dev \
    libxslt1-dev \
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
