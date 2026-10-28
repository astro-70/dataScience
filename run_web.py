"""
=====================================================================
Root Web Launcher (run_web.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Forwards to api-anomaly-detection/run_web.py.
"""

import sys
import subprocess
from pathlib import Path

root_dir = Path(__file__).resolve().parent
project_dir = root_dir / "api-anomaly-detection"

if __name__ == "__main__":
    script_path = project_dir / "run_web.py"
    cmd = [sys.executable, str(script_path)]
    sys.exit(subprocess.call(cmd, cwd=str(project_dir)))
