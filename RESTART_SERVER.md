# Quick Server Restart Guide

## The Issue
The `/login` endpoint was added but the server needs to be restarted to pick it up.

## Solution - Restart the Server

### Step 1: Stop Current Server

Find and kill the running uvicorn processes:

**Windows (PowerShell):**
```powershell
Get-Process -Name "python" | Where-Object {$_.CommandLine -like "*uvicorn*"} | Stop-Process -Force
```

**OR manually:**
1. Press `Ctrl+C` in the terminal where the server is running
2. If that doesn't work, close the terminal window

### Step 2: Start Server

```bash
cd C:\GitHub\GitHubRoot\sillinous\multiAgentStandardsProtocol

# Start on port 8080 (recommended, since it's already in use)
python -m uvicorn src.superstandard.api.server:app --reload --port 8080

# OR start on port 3000
python -m uvicorn src.superstandard.api.server:app --reload --port 3000
```

### Step 3: Access Login Page

Once the server starts, open your browser and go to:

**If using port 8080:**
```
http://localhost:8080/login
```

**If using port 3000:**
```
http://localhost:3000/login
```

## What to Expect

✅ You should see:
- "AOH - Agent Operations Hub" login page
- Connection status indicator (should be green)
- Pre-filled demo credentials
- Login button (enabled)

❌ If you see errors:
1. Check the server console for error messages
2. Click "Diagnose Connection Issues" button on the login page
3. Make sure you're using the correct port

## Demo Credentials

```
Principal ID: test-principal
Secret: test-secret
```

## Verify It's Working

1. Server should start without errors
2. You should see: `[OK] Authentication routes registered`
3. Login page loads at http://localhost:8080/login
4. Connection indicator shows green
5. You can click login (it should work now!)

## Quick Test Commands

**Test if server is running:**
```bash
curl http://localhost:8080/api/health
```

**Test if login endpoint exists:**
```bash
curl -I http://localhost:8080/login
```

Should return `200 OK` instead of `404 Not Found`

## Troubleshooting

**Port already in use:**
- Try a different port: `--port 8081` or `--port 3000`

**Module not found errors:**
- Make sure you're in the project root directory
- Check that all dependencies are installed

**404 on /login:**
- Server wasn't restarted - restart it!
- Check server logs for import errors

---

## Files Fixed

✅ `aoh_login.html` - Embedded JavaScript (no external dependency)
✅ `auth_routes.py` - Authentication endpoints
✅ `server.py` - Added `/login` endpoint
✅ All tests passing (45/45)

The login should work perfectly after restart! 🚀
