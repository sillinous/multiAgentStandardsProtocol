# 🚀 APQC Agent Platform - Quick Start Guide

## Run on Your Computer (5 Minutes)

### Step 1: Clone the Repository
```bash
git clone https://github.com/sillinous/multiAgentStandardsProtocol.git
cd multiAgentStandardsProtocol
```

### Step 2: Install Python Dependencies
```bash
pip install fastapi uvicorn sqlalchemy pydantic python-multipart
```

### Step 3: Start the API Server
```bash
python -m uvicorn api_server.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Open in Your Browser

- **Admin Panel**: http://localhost:8000/admin
- **User Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs

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
