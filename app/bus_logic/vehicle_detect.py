# app/bus_logic/vehicle_detect.py

from ultralytics import YOLO
import cv2
import torch
import warnings
import numpy as np
from datetime import datetime
import os
from bson import ObjectId
import asyncio
from typing import Dict, List
import logging
# Optional: Move to app/bus_logic/lpr.py later
import easyocr

# Global OCR reader (load once)
ocr_reader = None


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress unnecessary warnings
warnings.filterwarnings("ignore")

# Add safe globals for YOLO model loading
torch.serialization.add_safe_globals([
    type(torch.nn.Conv2d(3, 32, 3)),
    type(torch.nn.Sequential()),
])

# Global model instance
yolo_model = None

# Direct DB import (we'll discuss API vs DB below)
from app.core.database import db


def get_yolo_model():
    """
    Singleton: Load YOLO model once.
    """
    global yolo_model
    if yolo_model is None:
        try:
            logger.info("📦 Loading YOLOv8 model...")
            yolo_model = YOLO('yolov8n.pt')  # Use yolov8s.pt for better accuracy
            logger.info("✅ YOLO model loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {e}")
            raise
    return yolo_model


async def get_camera_streams() -> List[Dict]:
    """
    Fetch all active cameras from MongoDB.
    Maps schema to required format.
    """
    try:
        collection = db["cameras"]
        cursor = collection.find({"status": "Active"})  # Match your status field case
        cameras = await cursor.to_list(length=100)

        return [
            {
                "_id": str(cam["_id"]),
                "company": cam.get("company", "Unknown"),
                "location": cam.get("location", "Unknown"),
                "tollId": str(cam.get("tollId", "0")),
                "laneNo": int(cam.get("lane", 0)),  # 'lane' in your DB
                "io": cam.get("io", "in"),
                "rtsp_url": cam.get("stream"),
            }
            for cam in cameras
            if cam.get("stream") and isinstance(cam["stream"], str) and cam["stream"].startswith("rtsp://")
        ]
    except Exception as e:
        logger.error(f"❌ Error fetching cameras: {e}", exc_info=True)
        return []


def detect_vehicles(frame: np.ndarray):
    """
    Run YOLO inference and return annotated frame + detections.
    """
    model = get_yolo_model()
    results = model(frame)

    # annotated_frame = results[0].plot()  # Bounding boxes + labels
    detections = []

    boxes = results[0].boxes.cpu().numpy()
    names = results[0].names

    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        conf = box.conf[0]
        cls_id = int(box.cls[0])
        label = names[cls_id]

        if label in ['car', 'truck', 'bus', 'motorcycle']:
            detections.append({
                "vehicle_type": label,
                "confidence": float(conf),
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
            })

    logger.info(f"🔍 Found {len(detections)} vehicles: {[d['vehicle_type'] for d in detections]}")
    return detections  # Always a list of dicts




def get_ocr_reader():
    """
    Singleton: Load OCR model once.
    """
    global ocr_reader
    if ocr_reader is None:
        try:
            print("📦 Loading OCR model (EasyOCR)...")
            ocr_reader = easyocr.Reader(['en'])  # Add ['hi'] for Hindi if needed
            print("✅ OCR model loaded.")
        except Exception as e:
            print(f"❌ OCR load failed: {e}")
            raise
    return ocr_reader


def extract_license_plate(frame: np.ndarray, bbox: list) -> tuple[str | None, np.ndarray | None]:
    """
    Crop vehicle region and detect license plate text.
    :param frame: Full annotated frame
    :param bbox: [x1, y1, x2, y2]
    :return: (plate_text, cropped_plate_image)
    """
    x1, y1, x2, y2 = bbox
    # Expand slightly to include full plate
    margin = 10
    h, w = frame.shape[:2]
    x1 = max(0, x1 - margin)
    y1 = max(0, y1 - 20)
    x2 = min(w, x2 + margin)
    y2 = min(h, y2 + 30)

    plate_img = frame[y1:y2, x1:x2]

    if plate_img.size == 0:
        return None, None

    # Convert BGR → RGB for OCR
    plate_rgb = cv2.cvtColor(plate_img, cv2.COLOR_BGR2RGB)

    try:
        reader = get_ocr_reader()
        results = reader.readtext(plate_rgb, detail=0, paragraph=False, min_size=20)

        # Filter likely plate patterns (alphanumeric, length 6–10)
        for text in results:
            cleaned = ''.join(ch.upper() for ch in text if ch.isalnum())
            if 6 <= len(cleaned) <= 12 and any(c.isdigit() for c in cleaned):
                return cleaned, plate_img

        return results[0] if results else None, plate_img
    except Exception as e:
        print(f"❌ OCR error: {e}")
        return None, plate_img
    


async def save_detection_result(
    camera: Dict,
    frame: np.ndarray,
    detections: List[Dict]
):
    """
    Save detection result:
    1. Save image to /images/tollId/laneNo/YYYY-MM-DD/
    2. Insert record into TollTransaction
    """
    now = datetime.now()
    toll_id = camera["tollId"]
    lane_no = camera["laneNo"]

    # Create directory path
    base_dir = "/root/NextjsApps/firstbackend/toll_images"  # Change to your desired location
    # Or use relative: os.path.join("images", toll_id, str(lane_no), now.strftime("%Y-%m-%d"))
    img_dir = os.path.join(base_dir, toll_id, str(lane_no), now.strftime("%Y-%m-%d"))
    os.makedirs(img_dir, exist_ok=True)

    # Generate filename
    timestamp_str = now.strftime("%H_%M_%S_%f")[:-3]  # HH_MM_SS_mmm
    filename = f"vehicle_{timestamp_str}.jpg"
    img_path = os.path.join(img_dir, filename)

    # Save image
    success = cv2.imwrite(img_path, frame)
    if not success:
        logger.error(f"❌ Failed to save image: {img_path}")
        return

    # Construct stored URL/path (adjust based on how it's served)
    # If accessible via http://yourserver/images/... then:
    relative_path = f"/toll_images/{toll_id}/{lane_no}/{now.strftime('%Y-%m-%d')}/{filename}"

    # Pick top confidence vehicle
    best_detection = max(detections, key=lambda d: d["confidence"]) if detections else None
    bbox = best_detection["bbox"]
    vehicle_type = best_detection["vehicle_type"] if best_detection else "Unknown"
    confidence = best_detection["confidence"] if best_detection else 0.0

  # --- OCR License Plate ---
    plate_text, plate_img = extract_license_plate(frame, bbox)
    vehicle_no = plate_text or f"UNKNOWN_{now.strftime('%H%M%S_%f')[:-3]}"
    logger.info(f"License plate detected: {vehicle_no}")

    # Prepare document for TollTransaction
    transaction_doc = {
        "location": camera["location"],
        "tollId": int(toll_id),  
        "laneNo": int(lane_no),
        "vehicleNo": vehicle_no,  
        "vehicleType": vehicle_type.title(),  # Car, Truck
        "vehicleSubType": "",  # Optional: can be enhanced later
        "entryTime": now,
        "image": relative_path.replace("\\", "/"),  # Normalize path
        "video": "",  # Not capturing video yet
        "confidence": confidence,
        "cameraId": camera["_id"],
        "company": camera["company"],
        "io": camera["io"]
    }

    # Save to MongoDB
    try:
        result = await db["TollTransaction"].insert_one(transaction_doc)
        logger.info(f"💾 Saved transaction ID: {result.inserted_id} | Vehicle: {vehicle_type}")
    except Exception as e:
        logger.error(f"❌ Failed to save transaction: {e}", exc_info=True)


async def capture_and_process_stream(camera: Dict, interval_seconds: int = 5):
    """
    Capture frames from RTSP, detect vehicles, save every N seconds.
    """
    cap = cv2.VideoCapture(camera["rtsp_url"])
    if not cap.isOpened():
        logger.error(f"❌ Cannot open RTSP stream: {camera['rtsp_url']}")
        return

    logger.info(f"🟢 Processing stream: {camera['location']} - Lane {camera['laneNo']}")

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.warning("⚠️  Frame grab failed — retrying in 2s...")
            await asyncio.sleep(2)
            continue

        # Resize for faster processing
        frame = cv2.resize(frame, (1280, 720))

        # Run detection
        try:
            annotated_frame, detections = detect_vehicles(frame)
        except Exception as e:
            logger.error(f"❌ Detection error: {e}")
            continue

        if detections:
            # Add overlay text
            cv2.putText(annotated_frame, f"{len(detections)} Vehicles", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"{camera['location']} - Lane {camera['laneNo']}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # Save image + DB record
            await save_detection_result(camera, annotated_frame, detections)

        # Wait before next capture
        await asyncio.sleep(interval_seconds)

    cap.release()


async def start_vehicle_detection(interval_seconds: int = 5):
    """
    Main entry point: Start detection on all active cameras.
    """
    cameras = await get_camera_streams()
    if not cameras:
        logger.warning("🚨 No active cameras found in database!")
        return

    logger.info(f"🎥 Starting detection on {len(cameras)} camera(s)...")

    tasks = []
    for cam in cameras:
        task = asyncio.create_task(
            capture_and_process_stream(cam, interval_seconds=interval_seconds)
        )
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)