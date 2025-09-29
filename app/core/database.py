
# app/database.py
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables from .env
load_dotenv()

# Read config
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_NAME = os.getenv("MONGODB_NAME", "tpms")
MONGODB_HOST = os.getenv("MONGODB_URI")

if not MONGODB_HOST:
    raise RuntimeError("MONGODB_URI is not set in .env")
if not MONGODB_USERNAME:
    raise RuntimeError("MONGODB_USERNAME is not set in .env")
if not MONGODB_PASSWORD:
    raise RuntimeError("MONGODB_PASSWORD is not set in .env")

# Ensure MONGODB_HOST starts with mongodb://
if not MONGODB_HOST.startswith("mongodb://"):
    MONGODB_HOST = "mongodb://" + MONGODB_HOST

# Extract host (after mongodb://)
host_part = MONGODB_HOST.split("://", 1)[1]

# URL encode credentials
username = quote_plus(MONGODB_USERNAME)
password = quote_plus(MONGODB_PASSWORD)

def get_motor_uri():
# Build authenticated URI
    if MONGODB_USERNAME and MONGODB_PASSWORD:
        # URL-encode username and password
        client_uri = f"mongodb://{username}:{password}@{host_part}/{MONGODB_NAME}?authSource=admin"
        print("🚀 Final MongoDB URI:", client_uri.replace(password, "*****"))

    else:
        client_uri = f"{MONGODB_HOST}/{MONGODB_NAME}"

    print("Connecting to:", MONGODB_HOST)  # Debug
    print("MongoDB URI (hidden password):", client_uri.split(":")[0] + ":" + client_uri.split("@")[1])

    return client_uri

    # --- Create client and db ---
client = AsyncIOMotorClient(get_motor_uri())
db = client[MONGODB_NAME]

# --- Health check ---
async def connect_to_db():
    try:
        await client.admin.command('ping')
        print(f"🟢 Successfully connected to MongoDB: {MONGODB_NAME}")
    except Exception as e:
        print(f"🔴 Failed to connect to MongoDB: {e}")
        raise

async def close_db_connection():
    client.close()
    print("🔌 MongoDB connection closed")