#!/usr/bin/env python3
"""
Diagnostic script to identify issues with the APQC Agent Platform
"""

import sys
import os

print("=" * 60)
print("APQC Agent Platform - Diagnostic Tool")
print("=" * 60)

# Check Python version
print(f"\n✓ Python Version: {sys.version}")
if sys.version_info < (3, 8):
    print("❌ ERROR: Python 3.8+ required")
    sys.exit(1)

# Check current directory
print(f"\n✓ Current Directory: {os.getcwd()}")
expected_files = ['api_server', 'agents']
missing = [f for f in expected_files if not os.path.exists(f)]
if missing:
    print(f"❌ ERROR: Missing directories: {missing}")
    print("   Make sure you're in the project root: multiAgentStandardsProtocol/")
    sys.exit(1)
else:
    print("  ✓ Project structure looks correct")

# Check dependencies
print("\n📦 Checking dependencies...")
required = {
    'fastapi': 'FastAPI web framework',
    'uvicorn': 'ASGI server',
    'sqlalchemy': 'Database ORM',
    'pydantic': 'Data validation'
}

missing_deps = []
for package, description in required.items():
    try:
        __import__(package)
        print(f"  ✓ {package:15} - {description}")
    except ImportError:
        print(f"  ❌ {package:15} - MISSING")
        missing_deps.append(package)

if missing_deps:
    print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
    print("\n📦 Install with:")
    print(f"   pip3 install {' '.join(missing_deps)}")
    sys.exit(1)

# Check if api_server module can be imported
print("\n🔍 Testing api_server import...")
try:
    import api_server
    print("  ✓ api_server package found")
except ImportError as e:
    print(f"  ❌ Cannot import api_server: {e}")
    sys.exit(1)

# Check if main.py exists and can be imported
print("\n🔍 Testing api_server.main import...")
try:
    from api_server import main
    print("  ✓ api_server.main module found")
except ImportError as e:
    print(f"  ❌ Cannot import api_server.main: {e}")
    print("\nFull error:")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check if app object exists
print("\n🔍 Testing FastAPI app object...")
try:
    from api_server.main import app
    print(f"  ✓ FastAPI app found: {type(app)}")
except ImportError as e:
    print(f"  ❌ Cannot import app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check for port availability
print("\n🔍 Checking port availability...")
import socket
ports_to_check = [8000, 8005, 8080]
available_port = None
for port in ports_to_check:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    if result != 0:
        print(f"  ✓ Port {port} is available")
        if available_port is None:
            available_port = port
    else:
        print(f"  ⚠ Port {port} is in use")

if available_port is None:
    print("\n⚠ All common ports are in use")
    available_port = 9000
    print(f"  Suggestion: Use port {available_port}")

print("\n" + "=" * 60)
print("✅ ALL CHECKS PASSED!")
print("=" * 60)
print("\n🚀 You can start the server with:")
print(f"\n   python3 -m uvicorn api_server.main:app --host 0.0.0.0 --port {available_port} --reload")
print(f"\n   Then open: http://localhost:{available_port}/admin")
print()
