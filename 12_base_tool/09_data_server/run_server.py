#!/usr/bin/env python3
"""
Simple Polygon Server Launcher for 09_data_server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("         Polygon Data Server Launcher")
    print("         (from 09_data_server directory)")
    print("=" * 60)
    print()
    
    # Get directories
    data_server_dir = Path(__file__).parent
    project_root = data_server_dir.parent
    
    # Change to project root for proper module resolution
    os.chdir(project_root)
    
    # Check if .env exists in project root
    env_file = project_root / '.env'
    if not env_file.exists():
        print("ERROR: .env file not found in project root!")
        print("Please run setup or create .env file first")
        sys.exit(1)
    
    # Load environment manually
    try:
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print(f"Loaded environment from {env_file}")
    except Exception as e:
        print(f"Failed to load .env: {e}")
        sys.exit(1)
    
    # Check API key
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        print("ERROR: POLYGON_API_KEY not found in .env file")
        sys.exit(1)
    
    masked_key = api_key[:8] + '...' + api_key[-4:] if len(api_key) > 12 else 'configured'
    print(f"API Key: {masked_key}")
    print()
    
    print("Starting Polygon Data Server...")
    print("Server will be available at:")
    print("  • http://localhost:8200")
    print("  • API Docs: http://localhost:8200/docs")
    print("  • Health: http://localhost:8200/health")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Start the server from 09_data_server directory
    try:
        # Use the correct Python installation that has uvicorn
        python_exe = r"C:\Users\codyc\AppData\Local\Programs\Python\Python312\python.exe"
        if not os.path.exists(python_exe):
            python_exe = sys.executable  # Fallback to system default
            
        cmd = [
            python_exe, '-m', 'uvicorn',
            '09_data_server.polygon_server.server:app',
            '--host', '0.0.0.0',
            '--port', '8200',
            '--log-level', 'info'
        ]
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except subprocess.CalledProcessError as e:
        print(f"Server failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()