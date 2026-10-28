"""
=====================================================================
Web Dashboard Launcher (run_web.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Starts the Flask APM interactive dashboard on port 5000.
"""

import sys
from pathlib import Path

# Add project root to path
web_dir = Path(__file__).resolve().parent / "web"
if str(web_dir) not in sys.path:
    sys.path.insert(0, str(web_dir))

from app import app

if __name__ == "__main__":
    port = 5000
    print("\n" + "=" * 70)
    print("   MICROSERVICES APM ANOMALY DETECTION INTERACTIVE DASHBOARD   ")
    print(f"   Open your browser at: http://localhost:{port}")
    print("=" * 70 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False)
