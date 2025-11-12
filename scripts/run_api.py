#!/usr/bin/env python3
"""
Start the SuperStandard PCF Agent API Server

Usage:
    python scripts/run_api.py [--port PORT] [--reload] [--host HOST]

Examples:
    # Development mode with auto-reload
    python scripts/run_api.py --reload

    # Production mode on specific port
    python scripts/run_api.py --port 8080

    # Bind to specific host
    python scripts/run_api.py --host 0.0.0.0 --port 8000
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from superstandard.api.main import run_server


def main():
    parser = argparse.ArgumentParser(
        description='Start SuperStandard PCF Agent API Server'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind to (default: 8000)'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload for development'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("SuperStandard PCF Agent API Server")
    print("=" * 80)
    print(f"\nStarting server on http://{args.host}:{args.port}")
    print(f"Mode: {'Development (auto-reload)' if args.reload else 'Production'}")
    print(f"\nEndpoints:")
    print(f"  - API Docs: http://{args.host}:{args.port}/docs")
    print(f"  - Health Check: http://{args.host}:{args.port}/api/health")
    print(f"  - Execute Agent: POST http://{args.host}:{args.port}/api/pcf/{{hierarchy_id}}/execute")
    print(f"\nPress CTRL+C to stop")
    print("=" * 80)
    print()

    run_server(host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
