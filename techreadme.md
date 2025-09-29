```markdown
## Creating a Python Virtual Environment

To create a virtual environment in your project directory, run:

```bash
python -m venv .venv
source .venv/bin/activate #  to activate teh env
uvicorn app.core.main:app --reload --port 5000  # to run teh backend 
docker compose up -d # to update mongodb as it dockercompose is configure for DB
docker compose down # to down the container 
docker exec -it mongodb-tmps-firsttry mongosh -u admin -p admin123  # -- get into mongodb DB up by docker compose manually 
```

This will create a folder named `env` containing the virtual environment.
```
## If you need to free up a port (for example, port 4000) before starting your development server, you can use the following command:

```bash
sudo fuser -k -n tcp 4000
```

This will kill any process using TCP port 4000.

## How to connect FE with BE?
    next.config.js file in the firstapp (frontend) folder. 
    // firstapp/next.config.js

    ````
    module.exports = {
      async rewrites() {
        return [
          {
            source: '/api/:path*',
            destination: 'http://localhost:5000/:path*', // Match your backend's URL
          },
        ];
      },
    };
    ````

    Step 2: Change Frontend fetch Calls
    With the proxy set up, your fetch calls in the frontend code can remain as they are
    #/pages/setup.tsx
    ```const response = await fetch('/api/cameras');```

  BACKEND :
    Step 3: FastAPI web server on a different port, you need to specify the port number when you start the server using Uvicorn
    uvicorn main:app --port 5000
    # main: The name of your Python file (e.g., main.py).
    # app: The name of the FastAPI() instance within that file (e.g., app = FastAPI()).
    # --port 5000: The flag that tells Uvicorn to listen on port 5000.
    # 127.0.0.1 is for localhost, while 0.0.0.0 makes it accessible from any network interface.

  step 4:
  app/main.py
  Import the middleware
  from contextlib import asynccontextmanager
  from app.routes import router

  app = FastAPI(lifespan=lifespan)
  # Corrected: Remove the prefix="/api" here.
  app.include_router(router)



    Step 5:
    # app/routes.py
    from fastapi import APIRouter, HTTPException
    # from app.database import db
    from app.api.cameras import router as cameras_router

    # The main router for the application
    router = APIRouter(prefix="/api")
    # router = APIRouter()

    # Include sub-routers
    router.include_router(cameras_router)

    Step 6:
    # app/api/cameras.py
    router = APIRouter(prefix="/cameras", tags=["Cameras"])

    # GET /api/cameras — Get all cameras
    @router.get("/")
    async def get_cameras():
    .......

============= Using a Singleton Pattern =======
# Use a global variable to store the model
    global yolo_model
    if yolo_model is None:
        try:
            # The YOLO class handles the model loading internally
            yolo_model = YOLO('yolov8n.pt')
....

=======>>  FastAPI project (firstbackend), install motor (async MongoDB driver for Python): ` pip install motor python-dotenv`
=======>> How to used port config when project and db docker in same container ?

# firstbackend/.env
MONGODB_URI=mongodb://localhost:27018
# in docker-compose.yml, ports: - "27018:27017". which means Host port: 27018, Container port: 27017. So use 27018 to connect from host machine.
# MONGODB_URI=mongodb://mongodb:27017 ===> If both (If your FastAPI app runs in Docker) are in Docker (same network), use service name:



=======>>  How to get the values from .evn file ??

Step 1 : 
create .env file under root folder 
MONGODB_USERNAME=admin
MONGODB_PASSWORD=admin123

Step 2:  us `os` lib to get the variable 
# app/database.py 
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables from .env
load_dotenv()

# Read config
MONGODB_HOST = os.getenv("MONGODB_URI")


============>> How to include apis calls in swagger?
 FastAPI automatically generates interactive API documentation in Swagger UI and ReDoc. You don't need to write any extra code to create it.

    Swagger UI: http://localhost:5000/docs 📝
    ReDoc: http://localhost:5000/redoc 



============>> how to connect BE to DB?
Steps : run your db container 

Step 2:
# app/api/cameras.py
from fastapi import APIRouter, HTTPException
from app.database import db

# GET /api/cameras — Get all cameras
@router.get("/")
async def get_cameras():
    try:
        collection = db["cameras"]
        cameras = await collection.find().to_list(100)
        return [
            {**cam, "_id": str(cam["_id"])} for cam in cameras
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cameras: {str(e)}")


Step 3:
# app/database.py
# Read config
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
# Build authenticated URI
if MONGODB_USERNAME and MONGODB_PASSWORD:
    # URL-encode username and password
    client_uri = f"mongodb://{username}:{password}@{host_part}/{MONGODB_NAME}?authSource=admin"
    print("🚀 Final MongoDB URI:", client_uri.replace(password, "*****"))

# --- Health check ---
async def connect_to_db():
    try:
        await client.admin.command('ping')
        print(f"🟢 Successfully connected to MongoDB: {MONGODB_NAME}")
    except Exception as e:
        print(f"🔴 Failed to connect to MongoDB: {e}")
        raise



# ---- Multiplpe python versions on server ---
down load py version of Gzipped source tarball from https://www.python.org/
movie to server usinng winscp untar and install
sudo tar xzf Python-3.12.4.tgz
cd Python-3.12.4
sudo ./configure --enable-optimizations --prefix=/opt/python-3.12.4
sudo make -j$(nproc)
sudo make altinstall
navigate to fproject and
cd /root/NextjsApps/firstbackend
/opt/python-3.12.4/bin/python3.12 -m venv .venv


# -- install and uninstall requirments file 
pip install -r requirements.txt
pip uninstall -r requirements.txt


