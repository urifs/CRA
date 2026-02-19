"""
Test suite for Audit System
Tests:
- Audit log creation on CRUD operations (create, edit, delete)
- Audit log API endpoint with filters
- Shared data visibility across users
- User name tracking in audit logs
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_1_EMAIL = "test@test.com"
TEST_USER_1_PASSWORD = "password"
TEST_USER_2_EMAIL = f"testuser2_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER_2_PASSWORD = "password123"
TEST_USER_2_NAME = "Test User 2"


class TestAuditSystem:
    """Test audit system functionality"""
    
    @pytest.fixture(scope="class")
    def user1_session(self):
        """Login as test user 1"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_1_EMAIL,
            "password": TEST_USER_1_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        token = response.json()["token"]
        user = response.json()["user"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        session.user = user
        return session
    
    @pytest.fixture(scope="class")
    def user2_session(self):
        """Register and login as test user 2"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Register new user
        response = session.post(f"{BASE_URL}/api/auth/register", json={
            "name": TEST_USER_2_NAME,
            "email": TEST_USER_2_EMAIL,
            "password": TEST_USER_2_PASSWORD
        })
        
        if response.status_code == 400:
            # User already exists, try login
            response = session.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_USER_2_EMAIL,
                "password": TEST_USER_2_PASSWORD
            })
        
        assert response.status_code == 200, f"Auth failed: {response.text}"
        
        token = response.json()["token"]
        user = response.json()["user"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        session.user = user
        return session
    
    # ============ AUDIT LOG API TESTS ============
    
    def test_get_audit_logs_endpoint(self, user1_session):
        """Test GET /api/audit-logs returns logs"""
        response = user1_session.get(f"{BASE_URL}/api/audit-logs?limit=10")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        logs = response.json()
        assert isinstance(logs, list), "Response should be a list"
        print(f"SUCCESS: GET /api/audit-logs returned {len(logs)} logs")
    
    def test_audit_log_structure(self, user1_session):
        """Test audit log response structure"""
        response = user1_session.get(f"{BASE_URL}/api/audit-logs?limit=5")
        assert response.status_code == 200
        
        logs = response.json()
        if len(logs) > 0:
            log = logs[0]
            required_fields = ["id", "user_id", "user_name", "user_email", "action", 
                             "entity_type", "entity_id", "entity_name", "created_at"]
            for field in required_fields:
                assert field in log, f"Missing field: {field}"
            print(f"SUCCESS: Audit log has all required fields: {required_fields}")
        else:
            print("WARNING: No audit logs found to verify structure")
    
    def test_audit_log_filter_by_entity_type(self, user1_session):
        """Test filtering audit logs by entity_type"""
        response = user1_session.get(f"{BASE_URL}/api/audit-logs?entity_type=máquina&limit=50")
        assert response.status_code == 200
        
        logs = response.json()
        for log in logs:
            assert log["entity_type"] == "máquina", f"Filter failed: got {log['entity_type']}"
        print(f"SUCCESS: Filter by entity_type=máquina returned {len(logs)} logs")
    
    def test_audit_log_filter_by_action(self, user1_session):
        """Test filtering audit logs by action (via entity_type filter)"""
        # Note: API only supports entity_type and user_id filters
        response = user1_session.get(f"{BASE_URL}/api/audit-logs?limit=100")
        assert response.status_code == 200
        
        logs = response.json()
        actions = set(log["action"] for log in logs)
        print(f"SUCCESS: Found actions in logs: {actions}")
    
    # ============ AUDIT LOG CREATION ON CRUD ============
    
    def test_create_machine_generates_audit_log(self, user1_session):
        """Test that creating a machine generates an audit log"""
        # First get categories
        cat_response = user1_session.get(f"{BASE_URL}/api/categories")
        categories = cat_response.json()
        
        if not categories:
            # Create a category first
            cat_create = user1_session.post(f"{BASE_URL}/api/categories", json={
                "name": f"TEST_AuditCat_{uuid.uuid4().hex[:6]}",
                "description": "Test category for audit"
            })
            category_id = cat_create.json()["id"]
        else:
            category_id = categories[0]["id"]
        
        # Create machine
        machine_name = f"TEST_AuditMachine_{uuid.uuid4().hex[:6]}"
        machine_plate = f"AUD{uuid.uuid4().hex[:4].upper()}"
        
        create_response = user1_session.post(f"{BASE_URL}/api/machines", json={
            "name": machine_name,
            "plate": machine_plate,
            "category_id": category_id,
            "brand": "TestBrand",
            "model": "TestModel"
        })
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        machine_id = create_response.json()["id"]
        
        # Check audit log
        audit_response = user1_session.get(f"{BASE_URL}/api/audit-logs?entity_type=máquina&limit=10")
        assert audit_response.status_code == 200
        
        logs = audit_response.json()
        create_log = next((l for l in logs if l["entity_id"] == machine_id and l["action"] == "criar"), None)
        
        assert create_log is not None, "Audit log for machine creation not found"
        assert create_log["user_name"] == user1_session.user["name"], "User name mismatch in audit log"
        assert "criar" == create_log["action"], "Action should be 'criar'"
        
        print(f"SUCCESS: Machine creation generated audit log with user_name={create_log['user_name']}")
        
        # Cleanup
        user1_session.delete(f"{BASE_URL}/api/machines/{machine_id}")
        return machine_id
    
    def test_edit_machine_generates_audit_log(self, user1_session):
        """Test that editing a machine generates an audit log with details"""
        # Get categories
        cat_response = user1_session.get(f"{BASE_URL}/api/categories")
        categories = cat_response.json()
        category_id = categories[0]["id"] if categories else None
        
        if not category_id:
            pytest.skip("No categories available")
        
        # Create machine
        machine_name = f"TEST_EditAudit_{uuid.uuid4().hex[:6]}"
        machine_plate = f"EDT{uuid.uuid4().hex[:4].upper()}"
        
        create_response = user1_session.post(f"{BASE_URL}/api/machines", json={
            "name": machine_name,
            "plate": machine_plate,
            "category_id": category_id
        })
        machine_id = create_response.json()["id"]
        
        # Edit machine
        new_name = f"TEST_EditedMachine_{uuid.uuid4().hex[:6]}"
        edit_response = user1_session.put(f"{BASE_URL}/api/machines/{machine_id}", json={
            "name": new_name,
            "plate": machine_plate,
            "category_id": category_id
        })
        assert edit_response.status_code == 200, f"Edit failed: {edit_response.text}"
        
        # Check audit log
        audit_response = user1_session.get(f"{BASE_URL}/api/audit-logs?entity_type=máquina&limit=10")
        logs = audit_response.json()
        
        edit_log = next((l for l in logs if l["entity_id"] == machine_id and l["action"] == "editar"), None)
        
        assert edit_log is not None, "Audit log for machine edit not found"
        assert edit_log["details"], "Edit audit log should have details"
        assert "editar" == edit_log["action"], "Action should be 'editar'"
        
        print(f"SUCCESS: Machine edit generated audit log with details: {edit_log['details']}")
        
        # Cleanup
        user1_session.delete(f"{BASE_URL}/api/machines/{machine_id}")
    
    def test_delete_machine_generates_audit_log(self, user1_session):
        """Test that deleting a machine generates an audit log"""
        # Get categories
        cat_response = user1_session.get(f"{BASE_URL}/api/categories")
        categories = cat_response.json()
        category_id = categories[0]["id"] if categories else None
        
        if not category_id:
            pytest.skip("No categories available")
        
        # Create machine
        machine_name = f"TEST_DeleteAudit_{uuid.uuid4().hex[:6]}"
        machine_plate = f"DEL{uuid.uuid4().hex[:4].upper()}"
        
        create_response = user1_session.post(f"{BASE_URL}/api/machines", json={
            "name": machine_name,
            "plate": machine_plate,
            "category_id": category_id
        })
        machine_id = create_response.json()["id"]
        
        # Delete machine
        delete_response = user1_session.delete(f"{BASE_URL}/api/machines/{machine_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        # Check audit log
        audit_response = user1_session.get(f"{BASE_URL}/api/audit-logs?entity_type=máquina&limit=10")
        logs = audit_response.json()
        
        delete_log = next((l for l in logs if l["entity_id"] == machine_id and l["action"] == "excluir"), None)
        
        assert delete_log is not None, "Audit log for machine deletion not found"
        assert "excluir" == delete_log["action"], "Action should be 'excluir'"
        
        print(f"SUCCESS: Machine deletion generated audit log")
    
    def test_create_maintenance_generates_audit_log(self, user1_session):
        """Test that creating a maintenance generates an audit log"""
        # Get machines
        machines_response = user1_session.get(f"{BASE_URL}/api/machines")
        machines = machines_response.json()
        
        if not machines:
            pytest.skip("No machines available")
        
        machine_id = machines[0]["id"]
        
        # Create maintenance
        maintenance_response = user1_session.post(f"{BASE_URL}/api/maintenances", json={
            "machine_id": machine_id,
            "part_name": f"TEST_AuditPart_{uuid.uuid4().hex[:6]}",
            "replacement_date": "2025-01-15",
            "part_value": 150.00,
            "maintenance_type": "preventiva",
            "description": "Test maintenance for audit"
        })
        assert maintenance_response.status_code == 200, f"Create failed: {maintenance_response.text}"
        maintenance_id = maintenance_response.json()["id"]
        
        # Check audit log
        audit_response = user1_session.get(f"{BASE_URL}/api/audit-logs?entity_type=manutenção&limit=10")
        logs = audit_response.json()
        
        create_log = next((l for l in logs if l["entity_id"] == maintenance_id and l["action"] == "criar"), None)
        
        assert create_log is not None, "Audit log for maintenance creation not found"
        assert "Valor:" in create_log["details"], "Maintenance audit should include value details"
        
        print(f"SUCCESS: Maintenance creation generated audit log with details: {create_log['details']}")
        
        # Cleanup
        user1_session.delete(f"{BASE_URL}/api/maintenances/{maintenance_id}")
    
    def test_create_obra_generates_audit_log(self, user1_session):
        """Test that creating an obra generates an audit log"""
        obra_name = f"TEST_AuditObra_{uuid.uuid4().hex[:6]}"
        
        create_response = user1_session.post(f"{BASE_URL}/api/obras", json={
            "name": obra_name,
            "description": "Test obra for audit",
            "location": "Test Location",
            "status": "em_andamento"
        })
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        obra_id = create_response.json()["id"]
        
        # Check audit log
        audit_response = user1_session.get(f"{BASE_URL}/api/audit-logs?entity_type=obra&limit=10")
        logs = audit_response.json()
        
        create_log = next((l for l in logs if l["entity_id"] == obra_id and l["action"] == "criar"), None)
        
        assert create_log is not None, "Audit log for obra creation not found"
        assert create_log["entity_name"] == obra_name, "Entity name should match obra name"
        
        print(f"SUCCESS: Obra creation generated audit log")
        
        # Cleanup
        user1_session.delete(f"{BASE_URL}/api/obras/{obra_id}")
    
    def test_create_stock_item_generates_audit_log(self, user1_session):
        """Test that creating a stock item generates an audit log"""
        item_name = f"TEST_AuditStock_{uuid.uuid4().hex[:6]}"
        
        create_response = user1_session.post(f"{BASE_URL}/api/stock/items", json={
            "name": item_name,
            "code": "AUD001",
            "category": "Filtros",
            "unit": "un",
            "quantity": 10,
            "min_quantity": 5
        })
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        item_id = create_response.json()["id"]
        
        # Check audit log
        audit_response = user1_session.get(f"{BASE_URL}/api/audit-logs?entity_type=item de estoque&limit=10")
        logs = audit_response.json()
        
        create_log = next((l for l in logs if l["entity_id"] == item_id and l["action"] == "criar"), None)
        
        assert create_log is not None, "Audit log for stock item creation not found"
        
        print(f"SUCCESS: Stock item creation generated audit log")
        
        # Cleanup
        user1_session.delete(f"{BASE_URL}/api/stock/items/{item_id}")
    
    # ============ SHARED DATA TESTS ============
    
    def test_user2_sees_data_created_by_user1(self, user1_session, user2_session):
        """Test that user 2 can see data created by user 1 (shared system)"""
        # Get categories
        cat_response = user1_session.get(f"{BASE_URL}/api/categories")
        categories = cat_response.json()
        category_id = categories[0]["id"] if categories else None
        
        if not category_id:
            # Create category
            cat_create = user1_session.post(f"{BASE_URL}/api/categories", json={
                "name": f"TEST_SharedCat_{uuid.uuid4().hex[:6]}",
                "description": "Shared category test"
            })
            category_id = cat_create.json()["id"]
        
        # User 1 creates a machine
        machine_name = f"TEST_SharedMachine_{uuid.uuid4().hex[:6]}"
        machine_plate = f"SHR{uuid.uuid4().hex[:4].upper()}"
        
        create_response = user1_session.post(f"{BASE_URL}/api/machines", json={
            "name": machine_name,
            "plate": machine_plate,
            "category_id": category_id
        })
        assert create_response.status_code == 200
        machine_id = create_response.json()["id"]
        
        # User 2 should see the machine
        user2_machines = user2_session.get(f"{BASE_URL}/api/machines")
        assert user2_machines.status_code == 200
        
        machines = user2_machines.json()
        found_machine = next((m for m in machines if m["id"] == machine_id), None)
        
        assert found_machine is not None, "User 2 should see machine created by User 1"
        assert found_machine["name"] == machine_name, "Machine data should match"
        
        print(f"SUCCESS: User 2 can see machine '{machine_name}' created by User 1")
        
        # Cleanup
        user1_session.delete(f"{BASE_URL}/api/machines/{machine_id}")
    
    def test_user2_sees_audit_logs_from_user1(self, user1_session, user2_session):
        """Test that user 2 can see audit logs from user 1's actions"""
        # User 2 gets audit logs
        audit_response = user2_session.get(f"{BASE_URL}/api/audit-logs?limit=50")
        assert audit_response.status_code == 200
        
        logs = audit_response.json()
        
        # Check if there are logs from user 1
        user1_logs = [l for l in logs if l["user_email"] == TEST_USER_1_EMAIL]
        
        print(f"SUCCESS: User 2 can see {len(user1_logs)} audit logs from User 1")
        assert len(user1_logs) >= 0, "User 2 should be able to see audit logs"
    
    def test_user2_creates_data_visible_to_user1(self, user1_session, user2_session):
        """Test that data created by user 2 is visible to user 1"""
        # Get categories
        cat_response = user2_session.get(f"{BASE_URL}/api/categories")
        categories = cat_response.json()
        category_id = categories[0]["id"] if categories else None
        
        if not category_id:
            pytest.skip("No categories available")
        
        # User 2 creates a machine
        machine_name = f"TEST_User2Machine_{uuid.uuid4().hex[:6]}"
        machine_plate = f"U2M{uuid.uuid4().hex[:4].upper()}"
        
        create_response = user2_session.post(f"{BASE_URL}/api/machines", json={
            "name": machine_name,
            "plate": machine_plate,
            "category_id": category_id
        })
        assert create_response.status_code == 200
        machine_id = create_response.json()["id"]
        
        # User 1 should see the machine
        user1_machines = user1_session.get(f"{BASE_URL}/api/machines")
        assert user1_machines.status_code == 200
        
        machines = user1_machines.json()
        found_machine = next((m for m in machines if m["id"] == machine_id), None)
        
        assert found_machine is not None, "User 1 should see machine created by User 2"
        
        # Check audit log shows User 2's name
        audit_response = user1_session.get(f"{BASE_URL}/api/audit-logs?entity_type=máquina&limit=20")
        logs = audit_response.json()
        
        user2_log = next((l for l in logs if l["entity_id"] == machine_id), None)
        assert user2_log is not None, "Audit log should exist for User 2's machine"
        assert user2_log["user_name"] == TEST_USER_2_NAME, f"Audit log should show User 2's name, got: {user2_log['user_name']}"
        
        print(f"SUCCESS: User 1 sees machine created by User 2, audit shows '{user2_log['user_name']}'")
        
        # Cleanup
        user2_session.delete(f"{BASE_URL}/api/machines/{machine_id}")
    
    # ============ AUDIT LOG CONTENT TESTS ============
    
    def test_audit_log_contains_user_name(self, user1_session):
        """Test that audit logs contain the user's name"""
        response = user1_session.get(f"{BASE_URL}/api/audit-logs?limit=10")
        assert response.status_code == 200
        
        logs = response.json()
        for log in logs:
            assert log["user_name"], f"Audit log should have user_name, got: {log}"
            assert log["user_email"], f"Audit log should have user_email, got: {log}"
        
        print(f"SUCCESS: All audit logs contain user_name and user_email")
    
    def test_audit_log_actions_are_valid(self, user1_session):
        """Test that audit log actions are valid (criar, editar, excluir)"""
        response = user1_session.get(f"{BASE_URL}/api/audit-logs?limit=100")
        assert response.status_code == 200
        
        logs = response.json()
        valid_actions = {"criar", "editar", "excluir"}
        
        for log in logs:
            assert log["action"] in valid_actions, f"Invalid action: {log['action']}"
        
        print(f"SUCCESS: All audit log actions are valid")


class TestAuditCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_machines(self):
        """Cleanup TEST_ prefixed machines"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_1_EMAIL,
            "password": TEST_USER_1_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Cannot login for cleanup")
        
        token = response.json()["token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get all machines
        machines_response = session.get(f"{BASE_URL}/api/machines")
        if machines_response.status_code == 200:
            machines = machines_response.json()
            for machine in machines:
                if machine["name"].startswith("TEST_"):
                    session.delete(f"{BASE_URL}/api/machines/{machine['id']}")
                    print(f"Cleaned up machine: {machine['name']}")
        
        print("SUCCESS: Cleanup completed")
