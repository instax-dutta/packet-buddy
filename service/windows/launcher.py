"""
PacketBuddy Background Service Launcher
This script is executed by pythonw.exe (headless) via Task Scheduler.
It sets up the environment and starts the API server.
"""

import os
import sys
from pathlib import Path

# Set up paths
# accessible at service/windows/launcher.py
current_dir = Path(__file__).resolve().parent
# project root is ../..
project_root = current_dir.parent.parent

# 1. Set working directory to project root
os.chdir(project_root)

# 2. Add project root to sys.path
sys.path.insert(0, str(project_root))

# 3. Redirect stdout/stderr for pythonw compatibility
# pythonw.exe has no stdout/stderr, which causes logging handlers (StreamHandler) to fail
sys.stdout = open(project_root / "service_stdout.log", "w", buffering=1, encoding='utf-8')
sys.stderr = open(project_root / "service_stderr.log", "w", buffering=1, encoding='utf-8')

# 4. Import and run server
try:
    from src.api.server import run_server
    run_server()
except ImportError as e:
    # Log primitive error if import fails
    with open(project_root / "startup_error.log", "w") as f:
        f.write(f"Failed to start PacketBuddy service:\n{e}\n")
        f.write(f"Python path: {sys.path}\n")
        f.write(f"CWD: {os.getcwd()}\n")
except Exception as e:
    with open(project_root / "startup_error.log", "w") as f:
        f.write(f"Unexpected error:\n{e}\n")
