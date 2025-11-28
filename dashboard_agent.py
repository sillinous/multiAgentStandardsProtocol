#!/usr/bin/env python3
"""
🤖 APQC Dashboard Manager Agent

An intelligent agent that manages the setup and operation of APQC dashboards.

Features:
- Automatic environment detection
- Git repository synchronization
- Dependency installation
- Database initialization
- Server lifecycle management
- Health monitoring
- Error recovery

Usage:
    python dashboard_agent.py start     # Start all services
    python dashboard_agent.py stop      # Stop all services
    python dashboard_agent.py status    # Check service status
    python dashboard_agent.py setup     # One-time setup only
    python dashboard_agent.py restart   # Restart all services

Version: 1.0.0
Date: 2025-11-17
"""

import os
import sys
import subprocess
import time
import json
import signal
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import urllib.request
import urllib.error


@dataclass
class ServerInfo:
    """Information about a managed server"""
    name: str
    command: List[str]
    port: int
    health_endpoint: str
    process: Optional[subprocess.Popen] = None
    pid_file: Optional[str] = None


class DashboardAgent:
    """
    Intelligent agent for managing APQC dashboard services
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.pid_dir = self.project_root / ".agent_pids"
        self.pid_dir.mkdir(exist_ok=True)

        # Python command (will be detected in check_python)
        self.python_cmd = "python3"  # Default for Linux/Mac

        # Define managed servers
        self.servers = [
            ServerInfo(
                name="Main Dashboard",
                command=["python", "-m", "uvicorn", "src.superstandard.api.server:app",
                        "--host", "0.0.0.0", "--port", "8080"],
                port=8080,
                health_endpoint="http://localhost:8080/api/health",
                pid_file=str(self.pid_dir / "main_dashboard.pid")
            ),
            ServerInfo(
                name="APQC Factory",
                command=["python", "apqc_factory_server.py"],
                port=8765,
                health_endpoint="http://localhost:8765/api/health",
                pid_file=str(self.pid_dir / "apqc_factory.pid")
            )
        ]

    def update_server_commands(self):
        """Update server commands with detected Python command"""
        self.servers[0].command = [self.python_cmd, "-m", "uvicorn", "src.superstandard.api.server:app",
                                   "--host", "0.0.0.0", "--port", "8080"]
        self.servers[1].command = [self.python_cmd, "apqc_factory_server.py"]

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "AGENT": "🤖"
        }
        icon = icons.get(level, "ℹ️")
        print(f"[{timestamp}] {icon} {message}")

    def run_command(self, cmd: List[str], cwd: Optional[str] = None,
                   capture_output: bool = True) -> Tuple[bool, str]:
        """
        Execute a shell command

        Returns:
            Tuple of (success: bool, output: str)
        """
        try:
            if capture_output:
                result = subprocess.run(
                    cmd,
                    cwd=cwd or str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                return result.returncode == 0, result.stdout + result.stderr
            else:
                result = subprocess.run(
                    cmd,
                    cwd=cwd or str(self.project_root),
                    timeout=300
                )
                return result.returncode == 0, ""
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, f"Command failed: {e}"

    def check_python(self) -> bool:
        """Verify Python installation"""
        self.log("Checking Python installation...", "AGENT")
        # Try python3 first (Linux/Mac), then python (Windows)
        for cmd in ["python3", "python"]:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True
                )
                version = result.stdout.strip()
                self.log(f"Found {version} (using '{cmd}')", "SUCCESS")
                # Store which command works for later use
                self.python_cmd = cmd
                return True
            except FileNotFoundError:
                continue

        self.log("Python not found! Please install Python 3.8+", "ERROR")
        return False

    def check_git(self) -> bool:
        """Verify Git installation"""
        self.log("Checking Git installation...", "AGENT")
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True
            )
            version = result.stdout.strip()
            self.log(f"Found {version}", "SUCCESS")
            return True
        except FileNotFoundError:
            self.log("Git not found! Please install Git", "ERROR")
            return False

    def sync_repository(self) -> bool:
        """Synchronize local repository with remote"""
        self.log("Synchronizing repository with GitHub...", "AGENT")

        # Fetch from remote
        self.log("Fetching latest changes...", "INFO")
        success, output = self.run_command(["git", "fetch", "origin"])
        if not success:
            self.log(f"Failed to fetch: {output}", "ERROR")
            return False

        # Check current branch
        success, branch = self.run_command(["git", "branch", "--show-current"])
        if not success:
            self.log("Failed to detect current branch", "ERROR")
            return False

        branch = branch.strip()
        self.log(f"Current branch: {branch}", "INFO")

        # Pull latest changes
        self.log(f"Pulling latest changes from origin/{branch}...", "INFO")
        success, output = self.run_command(["git", "pull", "origin", branch])
        if not success:
            self.log(f"Pull failed: {output}", "WARNING")
            self.log("Attempting hard reset to match remote...", "INFO")
            success, output = self.run_command(["git", "reset", "--hard", f"origin/{branch}"])
            if not success:
                self.log(f"Reset failed: {output}", "ERROR")
                return False

        self.log("Repository synchronized successfully!", "SUCCESS")
        return True

    def install_dependencies(self) -> bool:
        """Install required Python packages"""
        self.log("Installing Python dependencies...", "AGENT")

        packages = [
            "fastapi",
            "uvicorn",
            "jinja2",
            "pydantic",
            "python-multipart"
        ]

        self.log(f"Installing: {', '.join(packages)}", "INFO")

        # Use python -m pip for better compatibility
        success, output = self.run_command(
            [self.python_cmd, "-m", "pip", "install"] + packages,
            capture_output=True
        )

        if success:
            self.log("Dependencies installed successfully!", "SUCCESS")
            return True
        else:
            self.log(f"Failed to install dependencies: {output}", "ERROR")
            return False

    def initialize_database(self) -> bool:
        """Initialize APQC agent database"""
        self.log("Initializing APQC database...", "AGENT")

        db_file = self.project_root / "apqc_agent_configs.db"

        # Check if database already exists
        if db_file.exists():
            self.log("Database already exists, checking...", "INFO")
            # Could add database validation here

        self.log("Running initialization...", "INFO")
        success, output = self.run_command(
            [self.python_cmd, "apqc_agent_factory.py", "--init"],
            capture_output=True
        )

        if success and "613 agent" in output:
            self.log("Database initialized with 613 agents!", "SUCCESS")
            return True
        elif success:
            self.log("Database initialization completed", "SUCCESS")
            return True
        else:
            self.log(f"Database initialization failed: {output}", "ERROR")
            return False

    def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return True
        except OSError:
            return False

    def check_server_health(self, url: str, timeout: int = 2) -> bool:
        """Check if a server is healthy via HTTP"""
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.status == 200
        except (urllib.error.URLError, urllib.error.HTTPError, Exception):
            return False

    def start_server(self, server: ServerInfo) -> bool:
        """Start a single server"""
        self.log(f"Starting {server.name} on port {server.port}...", "AGENT")

        # Check if port is available
        if not self.check_port_available(server.port):
            self.log(f"Port {server.port} is already in use!", "WARNING")

            # Check if it's our server that's already running
            if self.check_server_health(server.health_endpoint):
                self.log(f"{server.name} is already running", "INFO")
                return True
            else:
                self.log(f"Port {server.port} is blocked by another process", "ERROR")
                return False

        # Start the server process
        try:
            # Set environment for server
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"

            # Start process
            process = subprocess.Popen(
                server.command,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )

            server.process = process

            # Save PID
            with open(server.pid_file, 'w') as f:
                f.write(str(process.pid))

            # Wait for server to start
            self.log(f"Waiting for {server.name} to start...", "INFO")
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(1)
                if self.check_server_health(server.health_endpoint):
                    self.log(f"{server.name} started successfully!", "SUCCESS")
                    return True

                # Check if process died
                if process.poll() is not None:
                    self.log(f"{server.name} process terminated unexpectedly", "ERROR")
                    return False

            self.log(f"{server.name} failed to respond within {max_attempts} seconds", "ERROR")
            return False

        except Exception as e:
            self.log(f"Failed to start {server.name}: {e}", "ERROR")
            return False

    def stop_server(self, server: ServerInfo) -> bool:
        """Stop a single server"""
        self.log(f"Stopping {server.name}...", "AGENT")

        # Try to read PID from file
        if server.pid_file and os.path.exists(server.pid_file):
            try:
                with open(server.pid_file, 'r') as f:
                    pid = int(f.read().strip())

                # Kill process
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(2)

                    # Check if still running
                    try:
                        os.kill(pid, 0)  # Test if process exists
                        # Still running, force kill
                        os.kill(pid, signal.SIGKILL)
                        time.sleep(1)
                    except ProcessLookupError:
                        pass  # Process is gone

                    self.log(f"{server.name} stopped", "SUCCESS")
                except ProcessLookupError:
                    self.log(f"{server.name} was not running", "INFO")

                # Remove PID file
                os.remove(server.pid_file)

            except (ValueError, FileNotFoundError) as e:
                self.log(f"Could not read PID file: {e}", "WARNING")

        # Also try to kill by port (platform-specific)
        if platform.system() == "Windows":
            self.run_command(
                ["taskkill", "/F", "/FI", f"WINDOWTITLE eq *{server.name}*"],
                capture_output=True
            )
        else:
            # Unix-like systems
            self.run_command(
                ["pkill", "-f", f"port {server.port}"],
                capture_output=True
            )

        return True

    def get_status(self) -> Dict[str, any]:
        """Get status of all servers"""
        status = {
            "servers": [],
            "all_healthy": True
        }

        for server in self.servers:
            server_status = {
                "name": server.name,
                "port": server.port,
                "running": False,
                "healthy": False,
                "pid": None
            }

            # Check if PID file exists
            if server.pid_file and os.path.exists(server.pid_file):
                try:
                    with open(server.pid_file, 'r') as f:
                        pid = int(f.read().strip())
                        server_status["pid"] = pid

                        # Check if process is running
                        try:
                            os.kill(pid, 0)
                            server_status["running"] = True
                        except ProcessLookupError:
                            server_status["running"] = False
                except (ValueError, FileNotFoundError):
                    pass

            # Check health endpoint
            server_status["healthy"] = self.check_server_health(server.health_endpoint)

            if not server_status["healthy"]:
                status["all_healthy"] = False

            status["servers"].append(server_status)

        return status

    def setup(self) -> bool:
        """Run complete setup"""
        self.log("=" * 70, "INFO")
        self.log("🤖 APQC Dashboard Setup Agent", "AGENT")
        self.log("=" * 70, "INFO")

        # Step 1: Check prerequisites
        if not self.check_python():
            return False

        # Update server commands with detected Python command
        self.update_server_commands()

        if not self.check_git():
            return False

        # Step 2: Sync repository
        if not self.sync_repository():
            return False

        # Step 3: Install dependencies
        if not self.install_dependencies():
            return False

        # Step 4: Initialize database
        if not self.initialize_database():
            return False

        self.log("=" * 70, "INFO")
        self.log("Setup completed successfully! 🎉", "SUCCESS")
        self.log("=" * 70, "INFO")

        return True

    def start(self) -> bool:
        """Start all services"""
        self.log("=" * 70, "INFO")
        self.log("🤖 Starting APQC Dashboard Services", "AGENT")
        self.log("=" * 70, "INFO")

        # Detect Python command if not already done
        if not hasattr(self, 'python_cmd') or self.python_cmd == "python3":
            self.check_python()
            self.update_server_commands()

        all_started = True
        for server in self.servers:
            if not self.start_server(server):
                all_started = False

        if all_started:
            self.log("=" * 70, "INFO")
            self.log("All services started successfully! 🎉", "SUCCESS")
            self.log("=" * 70, "INFO")
            self.log("", "INFO")
            self.log("📊 Access the dashboards:", "INFO")
            self.log("   Main Dashboard: http://localhost:8080/dashboard", "INFO")
            self.log("   APQC Factory:   http://localhost:8765/apqc", "INFO")
            self.log("", "INFO")
            self.log("To stop services, run: python dashboard_agent.py stop", "INFO")
            self.log("=" * 70, "INFO")
        else:
            self.log("Some services failed to start", "ERROR")

        return all_started

    def stop(self) -> bool:
        """Stop all services"""
        self.log("=" * 70, "INFO")
        self.log("🤖 Stopping APQC Dashboard Services", "AGENT")
        self.log("=" * 70, "INFO")

        for server in self.servers:
            self.stop_server(server)

        self.log("All services stopped", "SUCCESS")
        return True

    def show_status(self):
        """Display status of all services"""
        self.log("=" * 70, "INFO")
        self.log("🤖 APQC Dashboard Services Status", "AGENT")
        self.log("=" * 70, "INFO")

        status = self.get_status()

        for server_status in status["servers"]:
            status_icon = "🟢" if server_status["healthy"] else "🔴"
            self.log(f"{status_icon} {server_status['name']} (Port {server_status['port']})", "INFO")

            if server_status["running"]:
                self.log(f"   Process: Running (PID {server_status['pid']})", "INFO")
            else:
                self.log(f"   Process: Not Running", "INFO")

            if server_status["healthy"]:
                self.log(f"   Health: Healthy ✓", "SUCCESS")
            else:
                self.log(f"   Health: Not Responding ✗", "ERROR")

            self.log("", "INFO")

        if status["all_healthy"]:
            self.log("All systems operational! 🎉", "SUCCESS")
        else:
            self.log("Some systems are not responding", "WARNING")

        self.log("=" * 70, "INFO")

    def restart(self) -> bool:
        """Restart all services"""
        self.log("Restarting all services...", "AGENT")
        self.stop()
        time.sleep(2)
        return self.start()


def main():
    """Main entry point"""
    agent = DashboardAgent()

    if len(sys.argv) < 2:
        print("Usage: python dashboard_agent.py [setup|start|stop|status|restart]")
        print("")
        print("Commands:")
        print("  setup    - Run complete setup (sync, install, initialize)")
        print("  start    - Start all dashboard services")
        print("  stop     - Stop all dashboard services")
        print("  status   - Show status of all services")
        print("  restart  - Restart all services")
        print("")
        print("Examples:")
        print("  python dashboard_agent.py setup")
        print("  python dashboard_agent.py start")
        print("  python dashboard_agent.py status")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "setup":
        success = agent.setup()
        sys.exit(0 if success else 1)

    elif command == "start":
        success = agent.start()
        sys.exit(0 if success else 1)

    elif command == "stop":
        agent.stop()
        sys.exit(0)

    elif command == "status":
        agent.show_status()
        sys.exit(0)

    elif command == "restart":
        success = agent.restart()
        sys.exit(0 if success else 1)

    else:
        print(f"Unknown command: {command}")
        print("Use 'setup', 'start', 'stop', 'status', or 'restart'")
        sys.exit(1)


if __name__ == "__main__":
    main()
