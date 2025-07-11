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
    photo: Optional[str] = None  # base64 encoded
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
    type: str  # "monthly", "per_session", "procedure"
    price: float
    description: str
    duration_days: Optional[int] = None  # for monthly packages
    sessions_included: Optional[int] = None  # for session packages
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
    status: str = "active"  # active, expired, cancelled
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
    status: str = "scheduled"  # scheduled, completed, cancelled
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
# CUSTOMER ROUTES
# ===============================

@api_router.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    customer_dict = customer.dict()
    # Convert date to string for MongoDB
    if 'birth_date' in customer_dict:
        customer_dict['birth_date'] = customer_dict['birth_date'].isoformat()
    customer_obj = Customer(**customer_dict)
    # Convert the object to dict and ensure dates are strings
    customer_data = customer_obj.dict()
    if 'birth_date' in customer_data and isinstance(customer_data['birth_date'], date):
        customer_data['birth_date'] = customer_data['birth_date'].isoformat()
    await db.customers.insert_one(customer_data)
    return customer_obj

@api_router.get("/customers", response_model=List[Customer])
async def get_customers():
    customers = await db.customers.find().to_list(1000)
    return [Customer(**customer) for customer in customers]

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(**customer)

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer: CustomerCreate):
    customer_dict = customer.dict()
    # Convert date to string for MongoDB
    if isinstance(customer_dict.get('birth_date'), date):
        customer_dict['birth_date'] = customer_dict['birth_date'].isoformat()
    customer_dict["id"] = customer_id
    customer_obj = Customer(**customer_dict)
    
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

# ===============================
# PACKAGE ROUTES
# ===============================

@api_router.post("/packages", response_model=Package)
async def create_package(package: PackageCreate):
    package_dict = package.dict()
    package_obj = Package(**package_dict)
    await db.packages.insert_one(package_obj.dict())
    return package_obj

@api_router.get("/packages", response_model=List[Package])
async def get_packages():
    packages = await db.packages.find().to_list(1000)
    return [Package(**package) for package in packages]

@api_router.get("/packages/{package_id}", response_model=Package)
async def get_package(package_id: str):
    package = await db.packages.find_one({"id": package_id})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return Package(**package)

@api_router.put("/packages/{package_id}", response_model=Package)
async def update_package(package_id: str, package: PackageCreate):
    package_dict = package.dict()
    package_dict["id"] = package_id
    package_obj = Package(**package_dict)
    
    result = await db.packages.replace_one({"id": package_id}, package_obj.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Package not found")
    return package_obj

@api_router.delete("/packages/{package_id}")
async def delete_package(package_id: str):
    result = await db.packages.delete_one({"id": package_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Package not found")
    return {"message": "Package deleted successfully"}

# ===============================
# CUSTOMER PACKAGE ROUTES
# ===============================

@api_router.post("/customer-packages", response_model=CustomerPackage)
async def create_customer_package(customer_package: CustomerPackageCreate):
    customer_package_dict = customer_package.dict()
    # Convert dates to strings for MongoDB
    if isinstance(customer_package_dict.get('purchase_date'), date):
        customer_package_dict['purchase_date'] = customer_package_dict['purchase_date'].isoformat()
    if isinstance(customer_package_dict.get('expiry_date'), date):
        customer_package_dict['expiry_date'] = customer_package_dict['expiry_date'].isoformat()
    customer_package_obj = CustomerPackage(**customer_package_dict)
    await db.customer_packages.insert_one(customer_package_obj.dict())
    return customer_package_obj

@api_router.get("/customer-packages", response_model=List[CustomerPackage])
async def get_customer_packages():
    customer_packages = await db.customer_packages.find().to_list(1000)
    return [CustomerPackage(**cp) for cp in customer_packages]

@api_router.get("/customer-packages/customer/{customer_id}", response_model=List[CustomerPackage])
async def get_customer_packages_by_customer(customer_id: str):
    customer_packages = await db.customer_packages.find({"customer_id": customer_id}).to_list(1000)
    return [CustomerPackage(**cp) for cp in customer_packages]

# ===============================
# APPOINTMENT ROUTES
# ===============================

@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appointment: AppointmentCreate):
    appointment_dict = appointment.dict()
    # Convert date to string for MongoDB
    if isinstance(appointment_dict.get('date'), date):
        appointment_dict['date'] = appointment_dict['date'].isoformat()
    appointment_obj = Appointment(**appointment_dict)
    await db.appointments.insert_one(appointment_obj.dict())
    return appointment_obj

@api_router.get("/appointments", response_model=List[Appointment])
async def get_appointments():
    appointments = await db.appointments.find().to_list(1000)
    return [Appointment(**appointment) for appointment in appointments]

@api_router.get("/appointments/date/{date}")
async def get_appointments_by_date(date: str):
    appointments = await db.appointments.find({"date": date}).to_list(1000)
    return [Appointment(**appointment) for appointment in appointments]

@api_router.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: str, appointment: AppointmentCreate):
    appointment_dict = appointment.dict()
    # Convert date to string for MongoDB
    if isinstance(appointment_dict.get('date'), date):
        appointment_dict['date'] = appointment_dict['date'].isoformat()
    appointment_dict["id"] = appointment_id
    appointment_obj = Appointment(**appointment_dict)
    
    result = await db.appointments.replace_one({"id": appointment_id}, appointment_obj.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment_obj

# ===============================
# PAYMENT ROUTES
# ===============================

@api_router.post("/payments", response_model=Payment)
async def create_payment(payment: PaymentCreate):
    payment_dict = payment.dict()
    # Convert date to string for MongoDB
    if isinstance(payment_dict.get('payment_date'), date):
        payment_dict['payment_date'] = payment_dict['payment_date'].isoformat()
    payment_obj = Payment(**payment_dict)
    await db.payments.insert_one(payment_obj.dict())
    return payment_obj

@api_router.get("/payments", response_model=List[Payment])
async def get_payments():
    payments = await db.payments.find().to_list(1000)
    return [Payment(**payment) for payment in payments]

# ===============================
# DASHBOARD ROUTES
# ===============================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    # Get counts
    total_customers = await db.customers.count_documents({})
    total_packages = await db.packages.count_documents({})
    total_appointments = await db.appointments.count_documents({})
    active_customer_packages = await db.customer_packages.count_documents({"status": "active"})
    
    # Get today's appointments
    today = datetime.now().date().isoformat()
    today_appointments = await db.appointments.find({"date": today}).to_list(1000)
    
    # Get recent payments
    recent_payments = await db.payments.find().sort("payment_date", -1).limit(5).to_list(5)
    
    return {
        "total_customers": total_customers,
        "total_packages": total_packages,
        "total_appointments": total_appointments,
        "active_customer_packages": active_customer_packages,
        "today_appointments": len(today_appointments),
        "recent_payments": recent_payments
    }

# ===============================
# BASIC ROUTES
# ===============================

@api_router.get("/")
async def root():
    return {"message": "Customer Management System API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()