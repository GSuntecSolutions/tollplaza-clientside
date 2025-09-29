# scripts/run_detection.py
import sys
import os
import asyncio

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Go up one level to get project root (where 'app/' lives)
project_root = os.path.dirname(script_dir)  # ← Now points to /root/NextjsApps/firstbackend

print(f"🔧 Adding to Python path: {project_root}")
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now you can import from app
try:
    from app.bus_logic.vehicle_detect import start_vehicle_detection
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("💡 Current Python path:")
    for p in sys.path:
        print(f"  {p}")
    sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting Vehicle Detection System...")
    try:
        asyncio.run(start_vehicle_detection())
    except KeyboardInterrupt:
        print("\n🛑 Detection stopped by user.")
    except Exception as e:
        print(f"❌ Error starting detection: {e}")