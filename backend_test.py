#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Customer Management System
Tests all CRUD operations for customers, packages, appointments, payments, and dashboard stats
"""

import requests
import json
from datetime import datetime, date, timedelta
import base64
import sys
import os

# Get backend URL from frontend .env file
BACKEND_URL = "https://fa7c640b-54f3-419e-be86-4a033b35843e.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_data = {}
        self.errors = []
        self.successes = []
        
    def log_success(self, message):
        print(f"✅ {message}")
        self.successes.append(message)
        
    def log_error(self, message):
        print(f"❌ {message}")
        self.errors.append(message)
        
    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request and handle response"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "PUT":
                response = requests.put(url, json=data)
            elif method == "DELETE":
                response = requests.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            if response.status_code == expected_status:
                return response.json() if response.content else {}
            else:
                self.log_error(f"{method} {endpoint} - Expected {expected_status}, got {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log_error(f"{method} {endpoint} - Request failed: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            self.log_error(f"{method} {endpoint} - JSON decode error: {str(e)}")
            return None
    
    def test_api_root(self):
        """Test basic API connectivity"""
        print("\n🔍 Testing API Root Endpoint...")
        result = self.make_request("GET", "/")
        if result and "message" in result:
            self.log_success("API root endpoint accessible")
            return True
        else:
            self.log_error("API root endpoint not accessible")
            return False
    
    def test_customer_management(self):
        """Test Customer CRUD operations"""
        print("\n🔍 Testing Customer Management API...")
        
        # Test data for customers
        customers_data = [
            {
                "name": "Maria Silva Santos",
                "cpf": "123.456.789-01",
                "email": "maria.santos@email.com",
                "phone": "(11) 99999-1234",
                "address": "Rua das Flores, 123 - São Paulo, SP",
                "birth_date": "1985-03-15",
                "photo": base64.b64encode(b"fake_photo_data_maria").decode(),
                "medical_notes": "Histórico de lesão no joelho direito. Evitar exercícios de alto impacto."
            },
            {
                "name": "João Carlos Oliveira",
                "cpf": "987.654.321-09",
                "email": "joao.oliveira@email.com",
                "phone": "(11) 88888-5678",
                "address": "Av. Paulista, 456 - São Paulo, SP",
                "birth_date": "1990-07-22",
                "medical_notes": "Sem restrições médicas conhecidas."
            }
        ]
        
        # CREATE customers
        created_customers = []
        for customer_data in customers_data:
            result = self.make_request("POST", "/customers", customer_data, 200)
            if result and "id" in result:
                created_customers.append(result)
                self.log_success(f"Created customer: {result['name']}")
            else:
                self.log_error(f"Failed to create customer: {customer_data['name']}")
                
        if not created_customers:
            self.log_error("No customers created - cannot continue customer tests")
            return False
            
        self.test_data['customers'] = created_customers
        
        # READ all customers
        result = self.make_request("GET", "/customers")
        if result and isinstance(result, list) and len(result) >= len(created_customers):
            self.log_success(f"Retrieved {len(result)} customers")
        else:
            self.log_error("Failed to retrieve customers list")
            
        # READ specific customer
        customer_id = created_customers[0]['id']
        result = self.make_request("GET", f"/customers/{customer_id}")
        if result and result['id'] == customer_id:
            self.log_success(f"Retrieved specific customer: {result['name']}")
        else:
            self.log_error(f"Failed to retrieve customer {customer_id}")
            
        # UPDATE customer
        update_data = customers_data[0].copy()
        update_data['phone'] = "(11) 99999-9999"
        result = self.make_request("PUT", f"/customers/{customer_id}", update_data)
        if result and result['phone'] == update_data['phone']:
            self.log_success(f"Updated customer phone: {result['phone']}")
        else:
            self.log_error(f"Failed to update customer {customer_id}")
            
        # DELETE customer (use second customer to keep first for other tests)
        if len(created_customers) > 1:
            delete_id = created_customers[1]['id']
            result = self.make_request("DELETE", f"/customers/{delete_id}")
            if result and "message" in result:
                self.log_success(f"Deleted customer {delete_id}")
            else:
                self.log_error(f"Failed to delete customer {delete_id}")
        
        return True
    
    def test_package_management(self):
        """Test Package CRUD operations"""
        print("\n🔍 Testing Package Management API...")
        
        # Test data for packages
        packages_data = [
            {
                "name": "Pilates Mensal Premium",
                "type": "monthly",
                "price": 350.00,
                "description": "Acesso ilimitado às aulas de Pilates durante 30 dias",
                "duration_days": 30,
                "sessions_included": None
            },
            {
                "name": "Pacote 8 Sessões Funcionais",
                "type": "per_session",
                "price": 480.00,
                "description": "8 sessões de treinamento funcional personalizado",
                "duration_days": None,
                "sessions_included": 8
            },
            {
                "name": "Tratamento Estético Facial",
                "type": "procedure",
                "price": 180.00,
                "description": "Sessão única de tratamento facial com limpeza profunda",
                "duration_days": None,
                "sessions_included": 1
            }
        ]
        
        # CREATE packages
        created_packages = []
        for package_data in packages_data:
            result = self.make_request("POST", "/packages", package_data, 200)
            if result and "id" in result:
                created_packages.append(result)
                self.log_success(f"Created package: {result['name']} ({result['type']})")
            else:
                self.log_error(f"Failed to create package: {package_data['name']}")
                
        if not created_packages:
            self.log_error("No packages created - cannot continue package tests")
            return False
            
        self.test_data['packages'] = created_packages
        
        # READ all packages
        result = self.make_request("GET", "/packages")
        if result and isinstance(result, list) and len(result) >= len(created_packages):
            self.log_success(f"Retrieved {len(result)} packages")
        else:
            self.log_error("Failed to retrieve packages list")
            
        # READ specific package
        package_id = created_packages[0]['id']
        result = self.make_request("GET", f"/packages/{package_id}")
        if result and result['id'] == package_id:
            self.log_success(f"Retrieved specific package: {result['name']}")
        else:
            self.log_error(f"Failed to retrieve package {package_id}")
            
        # UPDATE package
        update_data = packages_data[0].copy()
        update_data['price'] = 380.00
        result = self.make_request("PUT", f"/packages/{package_id}", update_data)
        if result and result['price'] == update_data['price']:
            self.log_success(f"Updated package price: R$ {result['price']}")
        else:
            self.log_error(f"Failed to update package {package_id}")
            
        # DELETE package (use last package to keep others for tests)
        if len(created_packages) > 1:
            delete_id = created_packages[-1]['id']
            result = self.make_request("DELETE", f"/packages/{delete_id}")
            if result and "message" in result:
                self.log_success(f"Deleted package {delete_id}")
                # Remove from test data
                self.test_data['packages'] = [p for p in created_packages if p['id'] != delete_id]
            else:
                self.log_error(f"Failed to delete package {delete_id}")
        
        return True
    
    def test_customer_package_relationships(self):
        """Test Customer-Package relationship management"""
        print("\n🔍 Testing Customer-Package Relationships...")
        
        if not self.test_data.get('customers') or not self.test_data.get('packages'):
            self.log_error("Missing customers or packages data - cannot test relationships")
            return False
            
        customer = self.test_data['customers'][0]
        package = self.test_data['packages'][0]
        
        # CREATE customer-package relationship
        today = date.today()
        expiry_date = today + timedelta(days=30)
        
        customer_package_data = {
            "customer_id": customer['id'],
            "package_id": package['id'],
            "purchase_date": today.isoformat(),
            "amount_paid": package['price'],
            "payment_method": "Cartão de Crédito",
            "remaining_sessions": package.get('sessions_included'),
            "expiry_date": expiry_date.isoformat() if package['type'] == 'monthly' else None
        }
        
        result = self.make_request("POST", "/customer-packages", customer_package_data, 200)
        if result and "id" in result:
            self.test_data['customer_packages'] = [result]
            self.log_success(f"Created customer-package relationship: {customer['name']} -> {package['name']}")
        else:
            self.log_error("Failed to create customer-package relationship")
            return False
            
        # READ all customer-packages
        result = self.make_request("GET", "/customer-packages")
        if result and isinstance(result, list) and len(result) >= 1:
            self.log_success(f"Retrieved {len(result)} customer-package relationships")
        else:
            self.log_error("Failed to retrieve customer-packages list")
            
        # READ customer-packages by customer
        result = self.make_request("GET", f"/customer-packages/customer/{customer['id']}")
        if result and isinstance(result, list) and len(result) >= 1:
            self.log_success(f"Retrieved customer-packages for customer: {customer['name']}")
        else:
            self.log_error(f"Failed to retrieve customer-packages for customer {customer['id']}")
        
        return True
    
    def test_appointment_scheduling(self):
        """Test Appointment CRUD operations"""
        print("\n🔍 Testing Appointment Scheduling API...")
        
        if not self.test_data.get('customers') or not self.test_data.get('packages'):
            self.log_error("Missing customers or packages data - cannot test appointments")
            return False
            
        customer = self.test_data['customers'][0]
        package = self.test_data['packages'][0]
        
        # Test data for appointments
        tomorrow = date.today() + timedelta(days=1)
        appointments_data = [
            {
                "customer_id": customer['id'],
                "package_id": package['id'],
                "date": tomorrow.isoformat(),
                "time": "09:00",
                "service_type": "Pilates Mat",
                "instructor": "Ana Paula Silva",
                "notes": "Cliente prefere exercícios de baixo impacto"
            },
            {
                "customer_id": customer['id'],
                "package_id": package['id'],
                "date": (tomorrow + timedelta(days=2)).isoformat(),
                "time": "14:30",
                "service_type": "Pilates Equipamentos",
                "instructor": "Carlos Roberto",
                "notes": "Foco em fortalecimento do core"
            }
        ]
        
        # CREATE appointments
        created_appointments = []
        for appointment_data in appointments_data:
            result = self.make_request("POST", "/appointments", appointment_data, 200)
            if result and "id" in result:
                created_appointments.append(result)
                self.log_success(f"Created appointment: {result['date']} {result['time']} - {result['service_type']}")
            else:
                self.log_error(f"Failed to create appointment for {appointment_data['date']}")
                
        if not created_appointments:
            self.log_error("No appointments created - cannot continue appointment tests")
            return False
            
        self.test_data['appointments'] = created_appointments
        
        # READ all appointments
        result = self.make_request("GET", "/appointments")
        if result and isinstance(result, list) and len(result) >= len(created_appointments):
            self.log_success(f"Retrieved {len(result)} appointments")
        else:
            self.log_error("Failed to retrieve appointments list")
            
        # READ appointments by date
        test_date = tomorrow.isoformat()
        result = self.make_request("GET", f"/appointments/date/{test_date}")
        if result and isinstance(result, list):
            self.log_success(f"Retrieved appointments for date {test_date}: {len(result)} found")
        else:
            self.log_error(f"Failed to retrieve appointments for date {test_date}")
            
        # UPDATE appointment
        appointment_id = created_appointments[0]['id']
        update_data = appointments_data[0].copy()
        update_data['time'] = "10:00"
        update_data['notes'] = "Horário alterado conforme solicitação do cliente"
        
        result = self.make_request("PUT", f"/appointments/{appointment_id}", update_data)
        if result and result['time'] == update_data['time']:
            self.log_success(f"Updated appointment time: {result['time']}")
        else:
            self.log_error(f"Failed to update appointment {appointment_id}")
        
        return True
    
    def test_payment_control(self):
        """Test Payment management"""
        print("\n🔍 Testing Payment Control API...")
        
        if not self.test_data.get('customer_packages'):
            self.log_error("Missing customer-package data - cannot test payments")
            return False
            
        customer_package = self.test_data['customer_packages'][0]
        
        # Test data for payments
        payments_data = [
            {
                "customer_package_id": customer_package['id'],
                "amount": 175.00,
                "payment_date": date.today().isoformat(),
                "payment_method": "Cartão de Crédito",
                "notes": "Primeira parcela do pacote mensal"
            },
            {
                "customer_package_id": customer_package['id'],
                "amount": 175.00,
                "payment_date": (date.today() + timedelta(days=15)).isoformat(),
                "payment_method": "PIX",
                "notes": "Segunda parcela do pacote mensal"
            }
        ]
        
        # CREATE payments
        created_payments = []
        for payment_data in payments_data:
            result = self.make_request("POST", "/payments", payment_data, 200)
            if result and "id" in result:
                created_payments.append(result)
                self.log_success(f"Created payment: R$ {result['amount']} via {result['payment_method']}")
            else:
                self.log_error(f"Failed to create payment of R$ {payment_data['amount']}")
                
        if not created_payments:
            self.log_error("No payments created - cannot continue payment tests")
            return False
            
        self.test_data['payments'] = created_payments
        
        # READ all payments
        result = self.make_request("GET", "/payments")
        if result and isinstance(result, list) and len(result) >= len(created_payments):
            self.log_success(f"Retrieved {len(result)} payments")
        else:
            self.log_error("Failed to retrieve payments list")
        
        return True
    
    def test_dashboard_statistics(self):
        """Test Dashboard statistics API"""
        print("\n🔍 Testing Dashboard Statistics API...")
        
        result = self.make_request("GET", "/dashboard/stats")
        if not result:
            self.log_error("Failed to retrieve dashboard statistics")
            return False
            
        # Check required fields
        required_fields = [
            'total_customers', 'total_packages', 'total_appointments',
            'active_customer_packages', 'today_appointments', 'recent_payments'
        ]
        
        missing_fields = [field for field in required_fields if field not in result]
        if missing_fields:
            self.log_error(f"Dashboard stats missing fields: {missing_fields}")
            return False
            
        # Validate data types and values
        stats = result
        if not isinstance(stats['total_customers'], int) or stats['total_customers'] < 0:
            self.log_error(f"Invalid total_customers: {stats['total_customers']}")
        else:
            self.log_success(f"Total customers: {stats['total_customers']}")
            
        if not isinstance(stats['total_packages'], int) or stats['total_packages'] < 0:
            self.log_error(f"Invalid total_packages: {stats['total_packages']}")
        else:
            self.log_success(f"Total packages: {stats['total_packages']}")
            
        if not isinstance(stats['total_appointments'], int) or stats['total_appointments'] < 0:
            self.log_error(f"Invalid total_appointments: {stats['total_appointments']}")
        else:
            self.log_success(f"Total appointments: {stats['total_appointments']}")
            
        if not isinstance(stats['active_customer_packages'], int) or stats['active_customer_packages'] < 0:
            self.log_error(f"Invalid active_customer_packages: {stats['active_customer_packages']}")
        else:
            self.log_success(f"Active customer packages: {stats['active_customer_packages']}")
            
        if not isinstance(stats['today_appointments'], int) or stats['today_appointments'] < 0:
            self.log_error(f"Invalid today_appointments: {stats['today_appointments']}")
        else:
            self.log_success(f"Today's appointments: {stats['today_appointments']}")
            
        if not isinstance(stats['recent_payments'], list):
            self.log_error(f"Invalid recent_payments type: {type(stats['recent_payments'])}")
        else:
            self.log_success(f"Recent payments: {len(stats['recent_payments'])} entries")
        
        return True
    
    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Comprehensive Backend API Testing...")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Test API connectivity first
        if not self.test_api_root():
            print("\n❌ API not accessible - stopping tests")
            return False
            
        # Run all tests in sequence
        test_methods = [
            self.test_customer_management,
            self.test_package_management,
            self.test_customer_package_relationships,
            self.test_appointment_scheduling,
            self.test_payment_control,
            self.test_dashboard_statistics
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_error(f"Test {test_method.__name__} failed with exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Successful operations: {len(self.successes)}")
        print(f"❌ Failed operations: {len(self.errors)}")
        
        if self.errors:
            print("\n🔍 ERRORS FOUND:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.successes:
            print(f"\n✅ SUCCESSFUL OPERATIONS: {len(self.successes)}")
            
        success_rate = len(self.successes) / (len(self.successes) + len(self.errors)) * 100 if (self.successes or self.errors) else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        return len(self.errors) == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)