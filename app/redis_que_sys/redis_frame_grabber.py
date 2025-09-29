# app/redis_que_sys/redis_frame_grabber.py
import cv2
import time
import redis
import json
import base64
import os
import sys
from celery import chain
# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (firstbackend)
print("Current dir:", current_dir)
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
# Add the project root to the Python path
print("Project root:", project_root)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print("Added to sys.path:", project_root)
# Now you can import from app
from app.core.db_sync import db
from datetime import datetime,timezone
from task_sender import celery_app
from db_saver import save_detection_result


r = redis.Redis(host='localhost', port=6379, db=0)

while True:
    collection = db["cameras"]
    cursor = collection.find({"status": "Active"})  # Match your status field case

    # Get all active cameras from MongoDB
    cameras = cursor.to_list(length=100)

    
    for cam  in cameras:
        try:
            cap = cv2.VideoCapture(cam["stream"])
            ret, frame = cap.read()
            if ret:
                # ✅ Encode frame
                _, buffer = cv2.imencode(".jpg", frame)
                frame_b64 = base64.b64encode(buffer).decode('utf-8')

             # Generate structured image path
                now = datetime.now(timezone.utc)
                timestamp_str = str(int(now.timestamp()))
                location = cam.get("location", "Unknown").replace(" ", "_")
                tollId = str(cam.get("tollId", "0"))
                lane = str(cam.get("lane", "0"))

                image_path = f"/images/{tollId}/{lane}/{now.strftime('%Y-%m-%d')}/vehicle_{timestamp_str}.jpg"
                print("Generated image path:", image_path)

                # video_path = f"/videos/{tollId}/{lane}/{now.strftime('%Y-%m-%d')}/feed_{timestamp_str}.mp4"
                # print("Generated video path:", video_path)



                # ✅ Include frame in message
                message = {
                    "_id": str(cam["_id"]),
                    "company": cam.get("company", "Unknown"),
                    "location": cam.get("location", "Unknown"),
                    "tollId": str(cam.get("tollId", "0")),
                    "laneNo": int(cam.get("lane", 0)),
                    "io": cam.get("io", "in"),
                    "rtsp_url": cam.get("stream"),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "frame": frame_b64,  # ✅ Add encoded image
                    "image_path": image_path  # Pass path forward
                }

               # ✅ Send task
                try:
                    celery_app.send_task(
                        'app.core_celeryworker1.celery_work1.process_frame',
                        args=[json.dumps(message)]
                    )
                    print(f"📤 Task sent for lane {cam['lane']}")
                except Exception as e:
                    print(f"❌ Failed to send task: {e}")
            else:
                print(f"❌ Failed to capture from {cam.get("stream")}")
            cap.release()
        except Exception as e:
            print(f"Error capturing: {e}")
    
    time.sleep(2)  # Wait before next cycle