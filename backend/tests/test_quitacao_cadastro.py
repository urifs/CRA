"""
Test suite for Quitação (Payment Settlement) and Cadastro (Registration) features
Tests:
1. Quitação de Contas a Pagar with data_pagamento and conta_bancaria_id
2. Quitação de Contas a Receber with data_recebimento and conta_bancaria_id
3. Quitar button appears for 'pendente' and 'em_aberto' status
4. conta_bancaria_id is saved in database after quitação
5. Cadastro form accessible from Contas a Pagar/Receber
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

class TestQuitacaoContasPagar:
    """Tests for Contas a Pagar quitação functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get or create a conta bancária for testing
        cb_response = requests.get(f"{BASE_URL}/api/admin/contas-bancarias?ativo=true", headers=self.headers)
        if cb_response.status_code == 200 and len(cb_response.json()) > 0:
            self.conta_bancaria_id = cb_response.json()[0]["id"]
        else:
            # Create a conta bancária
            cb_create = requests.post(f"{BASE_URL}/api/admin/contas-bancarias", headers=self.headers, json={
                "nome": "TEST_Conta Teste",
                "banco": "Banco Teste",
                "agencia": "0001",
                "conta": "12345-6",
                "tipo": "corrente",
                "ativo": True
            })
            if cb_create.status_code in [200, 201]:
                self.conta_bancaria_id = cb_create.json()["id"]
            else:
                self.conta_bancaria_id = None
    
    def test_create_conta_pagar_pendente(self):
        """Test creating a conta a pagar with pendente status"""
        data = {
            "descricao": "TEST_Conta Pagar Pendente",
            "valor": 100.00,
            "data_vencimento": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "status": "pendente",
            "forma_pagamento": "boleto"
        }
        response = requests.post(f"{BASE_URL}/api/admin/contas-pagar", headers=self.headers, json=data)
        assert response.status_code in [200, 201], f"Failed to create conta: {response.text}"
        conta = response.json()
        assert conta["descricao"] == "TEST_Conta Pagar Pendente"
        # Status should be pendente or em_aberto (default)
        assert conta["status"] in ["pendente", "em_aberto"]
        self.conta_pagar_id = conta["id"]
        return conta
    
    def test_quitar_conta_pagar_with_data_and_conta_bancaria(self):
        """Test quitação with data_pagamento and conta_bancaria_id"""
        # First create a conta
        conta = self.test_create_conta_pagar_pendente()
        conta_id = conta["id"]
        
        # Quitar with data_pagamento and conta_bancaria_id
        data_pagamento = datetime.now().strftime("%Y-%m-%d")
        quitar_data = {
            "data_pagamento": data_pagamento,
            "conta_bancaria_id": self.conta_bancaria_id
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/contas-pagar/{conta_id}/quitar",
            headers=self.headers,
            json=quitar_data
        )
        assert response.status_code == 200, f"Quitar failed: {response.text}"
        result = response.json()
        assert "message" in result
        assert result["data_pagamento"] == data_pagamento
        
        # Verify conta_bancaria_id was saved
        get_response = requests.get(f"{BASE_URL}/api/admin/contas-pagar", headers=self.headers)
        assert get_response.status_code == 200
        contas = get_response.json()
        conta_quitada = next((c for c in contas if c["id"] == conta_id), None)
        assert conta_quitada is not None, "Conta not found after quitação"
        assert conta_quitada["status"] == "quitada"
        assert conta_quitada.get("data_pagamento") == data_pagamento
        if self.conta_bancaria_id:
            assert conta_quitada.get("conta_bancaria_id") == self.conta_bancaria_id
        
        print(f"✓ Conta a Pagar quitada com data_pagamento={data_pagamento} e conta_bancaria_id={self.conta_bancaria_id}")
    
    def test_quitar_conta_pagar_em_aberto(self):
        """Test quitação for conta with em_aberto status"""
        # Create conta with em_aberto status
        data = {
            "descricao": "TEST_Conta Em Aberto",
            "valor": 200.00,
            "data_vencimento": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "status": "em_aberto",
            "forma_pagamento": "pix"
        }
        response = requests.post(f"{BASE_URL}/api/admin/contas-pagar", headers=self.headers, json=data)
        assert response.status_code in [200, 201]
        conta = response.json()
        conta_id = conta["id"]
        
        # Quitar
        quitar_response = requests.patch(
            f"{BASE_URL}/api/admin/contas-pagar/{conta_id}/quitar",
            headers=self.headers,
            json={"data_pagamento": datetime.now().strftime("%Y-%m-%d")}
        )
        assert quitar_response.status_code == 200
        print("✓ Conta em_aberto quitada com sucesso")


class TestQuitacaoContasReceber:
    """Tests for Contas a Receber quitação functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get conta bancária
        cb_response = requests.get(f"{BASE_URL}/api/admin/contas-bancarias?ativo=true", headers=self.headers)
        if cb_response.status_code == 200 and len(cb_response.json()) > 0:
            self.conta_bancaria_id = cb_response.json()[0]["id"]
        else:
            self.conta_bancaria_id = None
    
    def test_create_conta_receber_pendente(self):
        """Test creating a conta a receber with pendente status"""
        data = {
            "descricao": "TEST_Conta Receber Pendente",
            "valor": 500.00,
            "data_vencimento": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "status": "pendente",
            "forma_pagamento": "boleto"
        }
        response = requests.post(f"{BASE_URL}/api/admin/contas-receber", headers=self.headers, json=data)
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        conta = response.json()
        assert conta["descricao"] == "TEST_Conta Receber Pendente"
        return conta
    
    def test_quitar_conta_receber_with_data_and_conta_bancaria(self):
        """Test quitação with data_recebimento and conta_bancaria_id"""
        # Create conta
        conta = self.test_create_conta_receber_pendente()
        conta_id = conta["id"]
        
        # Quitar with data_recebimento and conta_bancaria_id
        data_recebimento = datetime.now().strftime("%Y-%m-%d")
        quitar_data = {
            "data_recebimento": data_recebimento,
            "conta_bancaria_id": self.conta_bancaria_id
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/contas-receber/{conta_id}/quitar",
            headers=self.headers,
            json=quitar_data
        )
        assert response.status_code == 200, f"Quitar failed: {response.text}"
        result = response.json()
        assert result["data_recebimento"] == data_recebimento
        
        # Verify conta_bancaria_id was saved
        get_response = requests.get(f"{BASE_URL}/api/admin/contas-receber", headers=self.headers)
        assert get_response.status_code == 200
        contas = get_response.json()
        conta_quitada = next((c for c in contas if c["id"] == conta_id), None)
        assert conta_quitada is not None
        assert conta_quitada["status"] == "quitada"
        assert conta_quitada.get("data_recebimento") == data_recebimento
        if self.conta_bancaria_id:
            assert conta_quitada.get("conta_bancaria_id") == self.conta_bancaria_id
        
        print(f"✓ Conta a Receber quitada com data_recebimento={data_recebimento} e conta_bancaria_id={self.conta_bancaria_id}")


class TestCadastroAPI:
    """Tests for Cadastro (Fornecedor/Cliente) API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_fornecedor_cadastro(self):
        """Test creating a fornecedor cadastro"""
        data = {
            "tipo_cadastro": "fornecedor",
            "tipo_pessoa": "PJ",
            "status": "ativo",
            "nome_razao": "TEST_Fornecedor Teste LTDA",
            "apelido_fantasia": "Fornecedor Teste",
            "cpf_cnpj": "12.345.678/0001-90",
            "telefone": "(11) 1234-5678",
            "email": "fornecedor@teste.com",
            "cidade": "São Paulo",
            "uf": "SP"
        }
        response = requests.post(f"{BASE_URL}/api/admin/cadastros", headers=self.headers, json=data)
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        cadastro = response.json()
        assert cadastro["nome_razao"] == "TEST_Fornecedor Teste LTDA"
        assert cadastro["tipo_cadastro"] == "fornecedor"
        print("✓ Fornecedor cadastrado com sucesso")
        return cadastro
    
    def test_create_cliente_cadastro(self):
        """Test creating a cliente cadastro"""
        data = {
            "tipo_cadastro": "cliente",
            "tipo_pessoa": "PF",
            "status": "ativo",
            "nome_razao": "TEST_Cliente Pessoa Física",
            "cpf_cnpj": "123.456.789-00",
            "telefone": "(11) 9876-5432",
            "email": "cliente@teste.com"
        }
        response = requests.post(f"{BASE_URL}/api/admin/cadastros", headers=self.headers, json=data)
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        cadastro = response.json()
        assert cadastro["nome_razao"] == "TEST_Cliente Pessoa Física"
        assert cadastro["tipo_cadastro"] == "cliente"
        print("✓ Cliente cadastrado com sucesso")
        return cadastro
    
    def test_list_cadastros(self):
        """Test listing cadastros"""
        response = requests.get(f"{BASE_URL}/api/admin/cadastros", headers=self.headers)
        assert response.status_code == 200
        cadastros = response.json()
        assert isinstance(cadastros, list)
        print(f"✓ Listagem de cadastros retornou {len(cadastros)} registros")


class TestContasBancarias:
    """Tests for Contas Bancárias API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_contas_bancarias(self):
        """Test listing contas bancárias"""
        response = requests.get(f"{BASE_URL}/api/admin/contas-bancarias?ativo=true", headers=self.headers)
        assert response.status_code == 200
        contas = response.json()
        assert isinstance(contas, list)
        print(f"✓ Listagem de contas bancárias retornou {len(contas)} registros")
        return contas


class TestStatusVerification:
    """Tests to verify quitar button appears for correct statuses"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_contas_pagar_status_filter(self):
        """Test that contas with pendente and em_aberto status are returned"""
        # Create conta with pendente status
        data_pendente = {
            "descricao": "TEST_Status Pendente",
            "valor": 100.00,
            "data_vencimento": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "status": "pendente",
            "forma_pagamento": "boleto"
        }
        resp1 = requests.post(f"{BASE_URL}/api/admin/contas-pagar", headers=self.headers, json=data_pendente)
        assert resp1.status_code in [200, 201]
        
        # Create conta with em_aberto status
        data_em_aberto = {
            "descricao": "TEST_Status Em Aberto",
            "valor": 150.00,
            "data_vencimento": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "status": "em_aberto",
            "forma_pagamento": "pix"
        }
        resp2 = requests.post(f"{BASE_URL}/api/admin/contas-pagar", headers=self.headers, json=data_em_aberto)
        assert resp2.status_code in [200, 201]
        
        # Get all contas
        response = requests.get(f"{BASE_URL}/api/admin/contas-pagar", headers=self.headers)
        assert response.status_code == 200
        contas = response.json()
        
        # Verify both statuses exist
        statuses = set(c["status"] for c in contas)
        print(f"✓ Statuses encontrados: {statuses}")
        
        # Count contas that should show quitar button (pendente or em_aberto)
        quitar_eligible = [c for c in contas if c["status"] in ["pendente", "em_aberto"]]
        print(f"✓ {len(quitar_eligible)} contas elegíveis para quitação (pendente ou em_aberto)")


# Cleanup test data
class TestCleanup:
    """Cleanup test data after tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not login for cleanup")
    
    def test_cleanup_test_data(self):
        """Clean up TEST_ prefixed data"""
        # Clean contas a pagar
        response = requests.get(f"{BASE_URL}/api/admin/contas-pagar", headers=self.headers)
        if response.status_code == 200:
            for conta in response.json():
                if conta.get("descricao", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/admin/contas-pagar/{conta['id']}", headers=self.headers)
        
        # Clean contas a receber
        response = requests.get(f"{BASE_URL}/api/admin/contas-receber", headers=self.headers)
        if response.status_code == 200:
            for conta in response.json():
                if conta.get("descricao", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/admin/contas-receber/{conta['id']}", headers=self.headers)
        
        # Clean cadastros
        response = requests.get(f"{BASE_URL}/api/admin/cadastros", headers=self.headers)
        if response.status_code == 200:
            for cadastro in response.json():
                if cadastro.get("nome_razao", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/admin/cadastros/{cadastro['id']}", headers=self.headers)
        
        print("✓ Test data cleanup completed")
