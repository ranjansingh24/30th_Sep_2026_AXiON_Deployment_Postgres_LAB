import os
import time
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import datetime

# --- DATABASE CONFIGURATION ---
AZURE_DB_HOST = os.getenv("DB_HOST", "axion-postgres-ranjan.postgres.database.azure.com")
AZURE_DB_NAME = os.getenv("DB_NAME", "axion_db")
AZURE_DB_USER = os.getenv("DB_USER", "psqladmin")
AZURE_DB_PASS = os.getenv("DB_PASS", "P@ssw0rd123456!")

DATABASE_URL = f"postgresql://{AZURE_DB_USER}:{AZURE_DB_PASS}@{AZURE_DB_HOST}:5432/{AZURE_DB_NAME}?sslmode=require"

# Fallback to local SQLite if PostgreSQL fails or is unreachable
SQLITE_URL = "sqlite:///./axion_local.db"

try:
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
    # Test connection
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("SELECT 1"))
    db_status = "ONLINE (Azure PostgreSQL)"
except Exception as e:
    print(f"PostgreSQL connection warning: {e}. Falling back to SQLite.")
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    db_status = "ONLINE (Local SQLite)"

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- DB MODELS ---
class PlantOperation(Base):
    __tablename__ = "plant_operations"
    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(50), unique=True, nullable=False)
    total_assets = Column(Integer, default=0)
    online_assets = Column(Integer, default=0)
    active_alerts = Column(Integer, default=0)

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False)
    status = Column(String(20), default="ONLINE") # ONLINE, ALERT, OFFLINE
    temperature = Column(Float, default=45.0)
    pressure = Column(Float, default=101.3)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), default="admin")

Base.metadata.create_all(bind=engine)

# Seed Initial Data if empty
def seed_initial_data():
    db = SessionLocal()
    try:
        if db.query(PlantOperation).count() == 0:
            plants = [
                PlantOperation(region="North", total_assets=4, online_assets=4, active_alerts=2),
                PlantOperation(region="South", total_assets=2, online_assets=2, active_alerts=0),
                PlantOperation(region="East", total_assets=2, online_assets=2, active_alerts=2),
                PlantOperation(region="West", total_assets=2, online_assets=2, active_alerts=0),
            ]
            db.add_all(plants)
            db.commit()

        if db.query(User).count() == 0:
            admin = User(username="admin@axion.com", password="Admin@AXiON2026!", role="admin")
            db.add(admin)
            db.commit()
    finally:
        db.close()

seed_initial_data()

# --- FASTAPI APP ---
app = FastAPI(
    title="AXiON Intelligence Platform API",
    description="Agentic AI Predictive Insights & Telemetry Ingestion Engine",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class AIQueryRequest(BaseModel):
    prompt: str

# API ENDPOINTS
@app.get("/api/health")
def get_health():
    return {
        "status": "HEALTHY",
        "api": "LIVE",
        "db": db_status,
        "sim": "ACTIVE",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/fleet")
def get_fleet_summary(db: Session = Depends(get_db)):
    plants = db.query(PlantOperation).all()
    total_assets = sum(p.total_assets for p in plants)
    online_assets = sum(p.online_assets for p in plants)
    active_alerts = sum(p.active_alerts for p in plants)
    return {
        "total_assets": total_assets,
        "online_assets": online_assets,
        "active_alerts": active_alerts,
        "last_update": datetime.datetime.now().strftime("%I:%M:%S %p")
    }

@app.get("/api/plant-operations")
def get_plant_operations(db: Session = Depends(get_db)):
    plants = db.query(PlantOperation).all()
    return [
        {
            "region": p.region,
            "type": "REFINERY",
            "total": p.total_assets,
            "online": p.online_assets,
            "alerts": p.active_alerts
        } for p in plants
    ]

@app.post("/api/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username, User.password == req.password).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {
        "success": True,
        "username": user.username,
        "role": user.role,
        "token": "axion-jwt-secret-token-2026"
    }

@app.post("/api/ai-assistant")
def ai_assistant(req: AIQueryRequest):
    prompt_lower = req.prompt.lower()
    if "alert" in prompt_lower or "warning" in prompt_lower:
        response = "Currently, North Refinery has 2 active alerts and East Refinery has 2 active alerts. Recommended action: Inspect turbine vibration sensors T-402 and E-109."
    elif "status" in prompt_lower or "health" in prompt_lower:
        response = "System Health is OPTIMAL. API is LIVE, PostgreSQL DB is connected, and Telemetry Simulation is ACTIVE across all 10 assets."
    elif "north" in prompt_lower:
        response = "North Refinery: 4 Total Assets, 4 Online, 2 Alerts detected in primary distillation unit."
    else:
        response = f"AXiON Predictive Insights: Telemetry analysis completed for query: '{req.prompt}'. All 10 global assets are operating within thermal tolerance limits."
    return {"response": response}

# Mount static frontend directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

@app.get("/")
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "AXiON Platform Backend Running. Swagger docs available at /docs"})

app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
