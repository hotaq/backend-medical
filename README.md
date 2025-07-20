# Medical Triage-BOTS System

A comprehensive AI-powered medical triage system using FastAPI backend and Next.js frontend with Docker containerization.

## 🏗️ Project Structure

```
backend/
├── app/                    # Main application code
│   ├── agents/            # AI agents (ChiefBOT, VisionBOT, TextBOT)
│   ├── database/          # Database models and operations
│   └── models/            # Pydantic models
├── frontend/              # Next.js React frontend
├── config/                # Configuration files
│   ├── nginx.conf         # Nginx reverse proxy config
│   ├── init-db/           # Database initialization scripts
│   ├── monitoring/        # Prometheus & Grafana configs
│   └── ssl/               # SSL certificates
├── scripts/               # Utility scripts
│   ├── start-dev.sh       # Start development environment
│   ├── stop-dev.sh        # Stop development environment
│   └── migrate_db.py      # Database migration script
├── docs/                  # Documentation
├── tests/                 # Test files
├── logs/                  # Application logs
└── uploads/               # File uploads
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd medical/backend
   ```

2. **Start the development environment**
   ```bash
   ./scripts/start-dev.sh
   ```

   This will:
   - Build all Docker images
   - Start PostgreSQL, Redis, Backend, and Frontend
   - Set up the database with initial data
   - Display service URLs when ready

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Stop Development Environment

```bash
./scripts/stop-dev.sh
```

For complete cleanup (removes data):
```bash
./scripts/stop-dev.sh --clean-all
```

## 🐳 Docker Configurations

### Development (docker-compose.dev.yml)
- Fast startup with hot reloading
- Backend and Frontend only with PostgreSQL and Redis
- Volume mounts for live code changes

### Production (docker-compose.yml)
- Full stack with Nginx reverse proxy
- Monitoring with Prometheus and Grafana
- SSL support and production optimizations

## 📚 API Endpoints

### Core Endpoints
- `GET /` - Root endpoint with system info
- `GET /health` - Health check with component status
- `POST /triage` - Main triage processing endpoint
- `GET /docs` - Interactive API documentation

### Triage Endpoint
The main `/triage` endpoint accepts:
- Text symptoms and complaints
- Medical images
- Structured patient data
- Vital signs and medical history

## 🗄️ Database

PostgreSQL database with the following main tables:
- `users` - System users
- `triage_cases` - Patient triage cases
- `bot_interactions` - AI bot interaction logs
- `medical_assessments` - Medical assessment results
- `audit_logs` - System audit trail

## 🤖 AI Agents

### ChiefBOT
- Orchestrates the triage process
- Coordinates between VisionBOT and TextBOT
- Makes final triage decisions

### VisionBOT
- Processes medical images
- Analyzes visual symptoms
- Extracts medical information from images

### TextBOT
- Processes text-based symptoms
- Analyzes patient complaints
- Generates medical assessments

## 🔧 Development Commands

### Docker Operations
```bash
# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Restart a specific service
docker-compose -f docker-compose.dev.yml restart backend

# Execute commands in containers
docker-compose -f docker-compose.dev.yml exec backend bash
docker-compose -f docker-compose.dev.yml exec frontend sh
```

### Database Operations
```bash
# Run migrations
docker-compose -f docker-compose.dev.yml exec backend python scripts/migrate_db.py

# Access PostgreSQL
docker-compose -f docker-compose.dev.yml exec postgres psql -U medical_user -d medical_triage_bots
```

## 📊 Monitoring (Production)

When using the full production setup:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin123)

## 🧪 Testing

Run tests inside the backend container:
```bash
docker-compose -f docker-compose.dev.yml exec backend pytest
```

## 🔒 Security

- Environment variables for sensitive data
- CORS protection
- Rate limiting via Nginx
- SSL/TLS support in production
- Database connection encryption

## 📝 Environment Variables

Key environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `LOG_LEVEL` - Logging level (debug, info, warning, error)
- `ENVIRONMENT` - Environment type (development, production)

## 🐛 Troubleshooting

### Common Issues

1. **Docker not starting**
   - Ensure Docker daemon is running
   - Check available disk space and memory

2. **Port conflicts**
   - Check if ports 3000, 8000, 5432, 6379 are available
   - Modify docker-compose.dev.yml if needed

3. **Database connection issues**
   - Wait for PostgreSQL to be fully initialized
   - Check database logs: `docker-compose -f docker-compose.dev.yml logs postgres`

4. **Frontend build errors**
   - Ensure package-lock.json exists in frontend/
   - Clear node_modules and rebuild if needed

### Logs and Debugging

```bash
# View all logs
docker-compose -f docker-compose.dev.yml logs -f

# View specific service logs
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend

# Check container status
docker-compose -f docker-compose.dev.yml ps
```

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation as needed
4. Use the development environment for testing

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Ensure all prerequisites are met
4. Check Docker and container status