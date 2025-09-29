# app/core_celeryworker1/celery_work1.py
from celery import Celery
import json
import redis
import cv2
import base64
import numpy as np
import time
import os
from datetime import datetime, timezone
import threading
import subprocess



# ✅ Correct absolute import
from app.bus_logic.vehicle_detect import detect_vehicles

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory to save images

IMAGE_ROOT = "/shared/images"  # NFS mounted path
VIDEO_ROOT = "/shared/videos"
# Ensure dirs exist
os.makedirs(IMAGE_ROOT, exist_ok=True)
os.makedirs(VIDEO_ROOT, exist_ok=True)

# --- Celery Setup ---
# Use Redis on server A
celery = Celery(
    'detector',
    broker='redis://101.53.132.75:6379/0',  # Server A
    backend='redis://101.53.132.75:6379/0'
)


# --- Client to send back to Machine A ---
saver_client = Celery(
    'saver_client',
    broker='redis://101.53.132.75:6379/0'  # Same Redis
)

@celery.task
def process_frame(message_str):
    try:
        message = json.loads(message_str)
        logger.info(f"🎥 Processing frame for lane {message.get('laneNo')}")
        
        if "frame" not in message:
            raise KeyError("Missing 'frame' in message")
        
        # Decode image
        frame_data = base64.b64decode(message["frame"])
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Run detection
        detections = detect_vehicles(frame)
        if detections and message["laneNo"] not in active_recordings:
           print(f"🚗 Vehicle detected on lane {message['laneNo']} → starting 30s recording")
           active_recordings[message["laneNo"]] = True

        # Start recording in background thread
           threading.Thread(
                target=start_video_recorder,
                args=(message["laneNo"], message["rtsp_url"]),
                daemon=True
            ).start()

        # Mark as recording
        # active_recordings[message["laneNo"]] = True

    # After 30s, auto-remove flag


       # Extract path
        img_path = message["image_path"]  # e.g., /images/101/2/2025-09-22/vehicle_123.jpg
        full_path = IMAGE_ROOT + img_path  # → /shared/images/images/...
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
       
     

            # Save image
        cv2.imwrite(full_path, frame)
        print(f"🖼️ Saved: {full_path}")
        
        
        # Prepare result for DB
        vehicle_type = detections[0]["vehicle_type"].capitalize() if detections else "Unknown"

        # Prepare result
        result = {
            "location": message["location"],
            "tollId": int(message["tollId"]),
            "laneNo": message["laneNo"],                # ✅ Correct name
            "vehicleNo": "UNKNOWN",                     # Placeholder
            "vehicleType": vehicle_type,
            "entryTime": datetime.fromisoformat(message["timestamp"].rstrip("Z")),  # Convert to datetime
            # "image": message["image_path"],             # Rename from image_path → image
            "cameraId": message["_id"],
            "company": message["company"],
            "io": message["io"],
            "confidence": detections[0]["confidence"] if detections else None,
            "processed_at": time.time(), 
             "image_url": img_path, # Relative path
             "video_url": f"/videos/{message["laneNo"]}/{int(time.time())}.mp4"  # Predicted path
     }
        print("📥 Full result keys:", list(result.keys()))

     # ✅ Send result back to Machine A's saver
        saver_client.send_task(
            'app.redis_que_sys.db_saver.save_detection_result',
            args=[result],
            queue='db_saver'  # 👈 Route correctly

        )
        logger.info("📤 Result sent to db_saver on Machine A $}" )
        return result

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


# Global dictionary to manage ongoing recordings per lane
active_recordings = {}

def start_video_recorder(lane_no, rtsp_url, duration=12):
    """
    Start recording a video from RTSP stream for N seconds.
    Saves to /shared/videos/
    """
    try:
        # Generate filename
        timestamp = int(time.time())
        video_dir = f"{VIDEO_ROOT}/{lane_no}"
        os.makedirs(video_dir, exist_ok=True)
        video_path = f"{video_dir}/{timestamp}.mp4"

        logger.info(f"📹 Starting 30s recording for lane {lane_no} → {video_path}")

        # Use FFmpeg (more reliable than OpenCV for video)
        command = [
            'ffmpeg',
            '-y',  # Overwrite
            '-rtsp_transport', 'tcp',
            '-i', rtsp_url,
            '-t', str(duration),  # Duration
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '23',
            '-an',  # No audio
            video_path
        ]
        
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=duration + 5)
            if result.returncode == 0:
                print(f"📹 Saved 30s clip: {video_path}")
            else:
                print(f"❌ FFmpeg error: {result.stderr.decode()}")
        except Exception as e:
            print(f"❌ Recording failed: {e}")

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise
        logger.info("🔍 Running vehicle detection...")  