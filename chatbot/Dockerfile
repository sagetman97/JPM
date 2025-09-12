FROM python:3.12-slim

WORKDIR /app

# Install essential build tools and dependencies for PDF/DOCX processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    build-essential \
    # Essential build tools
    pkg-config \
    # Dependencies for PDF/DOCX processing
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libtiff5-dev \
    libopenjp2-7-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    # Scientific computing dependencies for matplotlib, numpy, scipy, pandas
    libblas-dev \
    liblapack-dev \
    gfortran \
    libgfortran5 \
    libopenblas-dev \
    libhdf5-dev \
    libnetcdf-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary=all -r requirements.txt

# Install Playwright browsers and system dependencies
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
