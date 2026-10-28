"""
=====================================================================
Root Launcher (main.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Forwards execution to api-anomaly-detection/main.py.
"""

import sys
import subprocess
from pathlib import Path

root_dir = Path(__file__).resolve().parent
project_dir = root_dir / "api-anomaly-detection"

if __name__ == "__main__":
    script_path = project_dir / "main.py"
    cmd = [sys.executable, str(script_path)]
    sys.exit(subprocess.call(cmd, cwd=str(project_dir)))
