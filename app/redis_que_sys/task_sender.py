# app/core/task_sender.py
from celery import Celery

# Reuse same broker
celery_app = Celery(
    'frame_sender',
    broker='redis://101.53.132.75:6379/0',
    backend='redis://101.53.132.75:6379/0'
)

# Ensure it can connect
def test_connection():
    try:
        result = celery_app.control.inspect().ping()
        print("✅ Connected to Celery worker:", result)
    except Exception as e:
        print("❌ Cannot connect to Celery:", e)

if __name__ == "__main__":
    test_connection()