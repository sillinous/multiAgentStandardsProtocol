# 🪟 Windows Quick Start Guide

## 🚀 One-Click Setup

### To Start the Dashboards:

1. **Double-click** `start_dashboards.bat`
2. Wait for the script to finish (about 1-2 minutes)
3. Your browser will open automatically!

That's it! ✨

---

## 📊 What You'll Get

After running the script, you'll have access to:

### Main Dashboard Hub
**URL**: http://localhost:8080/dashboard

Available dashboards:
- 🔧 **Admin Dashboard** - Real-time monitoring
- 👤 **User Control Panel** - Agent registration
- 🕸️ **Network Visualization** - Force-directed graph
- 🤝 **Coordination Dashboard** - Workflow tracking
- 🧠 **Consciousness Monitor** - Agent awareness metrics

### APQC Agent Factory
**URL**: http://localhost:8765/apqc

Features:
- Browse all 613 APQC agents
- Configure each agent through UI
- Generate agents on-demand
- Interactive hierarchy explorer

### API Documentation
- **Main Server**: http://localhost:8080/docs
- **APQC Factory**: http://localhost:8765/docs

---

## 🛑 To Stop the Servers

**Double-click** `stop_dashboards.bat`

Or just close the two command windows that opened.

---

## ⚙️ What the Start Script Does

1. ✅ Syncs your local code with GitHub (gets latest updates)
2. ✅ Installs required Python packages
3. ✅ Initializes database with 613 APQC agents
4. ✅ Starts Main Dashboard Server (port 8080)
5. ✅ Starts APQC Factory Server (port 8765)
6. ✅ Opens your browser automatically

---

## 🔧 Troubleshooting

### "Python is not recognized"

You need to install Python first:
1. Download from https://www.python.org/downloads/
2. **Important**: Check "Add Python to PATH" during installation
3. Restart your computer
4. Try the script again

### "Port already in use"

Another program is using port 8080 or 8765.

**Solution**: Run `stop_dashboards.bat` first, then try again.

### Servers won't start

Make sure you're in the correct directory:
- Right-click `start_dashboards.bat`
- Check the folder location
- It should be in the `multiAgentStandardsProtocol` folder

---

## 📝 Manual Setup (If Script Doesn't Work)

Open Command Prompt or PowerShell in this folder, then run:

```bash
# Sync with GitHub
git fetch origin
git reset --hard origin/main

# Install dependencies
pip install fastapi uvicorn jinja2 pydantic python-multipart

# Initialize database
python apqc_agent_factory.py --init

# Start servers (in 2 separate windows)
# Window 1:
python -m uvicorn src.superstandard.api.server:app --host 0.0.0.0 --port 8080

# Window 2:
python apqc_factory_server.py
```

Then open http://localhost:8080/dashboard in your browser.

---

## 💡 Tips

- **First time?** The script might take 2-3 minutes to download and install everything
- **Subsequent runs** are much faster (30 seconds)
- **Keep the command windows open** while using the dashboards
- **Use `stop_dashboards.bat`** before running `start_dashboards.bat` again

---

## 🎯 What's Included

- **613 APQC Agents** - All configured and ready to use
- **6 Interactive Dashboards** - Real-time monitoring and control
- **Complete Documentation** - In the `/docs` folder
- **API Access** - RESTful APIs for all functionality

---

## 📚 More Information

- **Complete Guide**: See `APQC_AGENT_FACTORY_GUIDE.md`
- **Delivery Summary**: See `APQC_FACTORY_DELIVERY_SUMMARY.md`
- **Full Hierarchy**: See `APQC_PCF_COMPLETE_HIERARCHY.md`

---

**Enjoy your APQC Agent Factory! 🏭**
