#!/usr/bin/env python3
"""
Quick script to kill the Polygon server running on port 8200
"""

import subprocess
import sys

def kill_server():
    """Kill server running on port 8200"""
    try:
        # Find process using port 8200
        result = subprocess.run(
            ['netstat', '-ano'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Look for port 8200
        for line in result.stdout.split('\n'):
            if ':8200' in line and 'LISTENING' in line:
                # Extract PID (last column)
                pid = line.strip().split()[-1]
                print(f"Found server on port 8200 with PID: {pid}")
                
                # Kill the process
                kill_result = subprocess.run(
                    ['taskkill', '/PID', pid, '/F'],
                    capture_output=True,
                    text=True
                )
                
                if kill_result.returncode == 0:
                    print(f"Successfully killed server (PID: {pid})")
                else:
                    print(f"Failed to kill server: {kill_result.stderr}")
                return
        
        print("No server found running on port 8200")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running netstat: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Killing Polygon server on port 8200...")
    kill_server()