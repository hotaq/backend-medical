#!/bin/bash

# Development startup script for Medical Triage-BOTS System
# This script starts the backend and frontend services for development

set -e

echo "🏥 Medical Triage-BOTS Development Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_success "Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install docker-compose and try again."
    exit 1
fi

# Check if .env file exists, create from example if not
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        print_warning ".env file not found, copying from .env.example"
        cp .env.example .env
        print_status "Please review and update .env file with your settings"
    else
        print_error ".env file not found and no .env.example available"
        exit 1
    fi
fi

# Navigate to the backend directory
cd "$(dirname "$0")/.."

print_status "Current directory: $(pwd)"

# Create necessary directories if they don't exist
print_status "Creating necessary directories..."
mkdir -p logs uploads config/ssl models models/transformers models/datasets

# Set environment variables for MedGemma
export HF_TOKEN=${HF_TOKEN:-"your_huggingface_token_here"}
export MEDGEMMA_MODEL_SIZE=${MEDGEMMA_MODEL_SIZE:-"medium"}
export MEDGEMMA_DEPLOYMENT_MODE=${MEDGEMMA_DEPLOYMENT_MODE:-"development"}
export MEDGEMMA_QUANTIZATION=${MEDGEMMA_QUANTIZATION:-"true"}

print_status "MedGemma Configuration:"
echo "  Model Size: $MEDGEMMA_MODEL_SIZE"
echo "  Deployment Mode: $MEDGEMMA_DEPLOYMENT_MODE"
echo "  Quantization: $MEDGEMMA_QUANTIZATION"
echo "  HF Token: ${HF_TOKEN:0:10}..." # Show only first 10 chars for security

# Stop any existing containers
print_status "Stopping any existing containers..."
docker-compose -f docker-compose.dev.yml down --remove-orphans

# Remove any orphaned volumes (optional - uncomment if needed)
# print_warning "Removing orphaned volumes..."
# docker volume prune -f

# Build the images with HF token
print_status "Building Docker images with MedGemma support..."
docker-compose -f docker-compose.dev.yml build --no-cache --build-arg HF_TOKEN=${HF_TOKEN}

# Start the services
print_status "Starting services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."

# Function to wait for a service to be healthy
wait_for_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.dev.yml ps "$service_name" | grep -q "healthy\|Up"; then
            print_success "$service_name is ready"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "$service_name failed to start within expected time"
    return 1
}

# Wait for each service
print_status "Checking PostgreSQL..."
wait_for_service postgres

print_status "Checking Redis..."
wait_for_service redis

print_status "Checking Backend..."
wait_for_service backend

print_status "Checking Frontend..."
wait_for_service frontend

echo ""
print_success "All services are running!"
echo ""
echo "🌐 Service URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "📊 Database:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "🤖 MedGemma AI:"
echo "   Model Size: $MEDGEMMA_MODEL_SIZE"
echo "   Quantization: $MEDGEMMA_QUANTIZATION"
echo "   Cache Directory: ./models"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "   Stop services: docker-compose -f docker-compose.dev.yml down"
echo "   Restart a service: docker-compose -f docker-compose.dev.yml restart <service>"
echo "   Test MedGemma: docker-compose -f docker-compose.dev.yml exec backend python scripts/test_medgemma.py"
echo "   Interactive shell: docker-compose -f docker-compose.dev.yml exec backend python scripts/docker-entrypoint.sh shell"
echo ""
print_status "To view real-time logs, run:"
echo "   docker-compose -f docker-compose.dev.yml logs -f"
echo ""
print_warning "Press Ctrl+C to stop watching logs, or run 'docker-compose -f docker-compose.dev.yml down' to stop all services"

# Follow logs
docker-compose -f docker-compose.dev.yml logs -f
