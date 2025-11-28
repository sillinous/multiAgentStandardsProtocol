#!/usr/bin/env python3
"""
Simple startup script for APQC Agent Platform
Handles dependencies and provides clear error messages
"""

import sys
import subprocess

def check_dependencies():
    """Check if required packages are installed"""
    required = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing dependencies!")
        print(f"   Missing: {', '.join(missing)}")
        print("\n📦 Install them with:")
        print("   pip3 install fastapi uvicorn sqlalchemy pydantic python-multipart")
        return False
    
    print("✅ All dependencies installed")
    return True

def start_server(port=8000):
    """Start the uvicorn server"""
    print(f"\n🚀 Starting APQC Agent Platform on port {port}...")
    print(f"   Admin Panel: http://localhost:{port}/admin")
    print(f"   Dashboard:   http://localhost:{port}/dashboard")
    print(f"   API Docs:    http://localhost:{port}/docs")
    print("\n   Press Ctrl+C to stop\n")
    
    try:
        import uvicorn
        uvicorn.run(
            "api_server.main:app",
            host="0.0.0.0",
            port=port,
            reload=True
        )
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\n💡 Troubleshooting:")
        print(f"   1. Check if port {port} is available")
        print(f"   2. Try a different port: python3 start_server.py 8005")
        print("   3. Make sure you're in the project root directory")
        return False
    
    return True

if __name__ == "__main__":
    # Get port from command line if provided
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    # Start server
    start_server(port)
