"""
Test suite for new Admin Module features:
- Dashboard Financeiro with tabs (Resumo, A Pagar, A Receber, Quitados)
- Dashboard badges (MÊS, ANO, GERAL)
- Centro de Custo CRUD
- Formas de Pagamento CRUD
- Ordens de Serviço with tipo_financeiro
- Dashboard OS values integration
- Plano de Contas with subcontas
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


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


# ============ DASHBOARD FINANCEIRO TESTS ============

class TestDashboardFinanceiro:
    """Test Dashboard Financeiro with tabs and badges"""
    
    def test_dashboard_returns_all_tabs_data(self, auth_headers):
        """Test GET /api/admin/dashboard returns data for all tabs"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify main structure
        assert "stats" in data
        assert "aPagar" in data
        assert "aReceber" in data
        assert "quitados" in data
        assert "contasProximas" in data
    
    def test_dashboard_a_pagar_has_badges(self, auth_headers):
        """Test aPagar section has MÊS, ANO, GERAL values"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        aPagar = data["aPagar"]
        assert "total" in aPagar  # GERAL
        assert "mes" in aPagar    # MÊS
        assert "ano" in aPagar    # ANO
        assert "vencidas" in aPagar
        assert "osValor" in aPagar  # OS values
        
        # Values should be numbers
        assert isinstance(aPagar["total"], (int, float))
        assert isinstance(aPagar["mes"], (int, float))
        assert isinstance(aPagar["ano"], (int, float))
    
    def test_dashboard_a_receber_has_badges(self, auth_headers):
        """Test aReceber section has MÊS, ANO, GERAL values"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        aReceber = data["aReceber"]
        assert "total" in aReceber  # GERAL
        assert "mes" in aReceber    # MÊS
        assert "ano" in aReceber    # ANO
        assert "vencidas" in aReceber
        assert "osValor" in aReceber  # OS values
        
        # Values should be numbers
        assert isinstance(aReceber["total"], (int, float))
        assert isinstance(aReceber["mes"], (int, float))
        assert isinstance(aReceber["ano"], (int, float))
    
    def test_dashboard_quitados_structure(self, auth_headers):
        """Test quitados section has pagar and receber with MÊS, ANO, GERAL"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        quitados = data["quitados"]
        assert "pagar" in quitados
        assert "receber" in quitados
        
        # Pagar quitados
        assert "total" in quitados["pagar"]
        assert "mes" in quitados["pagar"]
        assert "ano" in quitados["pagar"]
        
        # Receber quitados
        assert "total" in quitados["receber"]
        assert "mes" in quitados["receber"]
        assert "ano" in quitados["receber"]


# ============ CENTRO DE CUSTO CRUD TESTS ============

class TestCentroCusto:
    """Test Centro de Custo CRUD operations"""
    created_id = None
    
    def test_create_centro_custo(self, auth_headers):
        """Test POST /api/admin/centros-custo"""
        payload = {
            "codigo": f"CC-{uuid.uuid4().hex[:6]}",
            "nome": f"TEST_Centro Custo {uuid.uuid4().hex[:8]}",
            "descricao": "Centro de custo de teste",
            "status": "ativo"
        }
        response = requests.post(f"{BASE_URL}/api/admin/centros-custo", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["nome"] == payload["nome"]
        assert data["codigo"] == payload["codigo"]
        assert data["status"] == "ativo"
        assert "id" in data
        
        TestCentroCusto.created_id = data["id"]
    
    def test_get_centros_custo(self, auth_headers):
        """Test GET /api/admin/centros-custo"""
        response = requests.get(f"{BASE_URL}/api/admin/centros-custo", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_centro_custo(self, auth_headers):
        """Test PUT /api/admin/centros-custo/{id}"""
        if not TestCentroCusto.created_id:
            pytest.skip("No centro created to update")
        
        payload = {
            "codigo": "CC-UPDATED",
            "nome": "TEST_Centro Custo Atualizado",
            "descricao": "Descrição atualizada",
            "status": "inativo"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/centros-custo/{TestCentroCusto.created_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == payload["nome"]
        assert data["status"] == "inativo"
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/admin/centros-custo", headers=auth_headers)
        centros = get_response.json()
        centro = next((c for c in centros if c["id"] == TestCentroCusto.created_id), None)
        assert centro is not None
        assert centro["nome"] == payload["nome"]
    
    def test_delete_centro_custo(self, auth_headers):
        """Test DELETE /api/admin/centros-custo/{id}"""
        if not TestCentroCusto.created_id:
            pytest.skip("No centro created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/centros-custo/{TestCentroCusto.created_id}",
            headers=auth_headers
        )
        assert response.status_code == 200


# ============ FORMAS DE PAGAMENTO CRUD TESTS ============

class TestFormasPagamento:
    """Test Formas de Pagamento CRUD operations"""
    created_id = None
    
    def test_create_forma_pagamento(self, auth_headers):
        """Test POST /api/admin/formas-pagamento"""
        payload = {
            "codigo": f"FP-{uuid.uuid4().hex[:6]}",
            "nome": f"TEST_Forma Pagamento {uuid.uuid4().hex[:8]}",
            "tipo": "pix",
            "taxa": 1.5,
            "prazo_recebimento": 1,
            "conta_bancaria": "Banco Teste - Ag 0001 CC 12345-6",
            "ativo": True,
            "observacoes": "Forma de pagamento de teste"
        }
        response = requests.post(f"{BASE_URL}/api/admin/formas-pagamento", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["nome"] == payload["nome"]
        assert data["tipo"] == "pix"
        assert data["taxa"] == 1.5
        assert data["prazo_recebimento"] == 1
        assert data["ativo"] == True
        assert "id" in data
        
        TestFormasPagamento.created_id = data["id"]
    
    def test_get_formas_pagamento(self, auth_headers):
        """Test GET /api/admin/formas-pagamento"""
        response = requests.get(f"{BASE_URL}/api/admin/formas-pagamento", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_formas_pagamento_ativas(self, auth_headers):
        """Test GET /api/admin/formas-pagamento?ativo=true"""
        response = requests.get(f"{BASE_URL}/api/admin/formas-pagamento?ativo=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned should be active
        for forma in data:
            assert forma.get("ativo") != False
    
    def test_update_forma_pagamento(self, auth_headers):
        """Test PUT /api/admin/formas-pagamento/{id}"""
        if not TestFormasPagamento.created_id:
            pytest.skip("No forma created to update")
        
        payload = {
            "codigo": "FP-UPDATED",
            "nome": "TEST_Forma Pagamento Atualizada",
            "tipo": "cartao_credito",
            "taxa": 2.5,
            "prazo_recebimento": 30,
            "conta_bancaria": "Banco Atualizado",
            "ativo": False,
            "observacoes": "Atualizado"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/formas-pagamento/{TestFormasPagamento.created_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == payload["nome"]
        assert data["tipo"] == "cartao_credito"
        assert data["taxa"] == 2.5
        assert data["ativo"] == False
    
    def test_delete_forma_pagamento(self, auth_headers):
        """Test DELETE /api/admin/formas-pagamento/{id}"""
        if not TestFormasPagamento.created_id:
            pytest.skip("No forma created to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/formas-pagamento/{TestFormasPagamento.created_id}",
            headers=auth_headers
        )
        assert response.status_code == 200


# ============ ORDENS DE SERVIÇO COM TIPO FINANCEIRO TESTS ============

class TestOrdensServicoTipoFinanceiro:
    """Test Ordens de Serviço with tipo_financeiro field"""
    os_a_pagar_id = None
    os_a_receber_id = None
    
    def test_create_os_a_pagar(self, auth_headers):
        """Test creating OS with tipo_financeiro = a_pagar"""
        payload = {
            "numero_contrato": f"CONT-{uuid.uuid4().hex[:6]}",
            "cliente_nome": "Cliente Teste A Pagar",
            "descricao": f"TEST_OS A Pagar {uuid.uuid4().hex[:8]}",
            "data_abertura": datetime.now().strftime("%Y-%m-%d"),
            "data_previsao_entrega": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "valor_total": 5000.00,
            "tipo_financeiro": "a_pagar"
        }
        response = requests.post(f"{BASE_URL}/api/admin/ordens-servico", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["tipo_financeiro"] == "a_pagar"
        assert data["valor_total"] == 5000.00
        assert "id" in data
        
        TestOrdensServicoTipoFinanceiro.os_a_pagar_id = data["id"]
    
    def test_create_os_a_receber(self, auth_headers):
        """Test creating OS with tipo_financeiro = a_receber"""
        payload = {
            "numero_contrato": f"CONT-{uuid.uuid4().hex[:6]}",
            "cliente_nome": "Cliente Teste A Receber",
            "descricao": f"TEST_OS A Receber {uuid.uuid4().hex[:8]}",
            "data_abertura": datetime.now().strftime("%Y-%m-%d"),
            "data_previsao_entrega": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "valor_total": 8000.00,
            "tipo_financeiro": "a_receber"
        }
        response = requests.post(f"{BASE_URL}/api/admin/ordens-servico", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["tipo_financeiro"] == "a_receber"
        assert data["valor_total"] == 8000.00
        
        TestOrdensServicoTipoFinanceiro.os_a_receber_id = data["id"]
    
    def test_dashboard_shows_os_values(self, auth_headers):
        """Test dashboard includes OS values in aPagar and aReceber"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # OS values should be present
        assert "osValor" in data["aPagar"]
        assert "osValor" in data["aReceber"]
        
        # Values should be >= 0 (we created OS with values)
        assert data["aPagar"]["osValor"] >= 0
        assert data["aReceber"]["osValor"] >= 0
    
    def test_cleanup_os_a_pagar(self, auth_headers):
        """Cleanup: Delete OS a pagar"""
        if TestOrdensServicoTipoFinanceiro.os_a_pagar_id:
            response = requests.delete(
                f"{BASE_URL}/api/admin/ordens-servico/{TestOrdensServicoTipoFinanceiro.os_a_pagar_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
    
    def test_cleanup_os_a_receber(self, auth_headers):
        """Cleanup: Delete OS a receber"""
        if TestOrdensServicoTipoFinanceiro.os_a_receber_id:
            response = requests.delete(
                f"{BASE_URL}/api/admin/ordens-servico/{TestOrdensServicoTipoFinanceiro.os_a_receber_id}",
                headers=auth_headers
            )
            assert response.status_code == 200


# ============ PLANO DE CONTAS COM SUBCONTAS TESTS ============

class TestPlanoContasSubcontas:
    """Test Plano de Contas with subcontas (2 levels)"""
    pai_id = None
    subconta_id = None
    
    def test_create_conta_pai(self, auth_headers):
        """Test creating a parent account (nivel 1)"""
        payload = {
            "codigo": f"1.{uuid.uuid4().hex[:4]}",
            "nome": f"TEST_Conta Pai {uuid.uuid4().hex[:8]}",
            "tipo": "despesa",
            "nivel": 1,
            "descricao": "Conta pai de teste"
        }
        response = requests.post(f"{BASE_URL}/api/admin/plano-contas", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["nome"] == payload["nome"]
        assert data["nivel"] == 1
        assert "id" in data
        
        TestPlanoContasSubcontas.pai_id = data["id"]
    
    def test_create_subconta(self, auth_headers):
        """Test creating a subconta (nivel 2) linked to parent"""
        if not TestPlanoContasSubcontas.pai_id:
            pytest.skip("No parent account created")
        
        payload = {
            "codigo": f"1.1.{uuid.uuid4().hex[:4]}",
            "nome": f"TEST_Subconta {uuid.uuid4().hex[:8]}",
            "tipo": "despesa",
            "nivel": 2,
            "pai_id": TestPlanoContasSubcontas.pai_id,
            "descricao": "Subconta de teste"
        }
        response = requests.post(f"{BASE_URL}/api/admin/plano-contas", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["nome"] == payload["nome"]
        assert data["nivel"] == 2
        assert data["pai_id"] == TestPlanoContasSubcontas.pai_id
        
        TestPlanoContasSubcontas.subconta_id = data["id"]
    
    def test_get_plano_contas_with_subcontas(self, auth_headers):
        """Test GET returns accounts with pai_nome for subcontas"""
        response = requests.get(f"{BASE_URL}/api/admin/plano-contas", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Find our subconta
        if TestPlanoContasSubcontas.subconta_id:
            subconta = next((c for c in data if c["id"] == TestPlanoContasSubcontas.subconta_id), None)
            if subconta:
                assert subconta.get("pai_id") == TestPlanoContasSubcontas.pai_id
    
    def test_cannot_delete_pai_with_subcontas(self, auth_headers):
        """Test that parent account with subcontas cannot be deleted"""
        if not TestPlanoContasSubcontas.pai_id or not TestPlanoContasSubcontas.subconta_id:
            pytest.skip("No parent or subconta created")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/plano-contas/{TestPlanoContasSubcontas.pai_id}",
            headers=auth_headers
        )
        # Should fail because it has subcontas
        assert response.status_code == 400
    
    def test_cleanup_subconta(self, auth_headers):
        """Cleanup: Delete subconta first"""
        if TestPlanoContasSubcontas.subconta_id:
            response = requests.delete(
                f"{BASE_URL}/api/admin/plano-contas/{TestPlanoContasSubcontas.subconta_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
    
    def test_cleanup_pai(self, auth_headers):
        """Cleanup: Delete parent account after subconta is deleted"""
        if TestPlanoContasSubcontas.pai_id:
            response = requests.delete(
                f"{BASE_URL}/api/admin/plano-contas/{TestPlanoContasSubcontas.pai_id}",
                headers=auth_headers
            )
            assert response.status_code == 200


# ============ CONTAS A PAGAR - FORMAS DE PAGAMENTO INTEGRATION ============

class TestContasPagarFormasPagamento:
    """Test that Contas a Pagar loads formas de pagamento from database"""
    forma_id = None
    
    def test_create_forma_for_integration(self, auth_headers):
        """Create a forma de pagamento for integration test"""
        payload = {
            "codigo": "FP-INT",
            "nome": "TEST_PIX Integração",
            "tipo": "pix",
            "taxa": 0,
            "prazo_recebimento": 0,
            "ativo": True
        }
        response = requests.post(f"{BASE_URL}/api/admin/formas-pagamento", json=payload, headers=auth_headers)
        assert response.status_code == 200
        TestContasPagarFormasPagamento.forma_id = response.json()["id"]
    
    def test_formas_pagamento_available_for_contas(self, auth_headers):
        """Test that formas de pagamento are available for contas a pagar"""
        response = requests.get(f"{BASE_URL}/api/admin/formas-pagamento?ativo=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least our test forma
        assert len(data) >= 1
    
    def test_cleanup_forma(self, auth_headers):
        """Cleanup: Delete test forma"""
        if TestContasPagarFormasPagamento.forma_id:
            response = requests.delete(
                f"{BASE_URL}/api/admin/formas-pagamento/{TestContasPagarFormasPagamento.forma_id}",
                headers=auth_headers
            )
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
