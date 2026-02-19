import requests
import sys
import json
from datetime import datetime
import uuid
import base64
import io

class FleetMaintenanceAPITester:
    def __init__(self, base_url="https://farm-fleet-pro.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.test_user_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestPass123!"
        self.test_user_name = "Test User"
        self.category_id = None
        self.machine_id = None
        self.maintenance_id = None
        self.stock_item_id = None
        self.stock_category_id = None

    def log_result(self, test_name, success, details="", error_msg=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED: {error_msg}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "error": error_msg
        })

    def make_request(self, method, endpoint, data=None, files=None):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if files:
            # Remove Content-Type for file uploads
            headers.pop('Content-Type', None)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            return response
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None

    def test_user_registration(self):
        """Test user registration"""
        data = {
            "name": self.test_user_name,
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        response = self.make_request("POST", "auth/register", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'token' in response_data and 'user' in response_data:
                self.token = response_data['token']
                self.user_id = response_data['user']['id']
                self.log_result("User Registration", True, f"User ID: {self.user_id}")
                return True
            else:
                self.log_result("User Registration", False, "", "Missing token or user in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("User Registration", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_user_login(self):
        """Test user login"""
        data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        response = self.make_request("POST", "auth/login", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'token' in response_data:
                self.token = response_data['token']
                self.log_result("User Login", True, f"Token received")
                return True
            else:
                self.log_result("User Login", False, "", "Missing token in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("User Login", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_auth_verification(self):
        """Test auth token verification"""
        response = self.make_request("GET", "auth/me")
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data and response_data['email'] == self.test_user_email:
                self.log_result("Auth Token Verification", True, f"User verified: {response_data['name']}")
                return True
            else:
                self.log_result("Auth Token Verification", False, "", "User data mismatch")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Auth Token Verification", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_create_category(self):
        """Test category creation"""
        data = {
            "name": "Trator de Teste",
            "description": "Categoria criada para testes automatizados"
        }
        
        response = self.make_request("POST", "categories", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data:
                self.category_id = response_data['id']
                self.log_result("Create Category", True, f"Category ID: {self.category_id}")
                return True
            else:
                self.log_result("Create Category", False, "", "Missing ID in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Create Category", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_list_categories(self):
        """Test listing categories"""
        response = self.make_request("GET", "categories")
        
        if response and response.status_code == 200:
            categories = response.json()
            if isinstance(categories, list) and len(categories) > 0:
                found_test_category = any(cat['id'] == self.category_id for cat in categories)
                if found_test_category:
                    self.log_result("List Categories", True, f"Found {len(categories)} categories")
                    return True
                else:
                    self.log_result("List Categories", False, "", "Test category not found in list")
            else:
                self.log_result("List Categories", False, "", "Empty or invalid categories list")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("List Categories", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_create_machine(self):
        """Test machine creation"""
        if not self.category_id:
            self.log_result("Create Machine", False, "", "No category ID available")
            return False
        
        data = {
            "name": "Trator John Deere Teste",
            "plate": f"TST{uuid.uuid4().hex[:4].upper()}",
            "category_id": self.category_id,
            "brand": "John Deere",
            "model": "6175J",
            "year": 2020,
            "notes": "Máquina criada para testes automatizados"
        }
        
        response = self.make_request("POST", "machines", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data:
                self.machine_id = response_data['id']
                self.log_result("Create Machine", True, f"Machine ID: {self.machine_id}, Plate: {data['plate']}")
                return True
            else:
                self.log_result("Create Machine", False, "", "Missing ID in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Create Machine", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_list_machines(self):
        """Test listing machines"""
        response = self.make_request("GET", "machines")
        
        if response and response.status_code == 200:
            machines = response.json()
            if isinstance(machines, list) and len(machines) > 0:
                found_test_machine = any(m['id'] == self.machine_id for m in machines)
                if found_test_machine:
                    self.log_result("List Machines", True, f"Found {len(machines)} machines")
                    return True
                else:
                    self.log_result("List Machines", False, "", "Test machine not found in list")
            else:
                self.log_result("List Machines", False, "", "Empty or invalid machines list")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("List Machines", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_get_machine_details(self):
        """Test getting machine details"""
        if not self.machine_id:
            self.log_result("Get Machine Details", False, "", "No machine ID available")
            return False
        
        response = self.make_request("GET", f"machines/{self.machine_id}")
        
        if response and response.status_code == 200:
            machine = response.json()
            if 'id' in machine and machine['id'] == self.machine_id:
                self.log_result("Get Machine Details", True, f"Machine: {machine['name']}")
                return True
            else:
                self.log_result("Get Machine Details", False, "", "Machine data mismatch")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Get Machine Details", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_create_maintenance(self):
        """Test maintenance creation"""
        if not self.machine_id:
            self.log_result("Create Maintenance", False, "", "No machine ID available")
            return False
        
        data = {
            "machine_id": self.machine_id,
            "part_name": "Filtro de óleo teste",
            "replacement_date": "2024-01-15",
            "part_value": 150.50,
            "maintenance_type": "preventiva",
            "description": "Manutenção criada para testes automatizados",
            "is_oil_change": False
        }
        
        response = self.make_request("POST", "maintenances", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data:
                self.maintenance_id = response_data['id']
                self.log_result("Create Maintenance", True, f"Maintenance ID: {self.maintenance_id}")
                return True
            else:
                self.log_result("Create Maintenance", False, "", "Missing ID in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Create Maintenance", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_create_oil_change_maintenance(self):
        """Test oil change maintenance creation"""
        if not self.machine_id:
            self.log_result("Create Oil Change Maintenance", False, "", "No machine ID available")
            return False
        
        data = {
            "machine_id": self.machine_id,
            "part_name": "Troca de óleo completa",
            "replacement_date": "2024-01-20",
            "part_value": 250.00,
            "maintenance_type": "preventiva",
            "description": "Troca de óleo para teste automatizado",
            "is_oil_change": True
        }
        
        response = self.make_request("POST", "maintenances", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data and response_data.get('is_oil_change') == True:
                self.log_result("Create Oil Change Maintenance", True, f"Oil Change Maintenance ID: {response_data['id']}")
                return True
            else:
                self.log_result("Create Oil Change Maintenance", False, "", "Missing ID or is_oil_change not set correctly")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Create Oil Change Maintenance", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_list_maintenances(self):
        """Test listing maintenances"""
        response = self.make_request("GET", "maintenances")
        
        if response and response.status_code == 200:
            maintenances = response.json()
            if isinstance(maintenances, list) and len(maintenances) > 0:
                found_test_maintenance = any(m['id'] == self.maintenance_id for m in maintenances)
                if found_test_maintenance:
                    self.log_result("List Maintenances", True, f"Found {len(maintenances)} maintenances")
                    return True
                else:
                    self.log_result("List Maintenances", False, "", "Test maintenance not found in list")
            else:
                self.log_result("List Maintenances", False, "", "Empty or invalid maintenances list")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("List Maintenances", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_filter_maintenances_by_machine(self):
        """Test filtering maintenances by machine"""
        if not self.machine_id:
            self.log_result("Filter Maintenances by Machine", False, "", "No machine ID available")
            return False
        
        response = self.make_request("GET", f"maintenances?machine_id={self.machine_id}")
        
        if response and response.status_code == 200:
            maintenances = response.json()
            if isinstance(maintenances, list):
                # All maintenances should belong to the specified machine
                all_match = all(m['machine_id'] == self.machine_id for m in maintenances)
                if all_match:
                    self.log_result("Filter Maintenances by Machine", True, f"Found {len(maintenances)} maintenances for machine")
                    return True
                else:
                    self.log_result("Filter Maintenances by Machine", False, "", "Some maintenances don't match machine filter")
            else:
                self.log_result("Filter Maintenances by Machine", False, "", "Invalid maintenances list")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Filter Maintenances by Machine", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_upload_photo(self):
        """Test photo upload to maintenance"""
        if not self.maintenance_id:
            self.log_result("Upload Photo", False, "", "No maintenance ID available")
            return False
        
        # Create a simple test image (1x1 pixel PNG)
        test_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="
        )
        
        files = {
            'file': ('test.png', io.BytesIO(test_image_data), 'image/png')
        }
        
        response = self.make_request("POST", f"maintenances/{self.maintenance_id}/photos", files=files)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'message' in response_data and 'photo' in response_data:
                self.log_result("Upload Photo", True, "Photo uploaded successfully")
                return True
            else:
                self.log_result("Upload Photo", False, "", "Missing message or photo in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Upload Photo", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_get_maintenance_details(self):
        """Test getting maintenance details"""
        if not self.maintenance_id:
            self.log_result("Get Maintenance Details", False, "", "No maintenance ID available")
            return False
        
        response = self.make_request("GET", f"maintenances/{self.maintenance_id}")
        
        if response and response.status_code == 200:
            maintenance = response.json()
            if 'id' in maintenance and maintenance['id'] == self.maintenance_id:
                # Check if photo was uploaded
                has_photos = 'photos' in maintenance and len(maintenance['photos']) > 0
                self.log_result("Get Maintenance Details", True, f"Maintenance: {maintenance['part_name']}, Photos: {len(maintenance.get('photos', []))}")
                return True
            else:
                self.log_result("Get Maintenance Details", False, "", "Maintenance data mismatch")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Get Maintenance Details", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        response = self.make_request("GET", "dashboard")
        
        if response and response.status_code == 200:
            stats = response.json()
            required_fields = ['total_machines', 'total_maintenances', 'preventive_count', 'corrective_count', 'total_spent', 'recent_maintenances', 'low_stock_count']
            
            if all(field in stats for field in required_fields):
                self.log_result("Dashboard Stats", True, f"Machines: {stats['total_machines']}, Maintenances: {stats['total_maintenances']}, Low Stock: {stats['low_stock_count']}")
                return True
            else:
                missing_fields = [field for field in required_fields if field not in stats]
                self.log_result("Dashboard Stats", False, "", f"Missing fields: {missing_fields}")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Dashboard Stats", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_update_machine(self):
        """Test machine update"""
        if not self.machine_id:
            self.log_result("Update Machine", False, "", "No machine ID available")
            return False
        
        data = {
            "name": "Trator John Deere Teste Atualizado",
            "plate": f"UPD{uuid.uuid4().hex[:4].upper()}",
            "category_id": self.category_id,
            "brand": "John Deere",
            "model": "6175J Updated",
            "year": 2021,
            "notes": "Máquina atualizada para testes automatizados"
        }
        
        response = self.make_request("PUT", f"machines/{self.machine_id}", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data and response_data['name'] == data['name']:
                self.log_result("Update Machine", True, f"Machine updated: {response_data['name']}")
                return True
            else:
                self.log_result("Update Machine", False, "", "Machine data not updated correctly")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Update Machine", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_create_stock_item(self):
        """Test stock item creation"""
        data = {
            "name": "Filtro de Óleo Teste",
            "code": "FO-TEST-001",
            "category": "Filtro",
            "unit": "un",
            "quantity": 10,
            "min_quantity": 5,
            "unit_price": 25.50,
            "location": "Prateleira A1",
            "notes": "Item criado para testes automatizados"
        }
        
        response = self.make_request("POST", "stock/items", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data:
                self.stock_item_id = response_data['id']
                self.log_result("Create Stock Item", True, f"Stock Item ID: {self.stock_item_id}")
                return True
            else:
                self.log_result("Create Stock Item", False, "", "Missing ID in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Create Stock Item", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_list_stock_items(self):
        """Test listing stock items"""
        response = self.make_request("GET", "stock/items")
        
        if response and response.status_code == 200:
            items = response.json()
            if isinstance(items, list) and len(items) > 0:
                found_test_item = any(item['id'] == self.stock_item_id for item in items)
                if found_test_item:
                    self.log_result("List Stock Items", True, f"Found {len(items)} stock items")
                    return True
                else:
                    self.log_result("List Stock Items", False, "", "Test stock item not found in list")
            else:
                self.log_result("List Stock Items", False, "", "Empty or invalid stock items list")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("List Stock Items", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_get_stock_item_details(self):
        """Test getting stock item details"""
        if not self.stock_item_id:
            self.log_result("Get Stock Item Details", False, "", "No stock item ID available")
            return False
        
        response = self.make_request("GET", f"stock/items/{self.stock_item_id}")
        
        if response and response.status_code == 200:
            item = response.json()
            if 'id' in item and item['id'] == self.stock_item_id:
                self.log_result("Get Stock Item Details", True, f"Item: {item['name']}, Quantity: {item['quantity']}")
                return True
            else:
                self.log_result("Get Stock Item Details", False, "", "Stock item data mismatch")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Get Stock Item Details", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_update_stock_item(self):
        """Test stock item update"""
        if not self.stock_item_id:
            self.log_result("Update Stock Item", False, "", "No stock item ID available")
            return False
        
        data = {
            "name": "Filtro de Óleo Teste Atualizado",
            "code": "FO-TEST-001-UPD",
            "category": "Filtro",
            "unit": "un",
            "min_quantity": 8,
            "unit_price": 30.00,
            "location": "Prateleira B2",
            "notes": "Item atualizado para testes automatizados"
        }
        
        response = self.make_request("PUT", f"stock/items/{self.stock_item_id}", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data and response_data['name'] == data['name']:
                self.log_result("Update Stock Item", True, f"Stock item updated: {response_data['name']}")
                return True
            else:
                self.log_result("Update Stock Item", False, "", "Stock item data not updated correctly")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Update Stock Item", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_create_stock_movement_entry(self):
        """Test stock movement creation (entry)"""
        if not self.stock_item_id:
            self.log_result("Create Stock Movement Entry", False, "", "No stock item ID available")
            return False
        
        data = {
            "item_id": self.stock_item_id,
            "movement_type": "entrada",
            "quantity": 5,
            "reason": "Compra",
            "notes": "Entrada de teste automatizado"
        }
        
        response = self.make_request("POST", "stock/movements", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data and response_data['movement_type'] == "entrada":
                self.log_result("Create Stock Movement Entry", True, f"Entry movement created: +{response_data['quantity']}")
                return True
            else:
                self.log_result("Create Stock Movement Entry", False, "", "Missing ID or incorrect movement type in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Create Stock Movement Entry", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_create_stock_movement_exit(self):
        """Test stock movement creation (exit)"""
        if not self.stock_item_id:
            self.log_result("Create Stock Movement Exit", False, "", "No stock item ID available")
            return False
        
        data = {
            "item_id": self.stock_item_id,
            "movement_type": "saida",
            "quantity": 3,
            "reason": "Uso em manutenção",
            "notes": "Saída de teste automatizado"
        }
        
        response = self.make_request("POST", "stock/movements", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data and response_data['movement_type'] == "saida":
                self.log_result("Create Stock Movement Exit", True, f"Exit movement created: -{response_data['quantity']}")
                return True
            else:
                self.log_result("Create Stock Movement Exit", False, "", "Missing ID or incorrect movement type in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Create Stock Movement Exit", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_list_stock_movements(self):
        """Test listing stock movements"""
        response = self.make_request("GET", "stock/movements")
        
        if response and response.status_code == 200:
            movements = response.json()
            if isinstance(movements, list) and len(movements) > 0:
                # Check if we have both entry and exit movements for our test item
                test_movements = [m for m in movements if m['item_id'] == self.stock_item_id]
                if len(test_movements) >= 2:  # Should have at least entry and exit
                    self.log_result("List Stock Movements", True, f"Found {len(movements)} total movements, {len(test_movements)} for test item")
                    return True
                else:
                    self.log_result("List Stock Movements", False, "", f"Expected at least 2 movements for test item, found {len(test_movements)}")
            else:
                self.log_result("List Stock Movements", False, "", "Empty or invalid stock movements list")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("List Stock Movements", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_filter_low_stock_items(self):
        """Test filtering low stock items"""
        # First, create a low stock item by reducing quantity below minimum
        if self.stock_item_id:
            # Create multiple exit movements to bring stock below minimum
            for i in range(3):
                data = {
                    "item_id": self.stock_item_id,
                    "movement_type": "saida",
                    "quantity": 2,
                    "reason": "Teste estoque baixo",
                    "notes": f"Redução {i+1} para teste de estoque baixo"
                }
                self.make_request("POST", "stock/movements", data)
        
        response = self.make_request("GET", "stock/items?low_stock_only=true")
        
        if response and response.status_code == 200:
            low_stock_items = response.json()
            if isinstance(low_stock_items, list):
                # Check if all returned items are actually low stock
                all_low_stock = all(item['is_low_stock'] for item in low_stock_items)
                if all_low_stock:
                    self.log_result("Filter Low Stock Items", True, f"Found {len(low_stock_items)} low stock items")
                    return True
                else:
                    self.log_result("Filter Low Stock Items", False, "", "Some items in low stock filter are not actually low stock")
            else:
                self.log_result("Filter Low Stock Items", False, "", "Invalid low stock items list")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Filter Low Stock Items", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False
    def test_create_usage_log(self):
        """Test usage log creation"""
        if not self.machine_id:
            self.log_result("Create Usage Log", False, "", "No machine ID available")
            return False
        
        data = {
            "machine_id": self.machine_id,
            "hours": 8.5,
            "notes": "Teste de registro de horas de uso"
        }
        
        response = self.make_request("POST", "usage-logs", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data and response_data.get('hours') == 8.5:
                self.log_result("Create Usage Log", True, f"Usage Log ID: {response_data['id']}, Hours: {response_data['hours']}")
                return True
            else:
                self.log_result("Create Usage Log", False, "", "Missing ID or incorrect hours in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Create Usage Log", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_list_usage_logs(self):
        """Test listing usage logs"""
        response = self.make_request("GET", "usage-logs")
        
        if response and response.status_code == 200:
            logs = response.json()
            if isinstance(logs, list) and len(logs) > 0:
                # Check if we have logs for our test machine
                test_logs = [log for log in logs if log['machine_id'] == self.machine_id]
                if len(test_logs) > 0:
                    self.log_result("List Usage Logs", True, f"Found {len(logs)} total logs, {len(test_logs)} for test machine")
                    return True
                else:
                    self.log_result("List Usage Logs", False, "", "No usage logs found for test machine")
            else:
                self.log_result("List Usage Logs", False, "", "Empty or invalid usage logs list")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("List Usage Logs", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_get_oil_change_status(self):
        """Test oil change status endpoint"""
        response = self.make_request("GET", "oil-change-status")
        
        if response and response.status_code == 200:
            status_list = response.json()
            if isinstance(status_list, list) and len(status_list) > 0:
                # Check if we have status for our test machine
                test_status = [status for status in status_list if status['machine_id'] == self.machine_id]
                if len(test_status) > 0:
                    status = test_status[0]
                    required_fields = ['machine_id', 'machine_name', 'machine_plate', 'hours_since_change', 'hours_remaining', 'days_since_change', 'days_remaining', 'needs_alert']
                    if all(field in status for field in required_fields):
                        self.log_result("Get Oil Change Status", True, f"Status for machine: Hours since change: {status['hours_since_change']}, Needs alert: {status['needs_alert']}")
                        return True
                    else:
                        missing_fields = [field for field in required_fields if field not in status]
                        self.log_result("Get Oil Change Status", False, "", f"Missing fields in status: {missing_fields}")
                else:
                    self.log_result("Get Oil Change Status", False, "", "No oil change status found for test machine")
            else:
                self.log_result("Get Oil Change Status", False, "", "Empty or invalid oil change status list")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Get Oil Change Status", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_get_notifications(self):
        """Test notifications endpoint"""
        response = self.make_request("GET", "notifications")
        
        if response and response.status_code == 200:
            notifications = response.json()
            if isinstance(notifications, list):
                # Notifications might be empty, which is fine
                self.log_result("Get Notifications", True, f"Found {len(notifications)} notifications")
                return True
            else:
                self.log_result("Get Notifications", False, "", "Invalid notifications response format")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Get Notifications", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_create_stock_category(self):
        """Test stock category creation"""
        data = {
            "name": "Categoria Teste"
        }
        
        response = self.make_request("POST", "stock/categories", data)
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'id' in response_data and response_data.get('name') == data['name']:
                self.stock_category_id = response_data['id']
                self.log_result("Create Stock Category", True, f"Stock Category ID: {self.stock_category_id}")
                return True
            else:
                self.log_result("Create Stock Category", False, "", "Missing ID or incorrect name in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Create Stock Category", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_list_stock_categories(self):
        """Test listing stock categories"""
        response = self.make_request("GET", "stock/categories")
        
        if response and response.status_code == 200:
            categories = response.json()
            if isinstance(categories, list) and len(categories) > 0:
                found_test_category = any(cat['id'] == getattr(self, 'stock_category_id', None) for cat in categories)
                if found_test_category:
                    self.log_result("List Stock Categories", True, f"Found {len(categories)} stock categories")
                    return True
                else:
                    self.log_result("List Stock Categories", False, "", "Test stock category not found in list")
            else:
                self.log_result("List Stock Categories", False, "", "Empty or invalid stock categories list")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("List Stock Categories", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def test_delete_stock_category(self):
        """Test stock category deletion"""
        if not hasattr(self, 'stock_category_id') or not self.stock_category_id:
            self.log_result("Delete Stock Category", False, "", "No stock category ID available")
            return False
        
        response = self.make_request("DELETE", f"stock/categories/{self.stock_category_id}")
        
        if response and response.status_code == 200:
            response_data = response.json()
            if 'message' in response_data:
                self.log_result("Delete Stock Category", True, "Stock category deleted successfully")
                return True
            else:
                self.log_result("Delete Stock Category", False, "", "Missing message in response")
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else "No response"
            self.log_result("Delete Stock Category", False, "", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        
        return False

    def cleanup_test_data(self):
        """Clean up test data"""
        cleanup_results = []
        
        # Delete maintenance
        if self.maintenance_id:
            response = self.make_request("DELETE", f"maintenances/{self.maintenance_id}")
            cleanup_results.append(f"Maintenance: {response.status_code if response else 'Failed'}")
        
        # Delete stock item (this will also delete related movements)
        if self.stock_item_id:
            response = self.make_request("DELETE", f"stock/items/{self.stock_item_id}")
            cleanup_results.append(f"Stock Item: {response.status_code if response else 'Failed'}")
        
        # Delete machine
        if self.machine_id:
            response = self.make_request("DELETE", f"machines/{self.machine_id}")
            cleanup_results.append(f"Machine: {response.status_code if response else 'Failed'}")
        
        # Delete category
        if self.category_id:
            response = self.make_request("DELETE", f"categories/{self.category_id}")
            cleanup_results.append(f"Category: {response.status_code if response else 'Failed'}")
        
        print(f"\n🧹 Cleanup completed: {', '.join(cleanup_results)}")

    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting Fleet Maintenance API Tests")
        print(f"📍 Base URL: {self.base_url}")
        print(f"👤 Test User: {self.test_user_email}")
        print("=" * 60)
        
        # Authentication Tests
        print("\n📋 AUTHENTICATION TESTS")
        if not self.test_user_registration():
            print("❌ Registration failed - stopping tests")
            return False
        
        if not self.test_user_login():
            print("❌ Login failed - stopping tests")
            return False
        
        if not self.test_auth_verification():
            print("❌ Auth verification failed - stopping tests")
            return False
        
        # Category Tests
        print("\n📋 CATEGORY TESTS")
        self.test_create_category()
        self.test_list_categories()
        
        # Machine Tests
        print("\n📋 MACHINE TESTS")
        self.test_create_machine()
        self.test_list_machines()
        self.test_get_machine_details()
        self.test_update_machine()
        
        # Maintenance Tests
        print("\n📋 MAINTENANCE TESTS")
        self.test_create_maintenance()
        self.test_create_oil_change_maintenance()
        self.test_list_maintenances()
        self.test_filter_maintenances_by_machine()
        self.test_get_maintenance_details()
        self.test_upload_photo()
        
        # Oil Change / Usage Tests
        print("\n📋 OIL CHANGE & USAGE TESTS")
        self.test_create_usage_log()
        self.test_list_usage_logs()
        self.test_get_oil_change_status()
        self.test_get_notifications()
        
        # Dashboard Tests
        print("\n📋 DASHBOARD TESTS")
        self.test_dashboard_stats()
        
        # Stock Tests
        print("\n📋 STOCK TESTS")
        self.test_create_stock_category()
        self.test_list_stock_categories()
        self.test_create_stock_item()
        self.test_list_stock_items()
        self.test_get_stock_item_details()
        self.test_update_stock_item()
        self.test_create_stock_movement_entry()
        self.test_create_stock_movement_exit()
        self.test_list_stock_movements()
        self.test_filter_low_stock_items()
        self.test_delete_stock_category()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Results
        print("\n" + "=" * 60)
        print(f"📊 TEST RESULTS: {self.tests_passed}/{self.tests_run} PASSED")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} TESTS FAILED")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['error']}")
            return False

def main():
    """Main test function"""
    tester = FleetMaintenanceAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())