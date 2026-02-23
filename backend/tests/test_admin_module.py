"""
Test suite for CRA Construtora Admin Module
Tests: Dashboard, Contas a Pagar, Contas a Receber, Fornecedores, Produtos, Ordens de Serviço, Plano de Contas
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
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
        assert data["user"]["email"] == "test@test.com"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@test.com",
        "password": "password"
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAdminDashboard:
    """Admin Dashboard tests"""
    
    def test_get_dashboard(self, auth_headers):
        """Test GET /api/admin/dashboard"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats structure
        assert "stats" in data
        stats = data["stats"]
        assert "totalPagar" in stats
        assert "totalReceber" in stats
        assert "saldoPrevisto" in stats
        assert "contasVencidas" in stats
        assert "notasEmitidas" in stats
        assert "fornecedores" in stats
        assert "produtos" in stats
        assert "ordensAbertas" in stats
        
        # Verify contasProximas
        assert "contasProximas" in data
        assert isinstance(data["contasProximas"], list)
    
    def test_dashboard_requires_auth(self):
        """Test dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard")
        assert response.status_code in [401, 403]


class TestContasPagar:
    """Contas a Pagar CRUD tests"""
    
    def test_create_conta_pagar(self, auth_headers):
        """Test POST /api/admin/contas-pagar"""
        vencimento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        payload = {
            "descricao": f"TEST_Conta Pagar {uuid.uuid4().hex[:8]}",
            "valor": 1500.50,
            "vencimento": vencimento,
            "fornecedor": "Fornecedor Teste",
            "categoria": "Material",
            "observacoes": "Teste automatizado"
        }
        response = requests.post(f"{BASE_URL}/api/admin/contas-pagar", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["descricao"] == payload["descricao"]
        assert data["valor"] == payload["valor"]
        assert data["pago"] == False
        assert "id" in data
        
        # Store for cleanup
        TestContasPagar.created_id = data["id"]
        return data["id"]
    
    def test_get_contas_pagar(self, auth_headers):
        """Test GET /api/admin/contas-pagar"""
        response = requests.get(f"{BASE_URL}/api/admin/contas-pagar", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_conta_pagar(self, auth_headers):
        """Test PUT /api/admin/contas-pagar/{id}"""
        if not hasattr(TestContasPagar, 'created_id'):
            pytest.skip("No conta created to update")
        
        vencimento = (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")
        payload = {
            "descricao": "TEST_Conta Pagar Atualizada",
            "valor": 2000.00,
            "vencimento": vencimento,
            "fornecedor": "Fornecedor Atualizado",
            "categoria": "Serviço",
            "observacoes": "Atualizado"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/contas-pagar/{TestContasPagar.created_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["descricao"] == payload["descricao"]
        assert data["valor"] == payload["valor"]
    
    def test_marcar_conta_paga(self, auth_headers):
        """Test PATCH /api/admin/contas-pagar/{id}/pagar"""
        if not hasattr(TestContasPagar, 'created_id'):
            pytest.skip("No conta created to mark as paid")
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/contas-pagar/{TestContasPagar.created_id}/pagar",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify it was marked as paid
        get_response = requests.get(f"{BASE_URL}/api/admin/contas-pagar", headers=auth_headers)
        contas = get_response.json()
        conta = next((c for c in contas if c["id"] == TestContasPagar.created_id), None)
        if conta:
            assert conta["pago"] == True
    
    def test_delete_conta_pagar(self, auth_headers):
        """Test DELETE /api/admin/contas-pagar/{id}"""
        if not hasattr(TestContasPagar, 'created_id'):
            pytest.skip("No conta created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/contas-pagar/{TestContasPagar.created_id}",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestContasReceber:
    """Contas a Receber CRUD tests"""
    
    def test_create_conta_receber(self, auth_headers):
        """Test POST /api/admin/contas-receber"""
        vencimento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        payload = {
            "descricao": f"TEST_Conta Receber {uuid.uuid4().hex[:8]}",
            "valor": 3500.00,
            "vencimento": vencimento,
            "cliente": "Cliente Teste",
            "categoria": "Serviço",
            "observacoes": "Teste automatizado"
        }
        response = requests.post(f"{BASE_URL}/api/admin/contas-receber", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["descricao"] == payload["descricao"]
        assert data["valor"] == payload["valor"]
        assert data["recebido"] == False
        assert "id" in data
        
        TestContasReceber.created_id = data["id"]
    
    def test_get_contas_receber(self, auth_headers):
        """Test GET /api/admin/contas-receber"""
        response = requests.get(f"{BASE_URL}/api/admin/contas-receber", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_conta_receber(self, auth_headers):
        """Test PUT /api/admin/contas-receber/{id}"""
        if not hasattr(TestContasReceber, 'created_id'):
            pytest.skip("No conta created to update")
        
        vencimento = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        payload = {
            "descricao": "TEST_Conta Receber Atualizada",
            "valor": 4000.00,
            "vencimento": vencimento,
            "cliente": "Cliente Atualizado",
            "categoria": "Produto",
            "observacoes": "Atualizado"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/contas-receber/{TestContasReceber.created_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["descricao"] == payload["descricao"]
    
    def test_marcar_conta_recebida(self, auth_headers):
        """Test PATCH /api/admin/contas-receber/{id}/receber"""
        if not hasattr(TestContasReceber, 'created_id'):
            pytest.skip("No conta created to mark as received")
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/contas-receber/{TestContasReceber.created_id}/receber",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_delete_conta_receber(self, auth_headers):
        """Test DELETE /api/admin/contas-receber/{id}"""
        if not hasattr(TestContasReceber, 'created_id'):
            pytest.skip("No conta created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/contas-receber/{TestContasReceber.created_id}",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestFornecedores:
    """Fornecedores CRUD tests"""
    
    def test_create_fornecedor(self, auth_headers):
        """Test POST /api/admin/fornecedores"""
        payload = {
            "nome": f"TEST_Fornecedor {uuid.uuid4().hex[:8]}",
            "cnpj": "12.345.678/0001-90",
            "email": "fornecedor@teste.com",
            "telefone": "(11) 99999-9999",
            "endereco": "Rua Teste, 123",
            "cidade": "São Paulo",
            "estado": "SP",
            "observacoes": "Teste automatizado"
        }
        response = requests.post(f"{BASE_URL}/api/admin/fornecedores", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["nome"] == payload["nome"]
        assert data["cnpj"] == payload["cnpj"]
        assert "id" in data
        
        TestFornecedores.created_id = data["id"]
    
    def test_get_fornecedores(self, auth_headers):
        """Test GET /api/admin/fornecedores"""
        response = requests.get(f"{BASE_URL}/api/admin/fornecedores", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_fornecedor(self, auth_headers):
        """Test PUT /api/admin/fornecedores/{id}"""
        if not hasattr(TestFornecedores, 'created_id'):
            pytest.skip("No fornecedor created to update")
        
        payload = {
            "nome": "TEST_Fornecedor Atualizado",
            "cnpj": "98.765.432/0001-10",
            "email": "atualizado@teste.com",
            "telefone": "(11) 88888-8888",
            "endereco": "Rua Atualizada, 456",
            "cidade": "Rio de Janeiro",
            "estado": "RJ",
            "observacoes": "Atualizado"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/fornecedores/{TestFornecedores.created_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == payload["nome"]
    
    def test_delete_fornecedor(self, auth_headers):
        """Test DELETE /api/admin/fornecedores/{id}"""
        if not hasattr(TestFornecedores, 'created_id'):
            pytest.skip("No fornecedor created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/fornecedores/{TestFornecedores.created_id}",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestProdutos:
    """Produtos CRUD tests"""
    
    def test_create_produto(self, auth_headers):
        """Test POST /api/admin/produtos"""
        payload = {
            "nome": f"TEST_Produto {uuid.uuid4().hex[:8]}",
            "codigo": f"PROD-{uuid.uuid4().hex[:6]}",
            "descricao": "Produto de teste",
            "unidade": "UN",
            "preco_custo": 100.00,
            "preco_venda": 150.00,
            "categoria": "Material",
            "ncm": "12345678"
        }
        response = requests.post(f"{BASE_URL}/api/admin/produtos", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["nome"] == payload["nome"]
        assert data["preco_custo"] == payload["preco_custo"]
        assert "id" in data
        
        TestProdutos.created_id = data["id"]
    
    def test_get_produtos(self, auth_headers):
        """Test GET /api/admin/produtos"""
        response = requests.get(f"{BASE_URL}/api/admin/produtos", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_produto(self, auth_headers):
        """Test PUT /api/admin/produtos/{id}"""
        if not hasattr(TestProdutos, 'created_id'):
            pytest.skip("No produto created to update")
        
        payload = {
            "nome": "TEST_Produto Atualizado",
            "codigo": "PROD-UPDATED",
            "descricao": "Produto atualizado",
            "unidade": "KG",
            "preco_custo": 120.00,
            "preco_venda": 180.00,
            "categoria": "Serviço",
            "ncm": "87654321"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/produtos/{TestProdutos.created_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == payload["nome"]
    
    def test_delete_produto(self, auth_headers):
        """Test DELETE /api/admin/produtos/{id}"""
        if not hasattr(TestProdutos, 'created_id'):
            pytest.skip("No produto created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/produtos/{TestProdutos.created_id}",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestOrdensServico:
    """Ordens de Serviço CRUD tests"""
    
    def test_create_ordem_servico(self, auth_headers):
        """Test POST /api/admin/ordens-servico"""
        payload = {
            "numero": f"OS-{uuid.uuid4().hex[:8]}",
            "cliente": "Cliente Teste",
            "descricao": "Ordem de serviço de teste",
            "data_abertura": datetime.now().strftime("%Y-%m-%d"),
            "data_previsao": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
            "valor_total": 5000.00,
            "observacoes": "Teste automatizado"
        }
        response = requests.post(f"{BASE_URL}/api/admin/ordens-servico", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["numero"] == payload["numero"]
        assert data["status"] == "aberta"
        assert "id" in data
        
        TestOrdensServico.created_id = data["id"]
    
    def test_get_ordens_servico(self, auth_headers):
        """Test GET /api/admin/ordens-servico"""
        response = requests.get(f"{BASE_URL}/api/admin/ordens-servico", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_ordem_servico(self, auth_headers):
        """Test PUT /api/admin/ordens-servico/{id}"""
        if not hasattr(TestOrdensServico, 'created_id'):
            pytest.skip("No ordem created to update")
        
        payload = {
            "numero": "OS-UPDATED",
            "cliente": "Cliente Atualizado",
            "descricao": "Ordem atualizada",
            "data_abertura": datetime.now().strftime("%Y-%m-%d"),
            "data_previsao": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "valor_total": 7500.00,
            "observacoes": "Atualizado"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/ordens-servico/{TestOrdensServico.created_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["numero"] == payload["numero"]
    
    def test_update_ordem_status(self, auth_headers):
        """Test PATCH /api/admin/ordens-servico/{id}/status"""
        if not hasattr(TestOrdensServico, 'created_id'):
            pytest.skip("No ordem created to update status")
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/ordens-servico/{TestOrdensServico.created_id}/status",
            json={"status": "em_andamento"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_delete_ordem_servico(self, auth_headers):
        """Test DELETE /api/admin/ordens-servico/{id}"""
        if not hasattr(TestOrdensServico, 'created_id'):
            pytest.skip("No ordem created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/ordens-servico/{TestOrdensServico.created_id}",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestPlanoContas:
    """Plano de Contas CRUD tests"""
    
    def test_create_plano_conta(self, auth_headers):
        """Test POST /api/admin/plano-contas"""
        payload = {
            "codigo": f"1.{uuid.uuid4().hex[:4]}",
            "nome": f"TEST_Conta {uuid.uuid4().hex[:8]}",
            "tipo": "receita",
            "grupo": "Receitas Operacionais",
            "descricao": "Conta de teste"
        }
        response = requests.post(f"{BASE_URL}/api/admin/plano-contas", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["nome"] == payload["nome"]
        assert data["tipo"] == payload["tipo"]
        assert "id" in data
        
        TestPlanoContas.created_id = data["id"]
    
    def test_get_plano_contas(self, auth_headers):
        """Test GET /api/admin/plano-contas"""
        response = requests.get(f"{BASE_URL}/api/admin/plano-contas", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_plano_conta(self, auth_headers):
        """Test PUT /api/admin/plano-contas/{id}"""
        if not hasattr(TestPlanoContas, 'created_id'):
            pytest.skip("No conta created to update")
        
        payload = {
            "codigo": "2.0001",
            "nome": "TEST_Conta Atualizada",
            "tipo": "despesa",
            "grupo": "Despesas Operacionais",
            "descricao": "Conta atualizada"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/plano-contas/{TestPlanoContas.created_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == payload["nome"]
    
    def test_delete_plano_conta(self, auth_headers):
        """Test DELETE /api/admin/plano-contas/{id}"""
        if not hasattr(TestPlanoContas, 'created_id'):
            pytest.skip("No conta created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/plano-contas/{TestPlanoContas.created_id}",
            headers=auth_headers
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
