import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

yolo_model = None       # Global YOLO model instance
ocr_reader = None      # Global EasyOCR reader instance



def get_yolo_model():
    global yolo_model
    if yolo_model is None:
        try:
            logger.info("📦 Loading YOLOv8 model...")
            yolo_model = YOLO('yolov8n.pt')
            logger.info("✅ YOLO model loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {e}")
            raise
    return yolo_model

# app/bus_logic/vehicle_identity.py
def detect_vehicles(frame: np.ndarray):
    """
    Run YOLO inference and return list of detected vehicles.
    """
    model = get_yolo_model()  # ✅ Fixed: Load YOLO, not OCR
    results = model(frame, verbose=False)

    detections = []
    names = model.names

    for result in results:
        boxes = result.boxes.cpu().numpy()
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

    return detections


def get_ocr_reader():
    global ocr_reader  # ✅ Fixed: was `yolo_model`!
    if ocr_reader is None:
        try:
            logger.info("📦 Loading OCR model (EasyOCR)...")
            ocr_reader = easyocr.Reader(['en'])
            logger.info("✅ OCR model loaded.")
        except Exception as e:
            logger.error(f"❌ OCR load failed: {e}")
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
    

# def detect_vehicles(frame: np.ndarray):
#     """
#     Run YOLO inference and return annotated frame + detections.
#     """
#     model = get_ocr_reader()
#     results = model(frame)
#     annotated_frame = results[0].plot()  # Bounding boxes + labels
#     detections = []
#     logger.info("🔍 Running vehicle detection...")
#     boxes = results[0].boxes.cpu().numpy()
#     names = results[0].names

#     for box in boxes:
#         x1, y1, x2, y2 = box.xyxy[0]
#         conf = box.conf[0]
#         cls_id = int(box.cls[0])
#         label = names[cls_id]

#         if label in ['car', 'truck', 'bus', 'motorcycle']:
#             detections.append({
#                 "vehicle_type": label,
#                 "confidence": float(conf),
#                 "bbox": [int(x1), int(y1), int(x2), int(y2)],
#             })

#     return annotated_frame, detections
