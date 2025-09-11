#!/bin/bash

# RoboAdvisor EC2 Deployment Script
# This script deploys the RoboAdvisor application using Docker Compose

set -e  # Exit on any error

echo "🚀 Starting RoboAdvisor EC2 Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_warning "Please copy env.example to .env and fill in your values:"
    echo "  cp env.example .env"
    echo "  nano .env  # Edit with your actual values"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running!"
    print_warning "Please start Docker:"
    echo "  sudo systemctl start docker"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose not found!"
    print_warning "Please install Docker Compose:"
    echo "  sudo apt install docker-compose"
    exit 1
fi

print_status "Environment file found"
print_status "Docker is running"
print_status "Docker Compose is available"

# Stop any existing containers
print_warning "Stopping existing containers..."
docker-compose down --remove-orphans || true

# Build and start services
print_status "Building and starting services..."
docker-compose up -d --build

# Wait for services to be healthy
print_warning "Waiting for services to be healthy..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check Qdrant
if curl -f http://localhost:6333/health > /dev/null 2>&1; then
    print_status "Qdrant is healthy"
else
    print_error "Qdrant is not responding"
fi

# Check Backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "Backend is healthy"
else
    print_error "Backend is not responding"
fi

# Check Chatbot
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_status "Chatbot is healthy"
else
    print_error "Chatbot is not responding"
fi

# Show running containers
print_status "Running containers:"
docker-compose ps

# Show logs
print_warning "Recent logs:"
docker-compose logs --tail=20

print_status "Deployment complete!"
print_warning "Services are running on:"
echo "  - Qdrant: http://localhost:6333"
echo "  - Backend: http://localhost:8000"
echo "  - Chatbot: http://localhost:8001"
echo ""
print_warning "To view logs: docker-compose logs -f"
print_warning "To stop services: docker-compose down"
