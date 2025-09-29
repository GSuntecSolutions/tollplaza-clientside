# app/core_celeryworker1/frame_detector.py (runs on B)
from celery import Celery
import cv2
import time
import json
from datetime import datetime
import base64

from core.db_synce import db  # Use sync PyMongo
from .celery_work1 import process_frame  # Your YOLO task

celery = Celery(
    'detector_poller',
    broker='redis://101.53.132.75:6379/0'
)

@celery.task
def poll_cameras():
    try:
        cameras = list(db.cameras.find({"status": "Active"}))
        for cam in cameras:
            try:
                cap = cv2.VideoCapture(cam["stream"])
                ret, frame = cap.read()
                cap.release()

                if ret:
                    _, buffer = cv2.imencode(".jpg", frame)
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')

                    message = {
                        "_id": str(cam["_id"]),
                        "laneNo": cam.get("lane"),
                        "location": cam.get("location"),
                        "tollId": cam.get("tollId"),
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "frame": frame_b64,
                        "image_path": f"/images/{cam['tollId']}/{cam['lane']}/{int(time.time())}.jpg"
                    }

                    # Send directly to detection queue
                    process_frame.delay(json.dumps(message))

            except Exception as e:
                print(f"Error capturing {cam['stream']}: {e}")
    except Exception as e:
        print(f"DB poll error: {e}")

# Run every 2 seconds
celery.conf.beat_schedule = {
    'poll-cameras': {
        'task': 'app.core_celeryworker1.frame_detector.poll_cameras',
        'schedule': 2.0
    }
}