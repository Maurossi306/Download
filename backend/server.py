from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import uuid
import os
import logging
import secrets
import base64

# Load .env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Auth setup
security = HTTPBasic()
USERNAME = "gabi"
PASSWORD = "gabi03"

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username

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

# ===============================
# ROUTES WITH AUTH
# ===============================
@api_router.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate, user: str = Depends(authenticate)):
    data = customer.dict()
    data["birth_date"] = data["birth_date"].isoformat()
    customer_obj = Customer(**data)
    await db.customers.insert_one(customer_obj.dict())
    return customer_obj

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(user: str = Depends(authenticate)):
    customers = await db.customers.find().to_list(1000)
    return [Customer(**c) for c in customers]

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str, user: str = Depends(authenticate)):
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(**customer)

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer: CustomerCreate, user: str = Depends(authenticate)):
    data = customer.dict()
    data["birth_date"] = data["birth_date"].isoformat()
    data["id"] = customer_id
    customer_obj = Customer(**data)
    result = await db.customers.replace_one({"id": customer_id}, customer_obj.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer_obj

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, user: str = Depends(authenticate)):
    result = await db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted"}

# Você deve repetir `user: str = Depends(authenticate)` nas demais rotas, como:
# - /packages
# - /customer-packages
# - /appointments
# - /payments
# - /dashboard/stats

# ===============================
# ROOT E FINALIZAÇÃO
# ===============================
@api_router.get("/")
async def root(user: str = Depends(authenticate)):
    return {"message": "API com autenticação ativa"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

logging.basicConfig(level=logging.INFO)
