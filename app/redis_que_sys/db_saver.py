# app/redis_que_sys/db_saver.py
from celery import Celery
from app.core.db_sync import db  # ✅ Reuse existing sync DB client
import os
import logging
from datetime import datetime


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Celery Setup ---
celery = Celery(
    'saver',
    broker='redis://101.53.132.75:6379/0',
    backend='redis://101.53.132.75:6379/0'
)

@celery.task(queue='db_saver')  # 👈 Explicit queue
def save_detection_result(result):
    try:
        print("💾 Saving detection result to MongoDB...")
        # ✅ DEBUG: Log what we actually received
        print("📥 FULL INCOMING RESULT:", result)
        print("🔍 AVAILABLE KEYS:", list(result.keys()))

       # ✅ Safely get vehicles (or detections)
        vehicles = result.get("vehicles") or result.get("detections") or []
        
        vehicle_type = "Unknown"
        if isinstance(vehicles, list) and len(vehicles) > 0:
            vehicle_type = vehicles[0].get("vehicle_type", "Unknown").capitalize()


        # Map to TollTransaction schema
        transaction = {
            "location": result.get("location", "Unknown"),
            "tollId": int(result.get("tollId", 0)),
            "laneNo": int(result.get("laneNo", result.get("lane", 0))),  # Try laneNo first, then lane
            "vehicleNo": result.get("vehicleNo", "UNKNOWN"),
            "vehicleType": result.get("vehicleType", "Unknown"),
            "entryTime": result.get("entryTime"),
            "image": result.get("image_url", ""),  # ✅ Map 'image_path' → 'image'
            "cameraId": result.get("cameraId", ""),
            "company": result.get("company", ""),
            "io": result.get("io", "in"),
            "confidence": result.get("confidence", 0.0),
            "processed_at": datetime.utcnow(),
            "video": result.get("video_url", "")  # Map 'video_path' if
        }
        print("📝 Mapped transaction data:", transaction)

        # Insert into TollTransaction collection
        collection = db["TollTransaction"]
        inserted = collection.insert_one(transaction)
        print(f"✅ Saved to TollTransaction with ID: {inserted.inserted_id}")
        return {"status": "saved", "id": str(inserted.inserted_id)}

    except Exception as e:
        print(f"❌ Save failed: {e}")
        raise