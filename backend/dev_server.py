#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import signal
from pathlib import Path

# Paths to watch
WATCH_DIRS = [
    "backend",
    "skills",
    "agent"
]

# Extensions to watch
WATCH_EXTENSIONS = {".py"}

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_all_files_mtimes(root_dir, watch_dirs):
    mtimes = {}
    for watch_dir in watch_dirs:
        full_path = os.path.join(root_dir, watch_dir)
        if not os.path.exists(full_path):
            continue
            
        for root, _, files in os.walk(full_path):
            if "__pycache__" in root:
                continue
            for file in files:
                if os.path.splitext(file)[1] in WATCH_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    try:
                        mtimes[file_path] = os.path.getmtime(file_path)
                    except OSError:
                        pass
    return mtimes

def run_server():
    root_dir = get_project_root()
    server_script = os.path.join(root_dir, "backend", "api_server.py")
    
    # Use same python interpreter
    cmd = [sys.executable, server_script]
    
    # Pass through arguments
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
        
    print(f"[DevServer] Starting server: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=root_dir)

def main():
    root_dir = get_project_root()
    print(f"[DevServer] Watching directories: {', '.join(WATCH_DIRS)}")
    
    process = run_server()
    last_mtimes = get_all_files_mtimes(root_dir, WATCH_DIRS)
    
    try:
        while True:
            time.sleep(1)
            
            # Check if process is still running
            if process.poll() is not None:
                print("[DevServer] Server process exited. Waiting for changes to restart...")
                # Don't restart immediately if it crashed, wait for code change
                while True:
                    time.sleep(1)
                    current_mtimes = get_all_files_mtimes(root_dir, WATCH_DIRS)
                    if current_mtimes != last_mtimes:
                        print("[DevServer] Changes detected after crash. Restarting...")
                        last_mtimes = current_mtimes
                        process = run_server()
                        break
            
            # Check for file changes
            current_mtimes = get_all_files_mtimes(root_dir, WATCH_DIRS)
            if current_mtimes != last_mtimes:
                print("\n[DevServer] 🔄 File change detected. Restarting server...")
                
                # Kill the process
                try:
                    # Try graceful shutdown first
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                except OSError:
                    pass
                
                last_mtimes = current_mtimes
                process = run_server()
                
    except KeyboardInterrupt:
        print("\n[DevServer] Stopping...")
        if process:
            process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
