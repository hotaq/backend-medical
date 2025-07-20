#!/usr/bin/env python3
"""
Startup Script for Medical Triage-BOTS FastAPI Application

This script provides a convenient way to start the FastAPI server with
proper configuration and environment setup.

Usage:
    python run_api.py                    # Development mode
    python run_api.py --prod             # Production mode
    python run_api.py --host 0.0.0.0     # Custom host
    python run_api.py --port 8080        # Custom port
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    import uvicorn
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required packages: {e}")
    print("Please install requirements: pip install -r api_requirements.txt")
    sys.exit(1)


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('triage_api.log')
        ]
    )


def load_environment():
    """Load environment variables from .env file"""
    env_file = backend_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print("ℹ️  No .env file found, using default configuration")


def validate_environment():
    """Validate required environment variables and setup"""
    issues = []

    # Check if database file can be created
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./medical_triage_bots.db")
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite+aiosqlite:///", "")
        db_dir = Path(db_path).parent
        if not db_dir.exists():
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created database directory: {db_dir}")
            except Exception as e:
                issues.append(f"Cannot create database directory {db_dir}: {e}")

    # Check if required app modules exist
    required_modules = [
        "app/agents/chief_bot.py",
        "app/models/triage_case.py",
        "app/database/config.py",
        "app/database/crud.py",
        "app/database/models.py"
    ]

    for module_path in required_modules:
        if not (backend_dir / module_path).exists():
            issues.append(f"Missing required module: {module_path}")

    if issues:
        print("❌ Environment validation failed:")
        for issue in issues:
            print(f"   - {issue}")
        return False

    print("✅ Environment validation passed")
    return True


async def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        # Test database connection
        from app.database.config import check_database_health
        db_health = await check_database_health()
        if db_health["status"] != "healthy":
            print(f"⚠️  Database health check failed: {db_health}")
            return False

        print("✅ Database connection verified")
        return True

    except Exception as e:
        print(f"❌ Dependency check failed: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Medical Triage-BOTS API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", default=True, help="Enable auto-reload")
    parser.add_argument("--prod", action="store_true", help="Production mode")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--check-only", action="store_true", help="Only check environment, don't start server")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    print("🏥 Medical Triage-BOTS FastAPI Server")
    print("=" * 50)

    # Load environment
    load_environment()

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Check dependencies
    async def run_checks():
        return await check_dependencies()

    deps_ok = asyncio.run(run_checks())
    if not deps_ok:
        print("❌ Dependency checks failed")
        sys.exit(1)

    if args.check_only:
        print("✅ All checks passed - environment ready")
        return

    # Configure for production or development
    if args.prod:
        args.reload = False
        args.log_level = "warning"
        print("🚀 Starting in PRODUCTION mode")
    else:
        print("🛠️  Starting in DEVELOPMENT mode")

    # Server configuration
    server_config = {
        "app": "main:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "reload": args.reload and not args.prod,
        "workers": args.workers if args.prod else 1,
        "access_log": True,
        "use_colors": True,
    }

    if args.prod:
        # Production-specific settings
        server_config.update({
            "proxy_headers": True,
            "forwarded_allow_ips": "*",
        })

    print(f"🌐 Starting server at http://{args.host}:{args.port}")
    print(f"📚 API documentation available at http://{args.host}:{args.port}/docs")
    print(f"🔄 Auto-reload: {'enabled' if server_config['reload'] else 'disabled'}")
    print(f"👥 Workers: {server_config['workers']}")
    print()

    try:
        uvicorn.run(**server_config)
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
