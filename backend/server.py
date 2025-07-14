from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date
import base64
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ===============================
# MODELS
# ===============================

class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    cpf: str
    email: str
    phone: str
    address: str
    birth_date: date
    photo: Optional[str] = None
    medical_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CustomerCreate(BaseModel):
    name: str
    cpf: str
    email: str
    phone: str
    address: str
    birth_date: date
    photo: Optional[str] = None
    medical_notes: Optional[str] = None

class Package(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    price: float
    description: str
    duration_days: Optional[int] = None
    sessions_included: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PackageCreate(BaseModel):
    name: str
    type: str
    price: float
    description: str
    duration_days: Optional[int] = None
    sessions_included: Optional[int] = None

class CustomerPackage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    package_id: str
    purchase_date: date
    amount_paid: float
    payment_method: str
    status: str = "active"
    remaining_sessions: Optional[int] = None
    expiry_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CustomerPackageCreate(BaseModel):
    customer_id: str
    package_id: str
    purchase_date: date
    amount_paid: float
    payment_method: str
    remaining_sessions: Optional[int] = None
    expiry_date: Optional[date] = None

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    package_id: str
    date: date
    time: str
    service_type: str
    instructor: Optional[str] = None
    status: str = "scheduled"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AppointmentCreate(BaseModel):
    customer_id: str
    package_id: str
    date: date
    time: str
    service_type: str
    instructor: Optional[str] = None
    notes: Optional[str] = None

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_package_id: str
    amount: float
    payment_date: date
    payment_method: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentCreate(BaseModel):
    customer_package_id: str
    amount: float
    payment_date: date
    payment_method: str
    notes: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

VALID_USERNAME = "gabi"
VALID_PASSWORD = "gabi03"

@api_router.post("/login")
async def login_user(credentials: LoginRequest):
    if credentials.username == VALID_USERNAME and credentials.password == VALID_PASSWORD:
        return {"message": "Login realizado com sucesso!"}
    else:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")

# ===============================
# CUSTOMER ROUTES
# ===============================
# ... [mantém o restante do código original sem alterações nas rotas] ...

# ===============================
# BASIC ROUTES
# ===============================

@api_router.get("/")
async def root():
    return {"message": "Customer Management System API"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
