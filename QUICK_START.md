# 🚀 APQC Agent Platform - Quick Start Guide

## Run on Your Computer (5 Minutes)

### Step 1: Clone the Repository
```bash
git clone https://github.com/sillinous/multiAgentStandardsProtocol.git
cd multiAgentStandardsProtocol
```

### Step 2: Install Python Dependencies
```bash
pip3 install fastapi uvicorn sqlalchemy pydantic python-multipart
```

### Step 3: Start the API Server

**Method 1: Use the startup script (Recommended)**
```bash
python3 start_server.py
```

**Method 2: Use the batch file (Windows only)**
```cmd
start_server.bat
```

**Method 3: Direct uvicorn command**
```bash
python3 -m uvicorn api_server.main:app --host 0.0.0.0 --port 8000 --reload
```

**Method 4: Using Python directly**
```bash
python3 -c "import uvicorn; uvicorn.run('api_server.main:app', host='0.0.0.0', port=8000, reload=True)"
```

You should see:
```
🚀 Starting Agent Platform API...
✅ Database initialized successfully
✅ API Server ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Open in Your Browser

- **Admin Panel**: http://localhost:8000/admin
- **User Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs

## 🔧 Troubleshooting

### "Command not found" or "ModuleNotFoundError"

**Problem**: Python or dependencies not installed

**Solution**:
```bash
# Check Python version (need 3.8+)
python3 --version

# Install dependencies
pip3 install fastapi uvicorn sqlalchemy pydantic python-multipart
```

### "Address already in use" or Port Error

**Problem**: Port 8000 is already being used

**Solution**: Use a different port
```bash
python3 start_server.py 8005
# or
python3 -m uvicorn api_server.main:app --host 0.0.0.0 --port 8005
```

### "No module named 'api_server'"

**Problem**: Not in the correct directory

**Solution**: Make sure you're in the project root
```bash
cd multiAgentStandardsProtocol
ls  # Should see: api_server/ workflows/ agents/ etc.
python3 start_server.py
```

### Can't access from browser

**Problem**: Browser can't connect

**Solutions**:
1. Make sure server is actually running (check terminal output)
2. Try http://127.0.0.1:8000/admin instead of localhost
3. Check firewall isn't blocking Python
4. Try a different browser

### Dependencies won't install

**Problem**: pip install fails

**Solutions**:
```bash
# Upgrade pip first
python3 -m pip install --upgrade pip

# Install with --user flag
pip3 install --user fastapi uvicorn sqlalchemy pydantic python-multipart

# If pip3 doesn't work, use python3 -m pip
python3 -m pip install fastapi uvicorn sqlalchemy pydantic python-multipart
```

## 🌐 Access from Other Computers

Find your IP address and replace `localhost` with it:
- Windows: `ipconfig`
- Mac/Linux: `ifconfig` or `hostname -I`

Example: http://192.168.1.100:8000/admin

## 📦 What You Get

- ✅ 1,100 APQC Level 5 Agents (100% Coverage)
- ✅ Multi-Agent Workflow Engine  
- ✅ REST API with Database
- ✅ Real-Time Dashboard
- ✅ Comprehensive Admin Panel

See ADMIN_PANEL_GUIDE.md for detailed features!
