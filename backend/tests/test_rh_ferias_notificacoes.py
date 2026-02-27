"""
Test suite for RH Férias and Notificações endpoints
Tests:
- GET /api/rh/ferias?ano=2026 - List férias by year
- POST /api/rh/ferias - Create férias
- PUT /api/rh/ferias/{id} - Update férias
- DELETE /api/rh/ferias/{id} - Delete férias
- GET /api/rh/ferias/alertas - Alertas de período aquisitivo
- GET /api/rh/notificacoes - All notifications
- GET /api/rh/notificacoes/contagem - Badge count
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuth:
    """Authentication helper"""
    
    @staticmethod
    def get_token():
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None


class TestFeriasEndpoints:
    """Test Férias CRUD endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuth.get_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        # Get existing funcionario ID
        response = requests.get(f"{BASE_URL}/api/rh/funcionarios", headers=self.headers)
        if response.status_code == 200 and response.json():
            self.funcionario_id = response.json()[0]["id"]
        else:
            self.funcionario_id = "9f166c5e-f770-4657-bb1e-ae1f7fb9433b"
    
    def test_list_ferias_by_year(self):
        """GET /api/rh/ferias?ano=2026 - List férias for year 2026"""
        response = requests.get(f"{BASE_URL}/api/rh/ferias?ano=2026", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify existing férias from context
        if len(data) > 0:
            ferias = data[0]
            assert "id" in ferias, "Férias should have id"
            assert "funcionario_id" in ferias, "Férias should have funcionario_id"
            assert "data_inicio" in ferias, "Férias should have data_inicio"
            assert "data_fim" in ferias, "Férias should have data_fim"
            print(f"Found {len(data)} férias for 2026")
    
    def test_list_ferias_empty_year(self):
        """GET /api/rh/ferias?ano=2020 - List férias for year with no data"""
        response = requests.get(f"{BASE_URL}/api/rh/ferias?ano=2020", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} férias for 2020 (expected 0 or few)")
    
    def test_create_ferias(self):
        """POST /api/rh/ferias - Create new férias"""
        ferias_data = {
            "funcionario_id": self.funcionario_id,
            "data_inicio": "2026-07-01",
            "data_fim": "2026-07-30",
            "dias_vendidos": 5,
            "observacoes": "TEST_Férias de julho"
        }
        
        response = requests.post(f"{BASE_URL}/api/rh/ferias", json=ferias_data, headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "id" in data, "Response should have id"
        assert data["funcionario_id"] == self.funcionario_id, "funcionario_id should match"
        assert data["data_inicio"] == "2026-07-01", "data_inicio should match"
        assert data["data_fim"] == "2026-07-30", "data_fim should match"
        assert data["dias_vendidos"] == 5, "dias_vendidos should match"
        
        # Store for cleanup
        self.created_ferias_id = data["id"]
        print(f"Created férias with ID: {data['id']}")
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/rh/ferias?ano=2026", headers=self.headers)
        assert get_response.status_code == 200
        ferias_list = get_response.json()
        found = any(f["id"] == data["id"] for f in ferias_list)
        assert found, "Created férias should be in list"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/rh/ferias/{data['id']}", headers=self.headers)
    
    def test_update_ferias(self):
        """PUT /api/rh/ferias/{id} - Update existing férias"""
        # First create a férias to update
        ferias_data = {
            "funcionario_id": self.funcionario_id,
            "data_inicio": "2026-08-01",
            "data_fim": "2026-08-15",
            "dias_vendidos": 0,
            "observacoes": "TEST_Original"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/rh/ferias", json=ferias_data, headers=self.headers)
        assert create_response.status_code == 200
        ferias_id = create_response.json()["id"]
        
        # Update the férias
        update_data = {
            "funcionario_id": self.funcionario_id,
            "data_inicio": "2026-08-05",
            "data_fim": "2026-08-20",
            "dias_vendidos": 3,
            "observacoes": "TEST_Updated"
        }
        
        update_response = requests.put(f"{BASE_URL}/api/rh/ferias/{ferias_id}", json=update_data, headers=self.headers)
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        data = update_response.json()
        assert "message" in data or "id" in data, "Response should confirm update"
        print(f"Updated férias {ferias_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/rh/ferias/{ferias_id}", headers=self.headers)
    
    def test_update_ferias_not_found(self):
        """PUT /api/rh/ferias/{id} - Update non-existent férias returns 404"""
        fake_id = str(uuid.uuid4())
        update_data = {
            "funcionario_id": self.funcionario_id,
            "data_inicio": "2026-08-01",
            "data_fim": "2026-08-15",
            "dias_vendidos": 0,
            "observacoes": "TEST"
        }
        
        response = requests.put(f"{BASE_URL}/api/rh/ferias/{fake_id}", json=update_data, headers=self.headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Correctly returned 404 for non-existent férias")
    
    def test_delete_ferias(self):
        """DELETE /api/rh/ferias/{id} - Delete férias"""
        # First create a férias to delete
        ferias_data = {
            "funcionario_id": self.funcionario_id,
            "data_inicio": "2026-09-01",
            "data_fim": "2026-09-15",
            "dias_vendidos": 0,
            "observacoes": "TEST_To be deleted"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/rh/ferias", json=ferias_data, headers=self.headers)
        assert create_response.status_code == 200
        ferias_id = create_response.json()["id"]
        
        # Delete the férias
        delete_response = requests.delete(f"{BASE_URL}/api/rh/ferias/{ferias_id}", headers=self.headers)
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        data = delete_response.json()
        assert "message" in data, "Response should have message"
        print(f"Deleted férias {ferias_id}")
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/rh/ferias?ano=2026", headers=self.headers)
        ferias_list = get_response.json()
        found = any(f["id"] == ferias_id for f in ferias_list)
        assert not found, "Deleted férias should not be in list"
    
    def test_delete_ferias_not_found(self):
        """DELETE /api/rh/ferias/{id} - Delete non-existent férias returns 404"""
        fake_id = str(uuid.uuid4())
        
        response = requests.delete(f"{BASE_URL}/api/rh/ferias/{fake_id}", headers=self.headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Correctly returned 404 for non-existent férias")


class TestFeriasAlertas:
    """Test Férias Alertas endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuth.get_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_ferias_alertas(self):
        """GET /api/rh/ferias/alertas - Get período aquisitivo alerts"""
        response = requests.get(f"{BASE_URL}/api/rh/ferias/alertas", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify alert structure if any exist
        if len(data) > 0:
            alerta = data[0]
            assert "funcionario_id" in alerta, "Alert should have funcionario_id"
            assert "funcionario_nome" in alerta, "Alert should have funcionario_nome"
            assert "mensagem" in alerta, "Alert should have mensagem"
            print(f"Found {len(data)} alertas de período aquisitivo")
            for a in data:
                print(f"  - {a['funcionario_nome']}: {a['mensagem']}")
        else:
            print("No alertas de período aquisitivo found")


class TestNotificacoes:
    """Test RH Notificações endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuth.get_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_all_notificacoes(self):
        """GET /api/rh/notificacoes - Get all RH notifications"""
        response = requests.get(f"{BASE_URL}/api/rh/notificacoes", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify structure
        assert "aniversariantes" in data, "Response should have aniversariantes"
        assert "alertas_ferias" in data, "Response should have alertas_ferias"
        assert "funcionarios_sem_ferias" in data, "Response should have funcionarios_sem_ferias"
        assert "alertas_epi" in data, "Response should have alertas_epi"
        assert "alertas_atestados" in data, "Response should have alertas_atestados"
        assert "inconsistencias_ponto" in data, "Response should have inconsistencias_ponto"
        
        # All should be lists
        assert isinstance(data["aniversariantes"], list)
        assert isinstance(data["alertas_ferias"], list)
        assert isinstance(data["funcionarios_sem_ferias"], list)
        assert isinstance(data["alertas_epi"], list)
        assert isinstance(data["alertas_atestados"], list)
        assert isinstance(data["inconsistencias_ponto"], list)
        
        print(f"Notificações summary:")
        print(f"  - Aniversariantes: {len(data['aniversariantes'])}")
        print(f"  - Alertas férias: {len(data['alertas_ferias'])}")
        print(f"  - Funcionários sem férias: {len(data['funcionarios_sem_ferias'])}")
        print(f"  - Alertas EPI: {len(data['alertas_epi'])}")
        print(f"  - Inconsistências ponto: {len(data['inconsistencias_ponto'])}")
    
    def test_aniversariantes_structure(self):
        """Verify aniversariantes data structure"""
        response = requests.get(f"{BASE_URL}/api/rh/notificacoes", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["aniversariantes"]) > 0:
            aniv = data["aniversariantes"][0]
            assert "nome" in aniv, "Aniversariante should have nome"
            assert "cargo" in aniv, "Aniversariante should have cargo"
            assert "data_formatada" in aniv, "Aniversariante should have data_formatada"
            assert "idade" in aniv, "Aniversariante should have idade"
            print(f"Aniversariante: {aniv['nome']} - {aniv['data_formatada']} ({aniv['idade']} anos)")
    
    def test_funcionarios_sem_ferias_structure(self):
        """Verify funcionarios_sem_ferias data structure"""
        response = requests.get(f"{BASE_URL}/api/rh/notificacoes", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["funcionarios_sem_ferias"]) > 0:
            func = data["funcionarios_sem_ferias"][0]
            assert "nome" in func, "Funcionário should have nome"
            assert "ultima_ferias" in func, "Funcionário should have ultima_ferias"
            print(f"Funcionário sem férias: {func['nome']} - Última: {func['ultima_ferias']}")
    
    def test_get_notificacoes_contagem(self):
        """GET /api/rh/notificacoes/contagem - Get badge count"""
        response = requests.get(f"{BASE_URL}/api/rh/notificacoes/contagem", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "total" in data, "Response should have total"
        assert "urgentes" in data, "Response should have urgentes"
        assert isinstance(data["total"], int), "total should be int"
        assert isinstance(data["urgentes"], int), "urgentes should be int"
        assert data["total"] >= 0, "total should be >= 0"
        assert data["urgentes"] >= 0, "urgentes should be >= 0"
        assert data["urgentes"] <= data["total"], "urgentes should be <= total"
        
        print(f"Contagem: total={data['total']}, urgentes={data['urgentes']}")


class TestExistingFerias:
    """Test with existing férias data from context"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuth.get_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        # Known férias ID from context
        self.existing_ferias_id = "26a9cdfb-1fa8-4c94-8083-883d681d96cd"
    
    def test_existing_ferias_in_list(self):
        """Verify existing férias from context is in the list"""
        response = requests.get(f"{BASE_URL}/api/rh/ferias?ano=2026", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        found = any(f["id"] == self.existing_ferias_id for f in data)
        assert found, f"Existing férias {self.existing_ferias_id} should be in list"
        
        # Verify the férias details
        ferias = next((f for f in data if f["id"] == self.existing_ferias_id), None)
        if ferias:
            assert ferias["data_inicio"] == "2026-03-01", "data_inicio should be 2026-03-01"
            assert ferias["data_fim"] == "2026-03-30", "data_fim should be 2026-03-30"
            print(f"Verified existing férias: {ferias['data_inicio']} to {ferias['data_fim']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
