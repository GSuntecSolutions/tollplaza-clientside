# app/core/db_sync.py
from pymongo import MongoClient
import os
from .database import get_motor_uri  # ← Reuse URI logic!


def get_sync_client():
    uri = get_motor_uri()
    return MongoClient(uri)

# Optional: pre-initialized client
client = get_sync_client()
db = client[os.getenv("MONGODB_NAME", "tpms")]