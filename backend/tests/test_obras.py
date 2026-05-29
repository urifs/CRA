"""
Test suite for Obras (Projects) feature - CRUD operations and machine linking
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cra-finance-ops.preview.emergentagent.com')

class TestObrasFeature:
    """Test Obras (Projects) CRUD and machine linking functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            # Try to register if login fails
            register_response = self.session.post(f"{BASE_URL}/api/auth/register", json={
                "name": "Test User",
                "email": "test@test.com",
                "password": "password"
            })
            if register_response.status_code == 200:
                token = register_response.json().get("token")
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.token = token
            else:
                pytest.skip("Authentication failed - skipping tests")
        
        yield
        
        # Cleanup: Delete test obras
        try:
            obras_response = self.session.get(f"{BASE_URL}/api/obras")
            if obras_response.status_code == 200:
                for obra in obras_response.json():
                    if obra["name"].startswith("TEST_"):
                        self.session.delete(f"{BASE_URL}/api/obras/{obra['id']}")
        except:
            pass
    
    # ============ OBRAS CRUD TESTS ============
    
    def test_create_obra(self):
        """Test creating a new obra"""
        payload = {
            "name": "TEST_Obra Nova",
            "description": "Descrição da obra de teste",
            "location": "Rodovia BR-101, Km 50",
            "start_date": "2024-01-15",
            "end_date": "2024-12-31",
            "status": "em_andamento"
        }
        
        response = self.session.post(f"{BASE_URL}/api/obras", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert data["location"] == payload["location"]
        assert data["status"] == payload["status"]
        assert "id" in data
        assert data["machine_count"] == 0
        assert data["total_maintenance_cost"] == 0
        print(f"✓ Created obra: {data['id']}")
    
    def test_list_obras(self):
        """Test listing all obras"""
        response = self.session.get(f"{BASE_URL}/api/obras")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} obras")
    
    def test_get_obra_detail(self):
        """Test getting obra details"""
        # First create an obra
        create_response = self.session.post(f"{BASE_URL}/api/obras", json={
            "name": "TEST_Obra Detail",
            "description": "Test description",
            "location": "Test location",
            "status": "em_andamento"
        })
        assert create_response.status_code == 200
        obra_id = create_response.json()["id"]
        
        # Get obra details
        response = self.session.get(f"{BASE_URL}/api/obras/{obra_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["id"] == obra_id
        assert data["name"] == "TEST_Obra Detail"
        assert "machines" in data
        assert "maintenances" in data
        assert "total_maintenance_cost" in data
        assert "preventive_cost" in data
        assert "corrective_cost" in data
        print(f"✓ Got obra detail: {obra_id}")
    
    def test_update_obra(self):
        """Test updating an obra"""
        # First create an obra
        create_response = self.session.post(f"{BASE_URL}/api/obras", json={
            "name": "TEST_Obra Update",
            "description": "Original description",
            "location": "Original location",
            "status": "em_andamento"
        })
        assert create_response.status_code == 200
        obra_id = create_response.json()["id"]
        
        # Update the obra
        update_payload = {
            "name": "TEST_Obra Updated",
            "description": "Updated description",
            "location": "Updated location",
            "status": "pausada"
        }
        
        response = self.session.put(f"{BASE_URL}/api/obras/{obra_id}", json=update_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["name"] == update_payload["name"]
        assert data["description"] == update_payload["description"]
        assert data["location"] == update_payload["location"]
        assert data["status"] == update_payload["status"]
        print(f"✓ Updated obra: {obra_id}")
    
    def test_delete_obra(self):
        """Test deleting an obra"""
        # First create an obra
        create_response = self.session.post(f"{BASE_URL}/api/obras", json={
            "name": "TEST_Obra Delete",
            "description": "To be deleted",
            "status": "em_andamento"
        })
        assert create_response.status_code == 200
        obra_id = create_response.json()["id"]
        
        # Delete the obra
        response = self.session.delete(f"{BASE_URL}/api/obras/{obra_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify it's deleted
        get_response = self.session.get(f"{BASE_URL}/api/obras/{obra_id}")
        assert get_response.status_code == 404
        print(f"✓ Deleted obra: {obra_id}")
    
    def test_get_nonexistent_obra(self):
        """Test getting a non-existent obra returns 404"""
        response = self.session.get(f"{BASE_URL}/api/obras/nonexistent-id-12345")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent obra returns 404")
    
    # ============ MACHINE LINKING TESTS ============
    
    def test_link_machine_to_obra(self):
        """Test linking a machine to an obra via PATCH"""
        # Create an obra
        obra_response = self.session.post(f"{BASE_URL}/api/obras", json={
            "name": "TEST_Obra Link Machine",
            "status": "em_andamento"
        })
        assert obra_response.status_code == 200
        obra_id = obra_response.json()["id"]
        
        # Create a category first
        cat_response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Category Link",
            "description": "Test category"
        })
        assert cat_response.status_code == 200
        category_id = cat_response.json()["id"]
        
        # Create a machine
        machine_response = self.session.post(f"{BASE_URL}/api/machines", json={
            "name": "TEST_Machine Link",
            "plate": "TEST-LINK-001",
            "category_id": category_id
        })
        assert machine_response.status_code == 200
        machine_id = machine_response.json()["id"]
        
        # Link machine to obra via PATCH
        response = self.session.patch(f"{BASE_URL}/api/machines/{machine_id}/obra", json={
            "obra_id": obra_id
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["obra_id"] == obra_id
        print(f"✓ Linked machine {machine_id} to obra {obra_id}")
        
        # Verify obra now has the machine
        obra_detail = self.session.get(f"{BASE_URL}/api/obras/{obra_id}")
        assert obra_detail.status_code == 200
        obra_data = obra_detail.json()
        machine_ids = [m["id"] for m in obra_data["machines"]]
        assert machine_id in machine_ids
        print(f"✓ Verified machine appears in obra detail")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/machines/{machine_id}")
        self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
    
    def test_unlink_machine_from_obra(self):
        """Test removing a machine from an obra (set obra_id to null)"""
        # Create an obra
        obra_response = self.session.post(f"{BASE_URL}/api/obras", json={
            "name": "TEST_Obra Unlink",
            "status": "em_andamento"
        })
        assert obra_response.status_code == 200
        obra_id = obra_response.json()["id"]
        
        # Create a category
        cat_response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Category Unlink",
            "description": "Test category"
        })
        assert cat_response.status_code == 200
        category_id = cat_response.json()["id"]
        
        # Create a machine linked to obra
        machine_response = self.session.post(f"{BASE_URL}/api/machines", json={
            "name": "TEST_Machine Unlink",
            "plate": "TEST-UNLINK-001",
            "category_id": category_id,
            "obra_id": obra_id
        })
        assert machine_response.status_code == 200
        machine_id = machine_response.json()["id"]
        
        # Unlink machine from obra
        response = self.session.patch(f"{BASE_URL}/api/machines/{machine_id}/obra", json={
            "obra_id": None
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["obra_id"] is None
        print(f"✓ Unlinked machine {machine_id} from obra")
        
        # Verify obra no longer has the machine
        obra_detail = self.session.get(f"{BASE_URL}/api/obras/{obra_id}")
        assert obra_detail.status_code == 200
        obra_data = obra_detail.json()
        machine_ids = [m["id"] for m in obra_data["machines"]]
        assert machine_id not in machine_ids
        print(f"✓ Verified machine removed from obra detail")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/machines/{machine_id}")
        self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
    
    def test_create_machine_with_obra(self):
        """Test creating a machine directly linked to an obra"""
        # Create an obra
        obra_response = self.session.post(f"{BASE_URL}/api/obras", json={
            "name": "TEST_Obra Create Machine",
            "status": "em_andamento"
        })
        assert obra_response.status_code == 200
        obra_id = obra_response.json()["id"]
        
        # Create a category
        cat_response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Category Create",
            "description": "Test category"
        })
        assert cat_response.status_code == 200
        category_id = cat_response.json()["id"]
        
        # Create a machine with obra_id
        response = self.session.post(f"{BASE_URL}/api/machines", json={
            "name": "TEST_Machine With Obra",
            "plate": "TEST-OBRA-001",
            "category_id": category_id,
            "obra_id": obra_id
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["obra_id"] == obra_id
        machine_id = data["id"]
        print(f"✓ Created machine with obra_id: {machine_id}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/machines/{machine_id}")
        self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
    
    # ============ MAINTENANCE COST CALCULATION TESTS ============
    
    def test_obra_maintenance_cost_calculation(self):
        """Test that maintenance costs are correctly calculated for obra"""
        # Create an obra
        obra_response = self.session.post(f"{BASE_URL}/api/obras", json={
            "name": "TEST_Obra Costs",
            "status": "em_andamento"
        })
        assert obra_response.status_code == 200
        obra_id = obra_response.json()["id"]
        
        # Create a category
        cat_response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Category Costs",
            "description": "Test category"
        })
        assert cat_response.status_code == 200
        category_id = cat_response.json()["id"]
        
        # Create a machine linked to obra
        machine_response = self.session.post(f"{BASE_URL}/api/machines", json={
            "name": "TEST_Machine Costs",
            "plate": "TEST-COSTS-001",
            "category_id": category_id,
            "obra_id": obra_id
        })
        assert machine_response.status_code == 200
        machine_id = machine_response.json()["id"]
        
        # Create maintenances for the machine
        maintenance1 = self.session.post(f"{BASE_URL}/api/maintenances", json={
            "machine_id": machine_id,
            "part_name": "TEST_Filtro de Óleo",
            "replacement_date": "2024-01-15",
            "part_value": 100.00,
            "maintenance_type": "preventiva",
            "description": "Troca preventiva"
        })
        assert maintenance1.status_code == 200
        maint1_id = maintenance1.json()["id"]
        
        maintenance2 = self.session.post(f"{BASE_URL}/api/maintenances", json={
            "machine_id": machine_id,
            "part_name": "TEST_Correia",
            "replacement_date": "2024-01-20",
            "part_value": 250.00,
            "maintenance_type": "corretiva",
            "description": "Troca corretiva"
        })
        assert maintenance2.status_code == 200
        maint2_id = maintenance2.json()["id"]
        
        # Get obra detail and verify costs
        obra_detail = self.session.get(f"{BASE_URL}/api/obras/{obra_id}")
        assert obra_detail.status_code == 200
        
        data = obra_detail.json()
        assert data["total_maintenance_cost"] == 350.00, f"Expected 350.00, got {data['total_maintenance_cost']}"
        assert data["preventive_cost"] == 100.00, f"Expected 100.00, got {data['preventive_cost']}"
        assert data["corrective_cost"] == 250.00, f"Expected 250.00, got {data['corrective_cost']}"
        assert len(data["maintenances"]) == 2
        print(f"✓ Obra costs calculated correctly: Total={data['total_maintenance_cost']}, Preventive={data['preventive_cost']}, Corrective={data['corrective_cost']}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/maintenances/{maint1_id}")
        self.session.delete(f"{BASE_URL}/api/maintenances/{maint2_id}")
        self.session.delete(f"{BASE_URL}/api/machines/{machine_id}")
        self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
    
    def test_obra_list_shows_machine_count_and_costs(self):
        """Test that obra list shows correct machine count and total costs"""
        # Create an obra
        obra_response = self.session.post(f"{BASE_URL}/api/obras", json={
            "name": "TEST_Obra List Stats",
            "status": "em_andamento"
        })
        assert obra_response.status_code == 200
        obra_id = obra_response.json()["id"]
        
        # Create a category
        cat_response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Category Stats",
            "description": "Test category"
        })
        assert cat_response.status_code == 200
        category_id = cat_response.json()["id"]
        
        # Create 2 machines linked to obra
        machine1 = self.session.post(f"{BASE_URL}/api/machines", json={
            "name": "TEST_Machine Stats 1",
            "plate": "TEST-STATS-001",
            "category_id": category_id,
            "obra_id": obra_id
        })
        assert machine1.status_code == 200
        machine1_id = machine1.json()["id"]
        
        machine2 = self.session.post(f"{BASE_URL}/api/machines", json={
            "name": "TEST_Machine Stats 2",
            "plate": "TEST-STATS-002",
            "category_id": category_id,
            "obra_id": obra_id
        })
        assert machine2.status_code == 200
        machine2_id = machine2.json()["id"]
        
        # Create a maintenance
        maintenance = self.session.post(f"{BASE_URL}/api/maintenances", json={
            "machine_id": machine1_id,
            "part_name": "TEST_Peça Stats",
            "replacement_date": "2024-01-15",
            "part_value": 500.00,
            "maintenance_type": "preventiva"
        })
        assert maintenance.status_code == 200
        maint_id = maintenance.json()["id"]
        
        # Get obras list
        obras_list = self.session.get(f"{BASE_URL}/api/obras")
        assert obras_list.status_code == 200
        
        # Find our test obra
        test_obra = None
        for obra in obras_list.json():
            if obra["id"] == obra_id:
                test_obra = obra
                break
        
        assert test_obra is not None
        assert test_obra["machine_count"] == 2, f"Expected 2 machines, got {test_obra['machine_count']}"
        assert test_obra["total_maintenance_cost"] == 500.00, f"Expected 500.00, got {test_obra['total_maintenance_cost']}"
        print(f"✓ Obra list shows correct stats: {test_obra['machine_count']} machines, R${test_obra['total_maintenance_cost']}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/maintenances/{maint_id}")
        self.session.delete(f"{BASE_URL}/api/machines/{machine1_id}")
        self.session.delete(f"{BASE_URL}/api/machines/{machine2_id}")
        self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
    
    # ============ FILTER MACHINES BY OBRA ============
    
    def test_filter_machines_by_obra(self):
        """Test filtering machines by obra_id"""
        # Create an obra
        obra_response = self.session.post(f"{BASE_URL}/api/obras", json={
            "name": "TEST_Obra Filter",
            "status": "em_andamento"
        })
        assert obra_response.status_code == 200
        obra_id = obra_response.json()["id"]
        
        # Create a category
        cat_response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Category Filter",
            "description": "Test category"
        })
        assert cat_response.status_code == 200
        category_id = cat_response.json()["id"]
        
        # Create a machine linked to obra
        machine_response = self.session.post(f"{BASE_URL}/api/machines", json={
            "name": "TEST_Machine Filter",
            "plate": "TEST-FILTER-001",
            "category_id": category_id,
            "obra_id": obra_id
        })
        assert machine_response.status_code == 200
        machine_id = machine_response.json()["id"]
        
        # Filter machines by obra_id
        response = self.session.get(f"{BASE_URL}/api/machines?obra_id={obra_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        machine_ids = [m["id"] for m in data]
        assert machine_id in machine_ids
        print(f"✓ Filtered machines by obra_id: found {len(data)} machines")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/machines/{machine_id}")
        self.session.delete(f"{BASE_URL}/api/categories/{category_id}")
    
    # ============ DELETE OBRA UNLINKS MACHINES ============
    
    def test_delete_obra_unlinks_machines(self):
        """Test that deleting an obra unlinks machines but doesn't delete them"""
        # Create an obra
        obra_response = self.session.post(f"{BASE_URL}/api/obras", json={
            "name": "TEST_Obra Delete Unlink",
            "status": "em_andamento"
        })
        assert obra_response.status_code == 200
        obra_id = obra_response.json()["id"]
        
        # Create a category
        cat_response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Category Delete Unlink",
            "description": "Test category"
        })
        assert cat_response.status_code == 200
        category_id = cat_response.json()["id"]
        
        # Create a machine linked to obra
        machine_response = self.session.post(f"{BASE_URL}/api/machines", json={
            "name": "TEST_Machine Delete Unlink",
            "plate": "TEST-DEL-UNLINK-001",
            "category_id": category_id,
            "obra_id": obra_id
        })
        assert machine_response.status_code == 200
        machine_id = machine_response.json()["id"]
        
        # Delete the obra
        delete_response = self.session.delete(f"{BASE_URL}/api/obras/{obra_id}")
        assert delete_response.status_code == 200
        
        # Verify machine still exists but obra_id is null
        machine_check = self.session.get(f"{BASE_URL}/api/machines/{machine_id}")
        assert machine_check.status_code == 200
        machine_data = machine_check.json()
        assert machine_data["obra_id"] is None, f"Expected obra_id to be None, got {machine_data['obra_id']}"
        print(f"✓ Machine still exists after obra deletion with obra_id=None")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/machines/{machine_id}")
        self.session.delete(f"{BASE_URL}/api/categories/{category_id}")


class TestLowStockAlerts:
    """Test low stock alerts functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed - skipping tests")
        
        yield
    
    def test_low_stock_notification(self):
        """Test that low stock items appear in notifications"""
        # Create a stock item with low quantity
        item_response = self.session.post(f"{BASE_URL}/api/stock/items", json={
            "name": "TEST_Low Stock Item",
            "code": "TEST-LOW-001",
            "category": "Filtros",
            "unit": "un",
            "quantity": 2,  # Low quantity (< 5)
            "min_quantity": 5,
            "unit_price": 50.00
        })
        assert item_response.status_code == 200
        item_id = item_response.json()["id"]
        
        # Check notifications
        notifications = self.session.get(f"{BASE_URL}/api/notifications")
        assert notifications.status_code == 200
        
        notif_data = notifications.json()
        low_stock_notifs = [n for n in notif_data if "stock" in n["notification_type"]]
        
        # Should have at least one low stock notification
        assert len(low_stock_notifs) >= 1, "Expected at least one low stock notification"
        print(f"✓ Found {len(low_stock_notifs)} low stock notifications")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/stock/items/{item_id}")
    
    def test_dashboard_low_stock_count(self):
        """Test that dashboard shows low stock count"""
        # Create a stock item with low quantity
        item_response = self.session.post(f"{BASE_URL}/api/stock/items", json={
            "name": "TEST_Dashboard Low Stock",
            "code": "TEST-DASH-LOW-001",
            "category": "Óleos",
            "unit": "L",
            "quantity": 1,
            "min_quantity": 10,
            "unit_price": 30.00
        })
        assert item_response.status_code == 200
        item_id = item_response.json()["id"]
        
        # Check dashboard
        dashboard = self.session.get(f"{BASE_URL}/api/dashboard")
        assert dashboard.status_code == 200
        
        data = dashboard.json()
        assert "low_stock_count" in data
        assert data["low_stock_count"] >= 1, f"Expected low_stock_count >= 1, got {data['low_stock_count']}"
        print(f"✓ Dashboard shows low_stock_count: {data['low_stock_count']}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/stock/items/{item_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
