"""
Quick Start Launcher for EmergencyRoute
"""

import sys
import webbrowser
import threading
import time
from app import app

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    print("=" * 70)
    print("🚑 EmergencyRoute — Emergency Vehicle Route Optimizer")
    print("📡 Graph Optimization • DAA Benchmark • Dynamic Traffic Simulator")
    print("🔗 Server URL: http://127.0.0.1:5000")
    print("=" * 70)

    # Automatically launch browser in background
    if "--no-browser" not in sys.argv:
        threading.Thread(target=open_browser, daemon=True).start()

    app.run(host="127.0.0.1", port=5000, debug=False)
