from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
import asyncpg
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date
import base64
import json

# Create the main app
app = FastAPI()

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ===============================
# DATABASE SETUP
# ===============================

async def get_database():
    return await asyncpg.connect(DATABASE_URL)

async def init_database():
    """Initialize database tables"""
    conn = await get_database()
    try:
        # Create customers table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                cpf VARCHAR NOT NULL,
                email VARCHAR NOT NULL,
                phone VARCHAR NOT NULL,
                address VARCHAR NOT NULL,
                birth_date DATE NOT NULL,
                photo TEXT,
                medical_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create packages table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS packages (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                type VARCHAR NOT NULL,
                price DECIMAL NOT NULL,
                description TEXT NOT NULL,
                duration_days INTEGER,
                sessions_included INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create customer_packages table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS customer_packages (
                id VARCHAR PRIMARY KEY,
                customer_id VARCHAR NOT NULL,
                package_id VARCHAR NOT NULL,
                purchase_date DATE NOT NULL,
                amount_paid DECIMAL NOT NULL,
                payment_method VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'active',
                remaining_sessions INTEGER,
                expiry_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create appointments table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id VARCHAR PRIMARY KEY,
                customer_id VARCHAR NOT NULL,
                package_id VARCHAR NOT NULL,
                date DATE NOT NULL,
                time VARCHAR NOT NULL,
                service_type VARCHAR NOT NULL,
                instructor VARCHAR,
                status VARCHAR DEFAULT 'scheduled',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create payments table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id VARCHAR PRIMARY KEY,
                customer_package_id VARCHAR NOT NULL,
                amount DECIMAL NOT NULL,
                payment_date DATE NOT NULL,
                payment_method VARCHAR NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("Database tables initialized successfully")
    finally:
        await conn.close()

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
# CUSTOMER ROUTES
# ===============================

@api_router.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    conn = await get_database()
    try:
        customer_dict = customer.dict()
        customer_id = str(uuid.uuid4())
        
        await conn.execute('''
            INSERT INTO customers (id, name, cpf, email, phone, address, birth_date, photo, medical_notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ''', customer_id, customer_dict['name'], customer_dict['cpf'], customer_dict['email'],
            customer_dict['phone'], customer_dict['address'], customer_dict['birth_date'],
            customer_dict.get('photo'), customer_dict.get('medical_notes'))
        
        customer_dict['id'] = customer_id
        return Customer(**customer_dict)
    finally:
        await conn.close()

@api_router.get("/customers", response_model=List[Customer])
async def get_customers():
    conn = await get_database()
    try:
        rows = await conn.fetch('SELECT * FROM customers ORDER BY created_at DESC')
        return [Customer(**dict(row)) for row in rows]
    finally:
        await conn.close()

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    conn = await get_database()
    try:
        row = await conn.fetchrow('SELECT * FROM customers WHERE id = $1', customer_id)
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")
        return Customer(**dict(row))
    finally:
        await conn.close()

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer: CustomerCreate):
    conn = await get_database()
    try:
        customer_dict = customer.dict()
        
        result = await conn.execute('''
            UPDATE customers 
            SET name=$2, cpf=$3, email=$4, phone=$5, address=$6, birth_date=$7, photo=$8, medical_notes=$9
            WHERE id=$1
        ''', customer_id, customer_dict['name'], customer_dict['cpf'], customer_dict['email'],
            customer_dict['phone'], customer_dict['address'], customer_dict['birth_date'],
            customer_dict.get('photo'), customer_dict.get('medical_notes'))
        
        if result == 'UPDATE 0':
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_dict['id'] = customer_id
        return Customer(**customer_dict)
    finally:
        await conn.close()

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    conn = await get_database()
    try:
        result = await conn.execute('DELETE FROM customers WHERE id = $1', customer_id)
        if result == 'DELETE 0':
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer deleted successfully"}
    finally:
        await conn.close()

# ===============================
# PACKAGE ROUTES
# ===============================

@api_router.post("/packages", response_model=Package)
async def create_package(package: PackageCreate):
    conn = await get_database()
    try:
        package_dict = package.dict()
        package_id = str(uuid.uuid4())
        
        await conn.execute('''
            INSERT INTO packages (id, name, type, price, description, duration_days, sessions_included)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', package_id, package_dict['name'], package_dict['type'], package_dict['price'],
            package_dict['description'], package_dict.get('duration_days'), package_dict.get('sessions_included'))
        
        package_dict['id'] = package_id
        return Package(**package_dict)
    finally:
        await conn.close()

@api_router.get("/packages", response_model=List[Package])
async def get_packages():
    conn = await get_database()
    try:
        rows = await conn.fetch('SELECT * FROM packages ORDER BY created_at DESC')
        return [Package(**dict(row)) for row in rows]
    finally:
        await conn.close()

@api_router.get("/packages/{package_id}", response_model=Package)
async def get_package(package_id: str):
    conn = await get_database()
    try:
        row = await conn.fetchrow('SELECT * FROM packages WHERE id = $1', package_id)
        if not row:
            raise HTTPException(status_code=404, detail="Package not found")
        return Package(**dict(row))
    finally:
        await conn.close()

@api_router.put("/packages/{package_id}", response_model=Package)
async def update_package(package_id: str, package: PackageCreate):
    conn = await get_database()
    try:
        package_dict = package.dict()
        
        result = await conn.execute('''
            UPDATE packages 
            SET name=$2, type=$3, price=$4, description=$5, duration_days=$6, sessions_included=$7
            WHERE id=$1
        ''', package_id, package_dict['name'], package_dict['type'], package_dict['price'],
            package_dict['description'], package_dict.get('duration_days'), package_dict.get('sessions_included'))
        
        if result == 'UPDATE 0':
            raise HTTPException(status_code=404, detail="Package not found")
        
        package_dict['id'] = package_id
        return Package(**package_dict)
    finally:
        await conn.close()

@api_router.delete("/packages/{package_id}")
async def delete_package(package_id: str):
    conn = await get_database()
    try:
        result = await conn.execute('DELETE FROM packages WHERE id = $1', package_id)
        if result == 'DELETE 0':
            raise HTTPException(status_code=404, detail="Package not found")
        return {"message": "Package deleted successfully"}
    finally:
        await conn.close()

# ===============================
# APPOINTMENT ROUTES
# ===============================

@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appointment: AppointmentCreate):
    conn = await get_database()
    try:
        appointment_dict = appointment.dict()
        appointment_id = str(uuid.uuid4())
        
        await conn.execute('''
            INSERT INTO appointments (id, customer_id, package_id, date, time, service_type, instructor, notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ''', appointment_id, appointment_dict['customer_id'], appointment_dict['package_id'],
            appointment_dict['date'], appointment_dict['time'], appointment_dict['service_type'],
            appointment_dict.get('instructor'), appointment_dict.get('notes'))
        
        appointment_dict['id'] = appointment_id
        return Appointment(**appointment_dict)
    finally:
        await conn.close()

@api_router.get("/appointments", response_model=List[Appointment])
async def get_appointments():
    conn = await get_database()
    try:
        rows = await conn.fetch('SELECT * FROM appointments ORDER BY date DESC, time DESC')
        return [Appointment(**dict(row)) for row in rows]
    finally:
        await conn.close()

# ===============================
# DASHBOARD ROUTES
# ===============================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    conn = await get_database()
    try:
        # Get counts
        total_customers = await conn.fetchval('SELECT COUNT(*) FROM customers')
        total_packages = await conn.fetchval('SELECT COUNT(*) FROM packages')
        total_appointments = await conn.fetchval('SELECT COUNT(*) FROM appointments')
        active_customer_packages = await conn.fetchval("SELECT COUNT(*) FROM customer_packages WHERE status = 'active'")
        
        # Get today's appointments
        today = datetime.now().date()
        today_appointments = await conn.fetchval('SELECT COUNT(*) FROM appointments WHERE date = $1', today)
        
        # Get recent payments
        recent_payments = await conn.fetch('SELECT * FROM payments ORDER BY payment_date DESC LIMIT 5')
        
        return {
            "total_customers": total_customers or 0,
            "total_packages": total_packages or 0,
            "total_appointments": total_appointments or 0,
            "active_customer_packages": active_customer_packages or 0,
            "today_appointments": today_appointments or 0,
            "recent_payments": [dict(payment) for payment in recent_payments]
        }
    finally:
        await conn.close()

# ===============================
# BASIC ROUTES
# ===============================

@api_router.get("/")
async def root():
    return {"message": "FitManager API - Sistema de Gestão de Clientes"}

# Include the router in the main app
app.include_router(api_router)

# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="build/static"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("build/index.html")

@app.get("/{path:path}")
async def serve_frontend_routes(path: str):
    # Serve frontend for all routes that don't start with /api
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    return FileResponse("build/index.html")

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

@app.on_event("startup")
async def startup_event():
    await init_database()