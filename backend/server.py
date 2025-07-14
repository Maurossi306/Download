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

# Carrega variáveis do .env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Conexão com o MongoDB
mongo_url = os.environ.get("MONGO_URL")
db_name = os.environ.get("DB_NAME")

if not mongo_url or not db_name:
    raise ValueError("As variáveis MONGO_URL e DB_NAME precisam estar no .env")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Criação do app principal
app = FastAPI()
api_router = APIRouter(prefix="/api")

# MODELS
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

# CUSTOMER ROUTES
@api_router.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    data = customer.dict()
    data['birth_date'] = data['birth_date'].isoformat()
    customer_obj = Customer(**data)
    await db.customers.insert_one(customer_obj.dict())
    return customer_obj

@api_router.get("/customers", response_model=List[Customer])
async def get_customers():
    customers = await db.customers.find().to_list(1000)
    return [Customer(**c) for c in customers]

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(**customer)

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer: CustomerCreate):
    data = customer.dict()
    data['birth_date'] = data['birth_date'].isoformat()
    data['id'] = customer_id
    customer_obj = Customer(**data)
    result = await db.customers.replace_one({"id": customer_id}, customer_obj.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer_obj

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    result = await db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted successfully"}

# Resto das rotas (packages, appointments, payments, dashboard) segue a mesma lógica... posso continuar se quiser

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
