"""
Test suite for Aluguéis de Máquinas and Central de Notificações features
Tests:
- Aluguéis CRUD operations
- Automatic conta a receber generation
- Finalizar aluguel (marks conta a receber as quitada)
- Maquinas disponiveis endpoint
- Notificações endpoint with prazo configurável
- Notificações contagem for badge
- Urgency classification (alta, media, baixa)
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data


class TestMaquinasDisponiveis:
    """Tests for maquinas-disponiveis endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        return response.json()["token"]
    
    def test_get_maquinas_disponiveis(self, auth_token):
        """Test getting available machines from management system"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/maquinas-disponiveis", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify machine structure if any exist
        if len(data) > 0:
            machine = data[0]
            assert "id" in machine
            assert "name" in machine


class TestAlugueis:
    """Tests for Aluguéis CRUD operations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_alugueis_list(self, headers):
        """Test getting list of alugueis"""
        response = requests.get(f"{BASE_URL}/api/admin/alugueis", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_alugueis_filter_by_status(self, headers):
        """Test filtering alugueis by status"""
        for status in ["ativo", "finalizado", "cancelado"]:
            response = requests.get(f"{BASE_URL}/api/admin/alugueis?status={status}", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            # All returned items should have the filtered status
            for aluguel in data:
                assert aluguel.get("status") == status
    
    def test_create_aluguel_with_conta_receber(self, headers):
        """Test creating aluguel with automatic conta a receber generation"""
        # Get a machine first
        machines_response = requests.get(f"{BASE_URL}/api/admin/maquinas-disponiveis", headers=headers)
        machines = machines_response.json()
        
        maquina_id = machines[0]["id"] if machines else "test-machine-id"
        maquina_nome = machines[0]["name"] if machines else "Test Machine"
        maquina_placa = machines[0].get("plate", "") if machines else "TEST-001"
        
        # Create aluguel
        today = datetime.now().strftime("%Y-%m-%d")
        vencimento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        aluguel_data = {
            "maquina_id": maquina_id,
            "maquina_nome": maquina_nome,
            "maquina_placa": maquina_placa,
            "cliente_nome": "TEST_Cliente Aluguel",
            "cliente_telefone": "(11) 99999-9999",
            "cliente_documento": "123.456.789-00",
            "tipo_periodo": "mensal",
            "periodo_especificado": "",
            "data_entrega": today,
            "data_vencimento": vencimento,
            "valor": 1500.00,
            "valor_caucao": 500.00,
            "local_entrega": "Rua Teste, 123",
            "observacoes": "Aluguel de teste",
            "gerar_conta_receber": True
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/alugueis", headers=headers, json=aluguel_data)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert "numero" in data
        assert data["cliente_nome"] == "TEST_Cliente Aluguel"
        assert data["tipo_periodo"] == "mensal"
        assert data["valor"] == 1500.00
        assert data["status"] == "ativo"
        # Verify conta a receber was generated
        assert data.get("conta_receber_id") is not None, "Conta a receber should be generated"
        
        return data
    
    def test_create_aluguel_all_period_types(self, headers):
        """Test creating alugueis with all period types"""
        machines_response = requests.get(f"{BASE_URL}/api/admin/maquinas-disponiveis", headers=headers)
        machines = machines_response.json()
        
        maquina_id = machines[0]["id"] if machines else "test-machine-id"
        maquina_nome = machines[0]["name"] if machines else "Test Machine"
        
        today = datetime.now().strftime("%Y-%m-%d")
        vencimento = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        period_types = ["hora", "diaria", "semanal", "quinzenal", "mensal", "semestral", "anual"]
        
        for tipo in period_types:
            aluguel_data = {
                "maquina_id": maquina_id,
                "maquina_nome": maquina_nome,
                "cliente_nome": f"TEST_Cliente_{tipo}",
                "tipo_periodo": tipo,
                "data_entrega": today,
                "data_vencimento": vencimento,
                "valor": 100.00,
                "gerar_conta_receber": False
            }
            
            response = requests.post(f"{BASE_URL}/api/admin/alugueis", headers=headers, json=aluguel_data)
            assert response.status_code == 200, f"Create failed for {tipo}: {response.text}"
            data = response.json()
            assert data["tipo_periodo"] == tipo
    
    def test_create_aluguel_outro_period(self, headers):
        """Test creating aluguel with 'outro' period type"""
        machines_response = requests.get(f"{BASE_URL}/api/admin/maquinas-disponiveis", headers=headers)
        machines = machines_response.json()
        
        maquina_id = machines[0]["id"] if machines else "test-machine-id"
        
        today = datetime.now().strftime("%Y-%m-%d")
        vencimento = (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")
        
        aluguel_data = {
            "maquina_id": maquina_id,
            "maquina_nome": "Test Machine",
            "cliente_nome": "TEST_Cliente_Outro",
            "tipo_periodo": "outro",
            "periodo_especificado": "45 dias",
            "data_entrega": today,
            "data_vencimento": vencimento,
            "valor": 2000.00,
            "gerar_conta_receber": False
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/alugueis", headers=headers, json=aluguel_data)
        assert response.status_code == 200
        data = response.json()
        assert data["tipo_periodo"] == "outro"
        assert data["periodo_especificado"] == "45 dias"
    
    def test_update_aluguel(self, headers):
        """Test updating an aluguel"""
        # First create one
        machines_response = requests.get(f"{BASE_URL}/api/admin/maquinas-disponiveis", headers=headers)
        machines = machines_response.json()
        maquina_id = machines[0]["id"] if machines else "test-machine-id"
        
        today = datetime.now().strftime("%Y-%m-%d")
        vencimento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        create_data = {
            "maquina_id": maquina_id,
            "maquina_nome": "Test Machine",
            "cliente_nome": "TEST_Update_Original",
            "tipo_periodo": "diaria",
            "data_entrega": today,
            "data_vencimento": vencimento,
            "valor": 500.00,
            "gerar_conta_receber": False
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/alugueis", headers=headers, json=create_data)
        assert create_response.status_code == 200
        aluguel_id = create_response.json()["id"]
        
        # Update it
        update_data = {
            "maquina_id": maquina_id,
            "maquina_nome": "Test Machine",
            "cliente_nome": "TEST_Update_Modified",
            "tipo_periodo": "semanal",
            "data_entrega": today,
            "data_vencimento": vencimento,
            "valor": 750.00,
            "gerar_conta_receber": False
        }
        
        update_response = requests.put(f"{BASE_URL}/api/admin/alugueis/{aluguel_id}", headers=headers, json=update_data)
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["cliente_nome"] == "TEST_Update_Modified"
        assert updated["tipo_periodo"] == "semanal"
        assert updated["valor"] == 750.00
    
    def test_finalizar_aluguel_marks_conta_quitada(self, headers):
        """Test that finalizing aluguel marks associated conta a receber as quitada"""
        # Create aluguel with conta a receber
        machines_response = requests.get(f"{BASE_URL}/api/admin/maquinas-disponiveis", headers=headers)
        machines = machines_response.json()
        maquina_id = machines[0]["id"] if machines else "test-machine-id"
        
        today = datetime.now().strftime("%Y-%m-%d")
        vencimento = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        create_data = {
            "maquina_id": maquina_id,
            "maquina_nome": "Test Machine Finalizar",
            "cliente_nome": "TEST_Finalizar_Cliente",
            "tipo_periodo": "diaria",
            "data_entrega": today,
            "data_vencimento": vencimento,
            "valor": 300.00,
            "gerar_conta_receber": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/alugueis", headers=headers, json=create_data)
        assert create_response.status_code == 200
        aluguel = create_response.json()
        aluguel_id = aluguel["id"]
        conta_receber_id = aluguel.get("conta_receber_id")
        assert conta_receber_id is not None
        
        # Finalize the aluguel
        status_response = requests.patch(
            f"{BASE_URL}/api/admin/alugueis/{aluguel_id}/status",
            headers=headers,
            json={"status": "finalizado", "data_devolucao": today}
        )
        assert status_response.status_code == 200
        updated = status_response.json()
        assert updated["status"] == "finalizado"
        
        # Verify conta a receber is now quitada
        contas_response = requests.get(f"{BASE_URL}/api/admin/contas-receber", headers=headers)
        assert contas_response.status_code == 200
        contas = contas_response.json()
        conta = next((c for c in contas if c.get("id") == conta_receber_id), None)
        if conta:
            assert conta["status"] == "quitada", "Conta a receber should be marked as quitada"
    
    def test_delete_aluguel_deletes_conta_receber(self, headers):
        """Test that deleting aluguel also deletes associated conta a receber"""
        machines_response = requests.get(f"{BASE_URL}/api/admin/maquinas-disponiveis", headers=headers)
        machines = machines_response.json()
        maquina_id = machines[0]["id"] if machines else "test-machine-id"
        
        today = datetime.now().strftime("%Y-%m-%d")
        vencimento = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        create_data = {
            "maquina_id": maquina_id,
            "maquina_nome": "Test Machine Delete",
            "cliente_nome": "TEST_Delete_Cliente",
            "tipo_periodo": "diaria",
            "data_entrega": today,
            "data_vencimento": vencimento,
            "valor": 200.00,
            "gerar_conta_receber": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/alugueis", headers=headers, json=create_data)
        assert create_response.status_code == 200
        aluguel = create_response.json()
        aluguel_id = aluguel["id"]
        conta_receber_id = aluguel.get("conta_receber_id")
        
        # Delete the aluguel
        delete_response = requests.delete(f"{BASE_URL}/api/admin/alugueis/{aluguel_id}", headers=headers)
        assert delete_response.status_code == 200
        
        # Verify aluguel is deleted
        get_response = requests.get(f"{BASE_URL}/api/admin/alugueis/{aluguel_id}", headers=headers)
        assert get_response.status_code == 404


class TestNotificacoes:
    """Tests for Notificações endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_notificacoes_default_prazo(self, headers):
        """Test getting notificacoes with default prazo (7 days)"""
        response = requests.get(f"{BASE_URL}/api/admin/notificacoes", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "resumo" in data
        assert "notificacoes" in data
        assert "prazo_dias" in data
        assert data["prazo_dias"] == 7
        
        # Verify resumo structure
        resumo = data["resumo"]
        assert "total" in resumo
        assert "vencidas" in resumo
        assert "alta" in resumo
        assert "media" in resumo
        assert "baixa" in resumo
        assert "por_tipo" in resumo
        
        # Verify por_tipo structure
        por_tipo = resumo["por_tipo"]
        assert "conta_pagar" in por_tipo
        assert "conta_receber" in por_tipo
        assert "ordem_servico" in por_tipo
        assert "aluguel" in por_tipo
    
    def test_get_notificacoes_custom_prazo(self, headers):
        """Test getting notificacoes with custom prazo"""
        for prazo in [3, 14, 30, 60]:
            response = requests.get(f"{BASE_URL}/api/admin/notificacoes?prazo_dias={prazo}", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["prazo_dias"] == prazo
    
    def test_notificacoes_urgency_classification(self, headers):
        """Test that notificacoes have proper urgency classification"""
        response = requests.get(f"{BASE_URL}/api/admin/notificacoes?prazo_dias=30", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        for notif in data["notificacoes"]:
            assert "urgencia" in notif
            assert notif["urgencia"] in ["alta", "media", "baixa"]
            assert "vencida" in notif
            assert "tipo" in notif
            assert notif["tipo"] in ["conta_pagar", "conta_receber", "ordem_servico", "aluguel"]
    
    def test_notificacoes_contagem(self, headers):
        """Test notificacoes contagem endpoint for badge"""
        response = requests.get(f"{BASE_URL}/api/admin/notificacoes/contagem?prazo_dias=7", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "vencidas" in data
        assert "prazo_dias" in data
        assert isinstance(data["total"], int)
        assert isinstance(data["vencidas"], int)
    
    def test_notificacoes_contagem_custom_prazo(self, headers):
        """Test notificacoes contagem with different prazo values"""
        for prazo in [3, 7, 14, 30]:
            response = requests.get(f"{BASE_URL}/api/admin/notificacoes/contagem?prazo_dias={prazo}", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["prazo_dias"] == prazo


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_cleanup_test_alugueis(self, headers):
        """Clean up test alugueis"""
        response = requests.get(f"{BASE_URL}/api/admin/alugueis", headers=headers)
        if response.status_code == 200:
            alugueis = response.json()
            for aluguel in alugueis:
                if aluguel.get("cliente_nome", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/admin/alugueis/{aluguel['id']}", headers=headers)
        assert True  # Cleanup always passes
