#!/bin/bash

# Development stop script for Medical Triage-BOTS System
# This script stops all development services and cleans up

set -e

echo "🏥 Medical Triage-BOTS Development Cleanup"
echo "=========================================="

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

# Navigate to the backend directory
cd "$(dirname "$0")/.."

print_status "Current directory: $(pwd)"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed."
    exit 1
fi

# Parse command line arguments
CLEAN_VOLUMES=false
CLEAN_IMAGES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean-volumes)
            CLEAN_VOLUMES=true
            shift
            ;;
        --clean-images)
            CLEAN_IMAGES=true
            shift
            ;;
        --clean-all)
            CLEAN_VOLUMES=true
            CLEAN_IMAGES=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clean-volumes    Remove all volumes (will delete database data)"
            echo "  --clean-images     Remove built images"
            echo "  --clean-all        Remove both volumes and images"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Stop and remove containers
print_status "Stopping and removing containers..."
docker-compose -f docker-compose.dev.yml down --remove-orphans

print_success "Containers stopped and removed"

# Clean up volumes if requested
if [ "$CLEAN_VOLUMES" = true ]; then
    print_warning "Removing volumes (this will delete all database data)..."
    docker-compose -f docker-compose.dev.yml down -v

    # Remove specific volumes
    print_status "Removing named volumes..."
    docker volume rm medical_postgres_data_dev 2>/dev/null || true
    docker volume rm medical_redis_data_dev 2>/dev/null || true

    print_success "Volumes removed"
fi

# Clean up images if requested
if [ "$CLEAN_IMAGES" = true ]; then
    print_status "Removing built images..."

    # Get image names from docker-compose
    IMAGES=$(docker-compose -f docker-compose.dev.yml config | grep 'image:' | awk '{print $2}' | sort | uniq)

    # Remove images built by docker-compose
    docker-compose -f docker-compose.dev.yml down --rmi local 2>/dev/null || true

    # Remove any dangling images
    print_status "Removing dangling images..."
    docker image prune -f

    print_success "Images removed"
fi

# Clean up networks
print_status "Cleaning up networks..."
docker network prune -f

# Show remaining Docker resources
print_status "Docker cleanup summary:"
echo ""
echo "📊 Remaining Docker resources:"
echo "   Containers: $(docker ps -a -q | wc -l)"
echo "   Images: $(docker images -q | wc -l)"
echo "   Volumes: $(docker volume ls -q | wc -l)"
echo "   Networks: $(docker network ls -q | wc -l)"
echo ""

if [ "$CLEAN_VOLUMES" = true ] || [ "$CLEAN_IMAGES" = true ]; then
    print_warning "Deep cleanup performed. Next startup will take longer due to rebuilding."
else
    print_status "Quick cleanup performed. To perform deep cleanup, use:"
    echo "   $0 --clean-all"
fi

echo ""
print_success "Development environment stopped successfully!"
echo ""
print_status "To start the services again, run:"
echo "   ./scripts/start-dev.sh"
echo ""
