# 🤖 Dashboard Agent - Intelligent Service Manager

The Dashboard Agent is an intelligent Python agent that manages the complete lifecycle of the APQC dashboard services.

## 🚀 Quick Start

### One-Command Setup and Start

```bash
# Run complete setup and start everything
python dashboard_agent.py setup
python dashboard_agent.py start
```

That's it! Your dashboards are now running.

---

## 📋 Commands

### `setup` - Complete Setup

Runs the complete setup process:
- ✅ Checks Python and Git installation
- ✅ Syncs repository with GitHub
- ✅ Installs all dependencies
- ✅ Initializes APQC database (613 agents)

```bash
python dashboard_agent.py setup
```

### `start` - Start Services

Starts all dashboard servers:
- Main Dashboard Server (port 8080)
- APQC Factory Server (port 8765)

```bash
python dashboard_agent.py start
```

### `stop` - Stop Services

Stops all running servers gracefully:

```bash
python dashboard_agent.py stop
```

### `status` - Check Status

Shows the current status of all services:

```bash
python dashboard_agent.py status
```

Output example:
```
🟢 Main Dashboard (Port 8080)
   Process: Running (PID 12345)
   Health: Healthy ✓

🟢 APQC Factory (Port 8765)
   Process: Running (PID 12346)
   Health: Healthy ✓
```

### `restart` - Restart Services

Stops and starts all services:

```bash
python dashboard_agent.py restart
```

---

## 🎯 Typical Workflow

### First Time Setup

```bash
# 1. Navigate to project directory
cd multiAgentStandardsProtocol

# 2. Run setup
python dashboard_agent.py setup

# 3. Start services
python dashboard_agent.py start

# 4. Open browser
# http://localhost:8080/dashboard
# http://localhost:8765/apqc
```

### Daily Usage

```bash
# Start the dashboards
python dashboard_agent.py start

# ... do your work ...

# Stop the dashboards when done
python dashboard_agent.py stop
```

### If Something Goes Wrong

```bash
# Check what's running
python dashboard_agent.py status

# Restart everything
python dashboard_agent.py restart

# Or stop and start fresh
python dashboard_agent.py stop
python dashboard_agent.py start
```

---

## ✨ Features

### Intelligent Setup
- Automatically detects your environment
- Verifies prerequisites (Python, Git)
- Handles git repository synchronization
- Installs dependencies only if needed
- Initializes database with 613 APQC agents

### Smart Server Management
- Checks port availability before starting
- Waits for servers to be healthy
- Saves process IDs for reliable stopping
- Monitors server health via HTTP endpoints
- Graceful shutdown with fallback force-kill

### Status Monitoring
- Real-time process monitoring
- Health check via API endpoints
- Clear visual status indicators
- Shows PIDs for debugging

### Error Handling
- Detailed error messages
- Automatic retry logic
- Fallback mechanisms
- Safe cleanup on failure

---

## 🔧 Advanced Usage

### Run in Background (Linux/Mac)

```bash
# Start and detach
nohup python dashboard_agent.py start > dashboard.log 2>&1 &

# Check status later
python dashboard_agent.py status

# Stop when done
python dashboard_agent.py stop
```

### Windows Task Scheduler

You can create a scheduled task to auto-start the dashboards:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start a program
5. Program: `python`
6. Arguments: `dashboard_agent.py start`
7. Start in: `C:\path\to\multiAgentStandardsProtocol`

### Check Logs

The agent writes PID files to `.agent_pids/` directory:

```bash
# View saved PIDs
ls .agent_pids/

# Check if processes are running
ps -p $(cat .agent_pids/main_dashboard.pid)
ps -p $(cat .agent_pids/apqc_factory.pid)
```

---

## 🐛 Troubleshooting

### "Python not found"

Install Python 3.8+ from https://www.python.org/downloads/

On Windows, make sure to check "Add Python to PATH" during installation.

### "Port already in use"

Another process is using port 8080 or 8765.

**Find what's using the port:**

Linux/Mac:
```bash
lsof -i :8080
lsof -i :8765
```

Windows:
```cmd
netstat -ano | findstr :8080
netstat -ano | findstr :8765
```

**Solution:**
```bash
# Stop the conflicting process, then
python dashboard_agent.py start
```

### "Failed to sync repository"

Make sure you have internet connection and can access GitHub.

**Manual sync:**
```bash
git fetch origin
git pull origin main
```

### "Database initialization failed"

Check if `APQC_PCF_COMPLETE_HIERARCHY.md` exists:

```bash
ls -la APQC_PCF_COMPLETE_HIERARCHY.md
```

If missing, run:
```bash
git pull origin main
```

### Servers won't stay running

Check the logs:

```bash
# Start with verbose output
python dashboard_agent.py start

# Or check server logs directly
python -m uvicorn src.superstandard.api.server:app --port 8080
python apqc_factory_server.py
```

---

## 📊 What Gets Installed

### Python Packages

- **fastapi** - Web framework for APIs
- **uvicorn** - ASGI server
- **jinja2** - Template engine
- **pydantic** - Data validation
- **python-multipart** - File upload support

### Databases

- **apqc_agent_configs.db** - SQLite database with 613 agent configurations

### Process Files

- **.agent_pids/main_dashboard.pid** - Main server PID
- **.agent_pids/apqc_factory.pid** - APQC factory PID

---

## 🎯 Dashboard URLs

Once started, access these URLs:

### Main Dashboard Hub
- **Landing Page**: http://localhost:8080/dashboard
- **Admin Dashboard**: http://localhost:8080/dashboard/admin
- **User Control**: http://localhost:8080/dashboard/user
- **Network Graph**: http://localhost:8080/dashboard/network
- **Coordination**: http://localhost:8080/dashboard/coordination
- **Consciousness**: http://localhost:8080/dashboard/consciousness

### APQC Factory
- **Hierarchy Explorer**: http://localhost:8765/apqc
- **API Docs**: http://localhost:8765/docs
- **Stats API**: http://localhost:8765/api/apqc/stats

---

## 🔒 Security Notes

- Servers bind to `0.0.0.0` (all interfaces) by default
- If exposing to network, consider adding authentication
- PID files contain process IDs (not sensitive)
- Database contains agent configurations (not user data)

---

## 🆘 Getting Help

If you encounter issues:

1. **Check status**: `python dashboard_agent.py status`
2. **View logs**: Check terminal output for errors
3. **Restart**: `python dashboard_agent.py restart`
4. **Fresh start**:
   ```bash
   python dashboard_agent.py stop
   python dashboard_agent.py setup
   python dashboard_agent.py start
   ```

---

## 📚 Related Documentation

- **APQC_AGENT_FACTORY_GUIDE.md** - Complete factory guide
- **APQC_FACTORY_DELIVERY_SUMMARY.md** - Feature summary
- **APQC_PCF_COMPLETE_HIERARCHY.md** - Full hierarchy
- **WINDOWS_QUICK_START.md** - Windows-specific guide

---

**Version**: 1.0.0
**Last Updated**: 2025-11-17
**Compatible With**: Windows, Linux, macOS
