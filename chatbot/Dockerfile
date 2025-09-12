FROM python:3.12-slim

WORKDIR /app

# Install essential build tools, PDF/DOCX processing, and Playwright dependencies
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
    # Playwright browser dependencies (Debian Trixie compatible)
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libx11-6 \
    libxext6 \
    libxfixes3 \
    libxcb1 \
    libxcb-dri3-0 \
    libxcb-present0 \
    libxcb-sync1 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxcb-randr0 \
    libxcb-render0 \
    libxcb-shape0 \
    libxcb-util1 \
    libxcb-image0 \
    libxcb-icccm4 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-xfixes0 \
    libxcb-shm0 \
    libxcb-cursor0 \
    # Font packages (Debian Trixie compatible)
    fonts-liberation \
    fonts-unifont \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary=all -r requirements.txt

# Install Playwright browsers (system dependencies already installed above)
RUN playwright install chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
