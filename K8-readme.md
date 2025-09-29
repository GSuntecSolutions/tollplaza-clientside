# Machine B / Client 
cd firstbackend &&  source .venv/bin/activate
celery -A app.core_celeryworker1.celery_work1 worker --loglevel=info


# Architecture V2 :
[Frontend] ←→ [Next.js + FastAPI] ←→ [MongoDB]         ← Machine A
   ↑                ↑                   ↑
   |                |                   |
   |        [Celery: db_saver worker] ←┘
   |
   └── Polls DB → Triggers → [Redis Queue]
                             ↓
             [Celery: detector worker] → Detect + Save media → Results → Redis
                             ↑
                    [Frame Grabber Service]
                             ↑
                       [RTSP Cameras]

# =================== Steps of Installation and configuration on client end ============================

1. pull from git repo : 
2. Navigate to `app/core/db_sync.py` and change the db cridentails and config details 
3. Change the project name from this file `/root/NextjsApps/firstbackend/setup.py` as per cleint name ie  `name="firstbackend"`
4. Follow the `nfs-share-readme.md` file for nfs installation and configuration for drive share.
5. run command `source .venv/bin/activate`
6. run command `sudo pip install -r requirements.txt`
7. Run command `pip install -e .`

# V2 --version -----------with docker 
1. git pull 
2. docker build -f Dockerfile.detector -t toll-detector .
3. docker compose up -d   
            docker compose down 
4. docker ps # if process is no started then check logs
5. docker logs firstbackend-detector-1
6.  docker exec -it firstbackend-detector-1 /bin/bash
7.          celery -A app.core_celeryworker1.celery_work1 worker --loglevel=info
<!--for refer- app# celery -A app.core_celeryworker1.celery_work1 worker --loglevel=info -->



### NOTE:  location or path of the project should be same i.e 
1.  project path on Machine GSTS : `/root/NextjsApps/firstbackend/`
2.  project path on Machine Client Machine : `/root/NextjsApps/firstbackend/`

