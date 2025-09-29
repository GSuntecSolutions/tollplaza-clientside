# set up to support multiple lines architecturre 

[Capture] → [Queue] → [Process/Detect] → [Queue] → [Save to DB]

# in details :
[Frontend]
   ↓
[API Gateway] → Save RTSP + Lane → MongoDB
   ↓
[Frame Grabber Service] ← Polls DB or listens for new lanes
   ↓
Captures frame every N seconds → Sends to Redis Queue (`frames`)
   ↓
[Celery Worker - Detection] ← Listens to `frames` queue
   ↓
Runs YOLO → Outputs {vehicle_type, bbox, timestamp}
   ↓
Sends result to Redis Queue (`results`)
   ↓
[Celery Worker - Saver] ← Listens to `results` queue
   ↓
Saves to MongoDB
   ↓
[Frontend] ← GET /api/results → shows data

# this is how messaging system works :
[Frame Grabber]
       ↓
   Redis (on Machine A)
     ↙              ↘
[Celery Worker 1]   [Celery Worker 2]
(GPU Machine B)     (DB Machine C)
YOLO Detection      Save to MongoDB

# Narrow down :
[Frame Grabber on Server A]
         ↓
     Redis @ 101.53.132.75:6379
         ↓ (lpush to "frames")
[Celery Worker on Server B]
         ↓
Celery connects to Redis at redis://101.53.132.75:6379
Polls for tasks → finds messages in default queue ("celery")
Calls `process_frame.delay(...)` → executes task




# how to kill redis porcess 
sudo systemctl stop redis-server

# redis config file location 
sudo nano /etc/redis/redis.conf
  
# this way we are sending frames to celery B from celery A m/c: Send the Frame Image (Base64) in the Message
Capture the frame
Encode it as base64
Include it in the message under "frame"


# Save images at client machine and link in our db : Save Image on Machine B + Store Path in DB (Best Practice)
[Frame Grabber A] → sends frame → [Worker B]
     ↓
[Worker B] saves image to disk: `/shared/images/123.jpg`
     ↓
Saves only file path in DB: `/images/123.jpg`
     ↓
Frontend requests: http://localhost:4000/images/123.jpg



# ---How many servicess need to start to start the project :
# -----GSTS machine / NON GPU / 101.53.132.75 / Machine A
1. FE : cd firstapp && npm run dev
2. BE : 
      2.1. move to .venv : source .venv/bin/activate
      2.2. start it :  uvicorn app.core.main:app --reload --port 5000
3. redis-server : 
      redis-server # to start the server 
      sudo systemctl restart  redis-server # 
         NOTE: sudo nano /etc/redis/redis.conf
         NOTE: restart service is not working. debugging solution is in the point ##3.a. in debugging section 
4. mongoDB :
      cd firstbackend/ && source .venv/bin/activate
      cd mongodb-firsttry/ && docker compose up -d 
      docker compose down 
      to check the db container manually : docker exec -it mongodb-tmps-firsttry mongosh -u admin -p admin123 
5. run python program to retrieve images:
       cd firstbackend/ && source .venv/bin/activate
      python app/redis_que_sys/redis_frame_grabber.py

6. Celery at m/c A to collected the data from M/c B and saved in DB 
       cd firstbackend/ && source .venv/bin/activate
       celery -A app.redis_que_sys.db_saver worker --loglevel=info (celery -A app.redis_que_sys.db_saver worker --loglevel=info --queues=db_saver)
NOTE : images locatiuonshared path /root/NextjsApps/firstapp/shared-images


# -----Client  machine / GPU / 64.52.201.243 / Machine B
7. celery on M/c B to handle shake with m/c A and collect the frames from m/c A
      cd /root/sachin-celery1/ && source .venv/bin/activate
      celery -A app.core_celeryworker1.celery_work1 worker --loglevel=info 
NOTE: images are stores at /shared/images




# To run python program at M/c A (non gpu)
(.venv) root@101-53-132-75:~/NextjsApps/firstbackend# python app/redis_que_sys/redis_frame_grabber.py 






# ========================================DEBUGGING =======================================
# --3.a. redis restart is not working 
         sudo ps aux | grep redis
        # Force kill the Redis process
            sudo kill -9 710387
        # Alternatively, kill all Redis processes
            sudo pkill -9 redis-server
        # Check if there are any Redis lock files
            sudo ls -la /var/run/redis/

        # Remove any stale PID files
            sudo rm -f /var/run/redis/redis-server.pid
        # Check for socket files
            sudo ls -la /var/run/redis/redis.sock
        # Now try to restart Redis
            sudo systemctl daemon-reload
            sudo systemctl start redis-server
            sudo systemctl status redis-server

