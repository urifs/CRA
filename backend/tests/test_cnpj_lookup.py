"""
Test CNPJ Lookup via BrasilAPI
Tests the /api/consulta/cnpj/{cnpj} endpoint that fetches company data from Receita Federal
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCNPJLookup:
    """CNPJ Lookup endpoint tests using BrasilAPI"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_cnpj_lookup_banco_do_brasil(self):
        """Test CNPJ lookup for Banco do Brasil (00000000000191)"""
        cnpj = "00000000000191"
        response = requests.get(
            f"{BASE_URL}/api/consulta/cnpj/{cnpj}",
            headers=self.headers
        )
        
        # Status code assertion
        assert response.status_code == 200, f"CNPJ lookup failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        
        company_data = data["data"]
        
        # Verify company name
        assert company_data["razao_social"] == "BANCO DO BRASIL SA"
        assert company_data["nome_fantasia"] == "DIRECAO GERAL"
        
        # Verify CNPJ
        assert company_data["cnpj"] == cnpj
        
        # Verify address fields are populated
        assert company_data["cidade"] == "BRASILIA"
        assert company_data["uf"] == "DF"
        assert company_data["bairro"] == "ASA NORTE"
        assert company_data["cep"] == "70040912"
        
        # Verify phone is populated
        assert company_data["telefone"] == "6134939002"
        
        print(f"CNPJ lookup successful for {cnpj}")
        print(f"Company: {company_data['razao_social']}")
        print(f"Location: {company_data['cidade']}/{company_data['uf']}")
    
    def test_cnpj_lookup_invalid_cnpj(self):
        """Test CNPJ lookup with invalid CNPJ (less than 14 digits)"""
        cnpj = "123456"  # Invalid - less than 14 digits
        response = requests.get(
            f"{BASE_URL}/api/consulta/cnpj/{cnpj}",
            headers=self.headers
        )
        
        # Should return 400 for invalid CNPJ
        assert response.status_code == 400
        assert "14 dígitos" in response.json().get("detail", "")
    
    def test_cnpj_lookup_not_found(self):
        """Test CNPJ lookup with non-existent CNPJ"""
        cnpj = "99999999999999"  # Non-existent CNPJ
        response = requests.get(
            f"{BASE_URL}/api/consulta/cnpj/{cnpj}",
            headers=self.headers
        )
        
        # Should return 404 for non-existent CNPJ
        assert response.status_code == 404
    
    def test_cnpj_lookup_without_auth(self):
        """Test CNPJ lookup without authentication"""
        cnpj = "00000000000191"
        response = requests.get(
            f"{BASE_URL}/api/consulta/cnpj/{cnpj}"
            # No auth headers
        )
        
        # Should return 401/403 for unauthenticated request
        assert response.status_code in [401, 403]
    
    def test_cnpj_lookup_with_formatting(self):
        """Test CNPJ lookup with formatted CNPJ (with dots and dashes)"""
        cnpj = "00.000.000/0001-91"  # Formatted CNPJ
        response = requests.get(
            f"{BASE_URL}/api/consulta/cnpj/{cnpj}",
            headers=self.headers
        )
        
        # Should work - backend strips non-numeric characters
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["razao_social"] == "BANCO DO BRASIL SA"


class TestCEPLookup:
    """CEP Lookup endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_cep_lookup_valid(self):
        """Test CEP lookup for valid CEP"""
        cep = "01310100"  # Av. Paulista, São Paulo
        response = requests.get(
            f"{BASE_URL}/api/consulta/cep/{cep}",
            headers=self.headers
        )
        
        # Status code assertion
        assert response.status_code == 200, f"CEP lookup failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        
        address_data = data["data"]
        assert address_data["uf"] == "SP"
        assert "São Paulo" in address_data["cidade"] or "SAO PAULO" in address_data["cidade"].upper()
        
        print(f"CEP lookup successful for {cep}")
        print(f"Address: {address_data.get('endereco', '')}, {address_data['cidade']}/{address_data['uf']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
