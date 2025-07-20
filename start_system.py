#!/usr/bin/env python3
"""
Combined Startup Script for Medical Triage-BOTS System
Frontend + Backend Integration

This script provides a convenient way to start both the FastAPI backend
and React frontend together with proper dependency checking and monitoring.

Usage:
    python start_system.py                    # Start both frontend and backend
    python start_system.py --backend-only     # Start only backend
    python start_system.py --frontend-only    # Start only frontend
    python start_system.py --check            # Check dependencies only
"""

import argparse
import asyncio
import logging
import os
import subprocess
import sys
import time
import signal
from pathlib import Path
from typing import List, Optional
import threading
import queue

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('system_startup.log')
    ]
)
logger = logging.getLogger(__name__)

class SystemManager:
    """Manages the startup and monitoring of the Medical Triage-BOTS system"""

    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.frontend_dir = self.backend_dir / "frontend"
        self.processes = {}
        self.shutdown_event = threading.Event()

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        logger.info("🔍 Checking system dependencies...")

        issues = []

        # Check Python version
        if sys.version_info < (3, 8):
            issues.append(f"Python 3.8+ required, found {sys.version}")
        else:
            logger.info(f"✅ Python version: {sys.version.split()[0]}")

        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                logger.info(f"✅ Node.js version: {node_version}")

                # Check if version is 18+
                version_num = int(node_version.lstrip('v').split('.')[0])
                if version_num < 18:
                    issues.append(f"Node.js 18+ required, found {node_version}")
            else:
                issues.append("Node.js not found")
        except FileNotFoundError:
            issues.append("Node.js not installed")

        # Check npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                npm_version = result.stdout.strip()
                logger.info(f"✅ npm version: {npm_version}")
            else:
                issues.append("npm not found")
        except FileNotFoundError:
            issues.append("npm not installed")

        # Check Python packages
        required_packages = [
            'fastapi', 'uvicorn', 'sqlalchemy', 'aiosqlite',
            'pydantic', 'asyncio', 'httpx'
        ]

        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✅ Python package: {package}")
            except ImportError:
                issues.append(f"Python package missing: {package}")

        # Check if backend files exist
        required_backend_files = [
            'main.py',
            'app/agents/chief_bot.py',
            'app/models/triage_case.py',
            'app/database/config.py'
        ]

        for file_path in required_backend_files:
            full_path = self.backend_dir / file_path
            if not full_path.exists():
                issues.append(f"Backend file missing: {file_path}")
            else:
                logger.info(f"✅ Backend file: {file_path}")

        # Check if frontend directory exists and has package.json
        if not self.frontend_dir.exists():
            issues.append("Frontend directory not found")
        else:
            package_json = self.frontend_dir / "package.json"
            if not package_json.exists():
                issues.append("Frontend package.json not found")
            else:
                logger.info("✅ Frontend structure found")

        # Check database
        db_path = self.backend_dir / "medical_triage_bots.db"
        if db_path.exists():
            logger.info("✅ Database file exists")
        else:
            logger.warning("⚠️ Database file not found - will be created on first run")

        if issues:
            logger.error("❌ Dependency check failed:")
            for issue in issues:
                logger.error(f"   - {issue}")
            return False

        logger.info("✅ All dependencies satisfied!")
        return True

    def install_frontend_dependencies(self) -> bool:
        """Install frontend dependencies if needed"""
        logger.info("📦 Checking frontend dependencies...")

        node_modules = self.frontend_dir / "node_modules"
        if not node_modules.exists():
            logger.info("📦 Installing frontend dependencies (this may take a few minutes)...")
            try:
                process = subprocess.run(
                    ['npm', 'install'],
                    cwd=self.frontend_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )

                if process.returncode == 0:
                    logger.info("✅ Frontend dependencies installed successfully")
                    return True
                else:
                    logger.error(f"❌ npm install failed: {process.stderr}")
                    return False

            except subprocess.TimeoutExpired:
                logger.error("❌ npm install timed out after 5 minutes")
                return False
            except Exception as e:
                logger.error(f"❌ Error installing frontend dependencies: {e}")
                return False
        else:
            logger.info("✅ Frontend dependencies already installed")
            return True

    def wait_for_backend(self, timeout: int = 30) -> bool:
        """Wait for backend to be ready"""
        logger.info("⏳ Waiting for backend to be ready...")

        for i in range(timeout):
            try:
                import httpx
                response = httpx.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    logger.info("✅ Backend is ready!")
                    return True
            except:
                pass

            time.sleep(1)
            if i % 5 == 0:
                logger.info(f"   Still waiting... ({i}/{timeout}s)")

        logger.error("❌ Backend failed to start within timeout")
        return False

    def start_backend(self) -> Optional[subprocess.Popen]:
        """Start the FastAPI backend"""
        logger.info("🚀 Starting Medical Triage-BOTS Backend...")

        try:
            # Initialize database first
            logger.info("🏗️ Initializing database...")
            init_process = subprocess.run([
                sys.executable, '-c',
                '''
import asyncio
from app.database.config import init_database
asyncio.run(init_database())
print("Database initialized successfully!")
                '''
            ], cwd=self.backend_dir, capture_output=True, text=True)

            if init_process.returncode == 0:
                logger.info("✅ Database initialized")
            else:
                logger.warning(f"⚠️ Database initialization warning: {init_process.stderr}")

            # Start the backend server
            process = subprocess.Popen([
                sys.executable, 'main.py'
            ], cwd=self.backend_dir,
               stdout=subprocess.PIPE,
               stderr=subprocess.STDOUT,
               universal_newlines=True,
               bufsize=1)

            self.processes['backend'] = process

            # Start monitoring thread
            def monitor_backend():
                for line in process.stdout:
                    logger.info(f"[Backend] {line.strip()}")

            backend_thread = threading.Thread(target=monitor_backend, daemon=True)
            backend_thread.start()

            # Wait for backend to be ready
            if self.wait_for_backend():
                return process
            else:
                process.terminate()
                return None

        except Exception as e:
            logger.error(f"❌ Failed to start backend: {e}")
            return None

    def start_frontend(self) -> Optional[subprocess.Popen]:
        """Start the React frontend"""
        logger.info("🚀 Starting Medical Triage-BOTS Frontend...")

        try:
            # Check if we need to install dependencies
            if not self.install_frontend_dependencies():
                return None

            # Set environment variables
            env = os.environ.copy()
            env['NEXT_PUBLIC_API_URL'] = 'http://localhost:8000'
            env['NODE_ENV'] = 'development'

            # Start the frontend server
            process = subprocess.Popen([
                'npm', 'run', 'dev'
            ], cwd=self.frontend_dir,
               stdout=subprocess.PIPE,
               stderr=subprocess.STDOUT,
               universal_newlines=True,
               bufsize=1,
               env=env)

            self.processes['frontend'] = process

            # Start monitoring thread
            def monitor_frontend():
                for line in process.stdout:
                    if line.strip():
                        logger.info(f"[Frontend] {line.strip()}")

            frontend_thread = threading.Thread(target=monitor_frontend, daemon=True)
            frontend_thread.start()

            return process

        except Exception as e:
            logger.error(f"❌ Failed to start frontend: {e}")
            return None

    def shutdown_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("🛑 Shutdown signal received")
        self.shutdown_event.set()
        self.cleanup()

    def cleanup(self):
        """Clean up all processes"""
        logger.info("🧹 Cleaning up processes...")

        for name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info(f"🛑 Stopping {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {name}...")
                    process.kill()
                except Exception as e:
                    logger.error(f"Error stopping {name}: {e}")

        logger.info("✅ Cleanup complete")

    def run(self, backend_only: bool = False, frontend_only: bool = False):
        """Run the complete system"""

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.shutdown_handler)
        signal.signal(signal.SIGTERM, self.shutdown_handler)

        try:
            if not backend_only and not frontend_only:
                logger.info("🏥 Starting Complete Medical Triage-BOTS System")
                logger.info("=" * 60)

                # Start backend first
                backend_process = self.start_backend()
                if not backend_process:
                    logger.error("❌ Failed to start backend - aborting")
                    return False

                # Start frontend
                frontend_process = self.start_frontend()
                if not frontend_process:
                    logger.error("❌ Failed to start frontend - continuing with backend only")

                logger.info("🎉 System startup complete!")
                logger.info("🌐 Frontend: http://localhost:3000")
                logger.info("🔗 Backend API: http://localhost:8000")
                logger.info("📚 API Docs: http://localhost:8000/docs")

            elif backend_only:
                logger.info("🏥 Starting Backend Only")
                backend_process = self.start_backend()
                if not backend_process:
                    return False

                logger.info("🎉 Backend startup complete!")
                logger.info("🔗 Backend API: http://localhost:8000")
                logger.info("📚 API Docs: http://localhost:8000/docs")

            elif frontend_only:
                logger.info("🏥 Starting Frontend Only")
                frontend_process = self.start_frontend()
                if not frontend_process:
                    return False

                logger.info("🎉 Frontend startup complete!")
                logger.info("🌐 Frontend: http://localhost:3000")

            # Monitor processes
            logger.info("\n📊 System is running. Press Ctrl+C to stop.")
            logger.info("📝 Logs are being saved to system_startup.log")

            # Keep running until shutdown
            while not self.shutdown_event.is_set():
                time.sleep(1)

                # Check if processes are still running
                for name, process in list(self.processes.items()):
                    if process and process.poll() is not None:
                        logger.warning(f"⚠️ {name} process has stopped")
                        del self.processes[name]

                # If no processes are running, exit
                if not self.processes:
                    logger.info("🛑 All processes have stopped")
                    break

            return True

        except KeyboardInterrupt:
            logger.info("\n🛑 Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ System error: {e}")
        finally:
            self.cleanup()

        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Medical Triage-BOTS System Launcher")
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Start only the backend server"
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Start only the frontend server"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check dependencies only, don't start services"
    )
    parser.add_argument(
        "--no-deps-check",
        action="store_true",
        help="Skip dependency checking"
    )

    args = parser.parse_args()

    if args.backend_only and args.frontend_only:
        print("❌ Cannot specify both --backend-only and --frontend-only")
        sys.exit(1)

    system_manager = SystemManager()

    print("🏥 Medical Triage-BOTS System Launcher")
    print("=" * 50)

    # Check dependencies unless skipped
    if not args.no_deps_check:
        if not system_manager.check_dependencies():
            print("\n💡 To install missing dependencies:")
            print("   Backend: pip install -r api_requirements.txt")
            print("   Frontend: cd frontend && npm install")
            sys.exit(1)

    if args.check:
        print("✅ All dependencies satisfied - system ready to launch!")
        return

    # Run the system
    success = system_manager.run(
        backend_only=args.backend_only,
        frontend_only=args.frontend_only
    )

    if success:
        print("\n👋 Medical Triage-BOTS System shutdown complete")
    else:
        print("\n❌ System startup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
