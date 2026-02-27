"""
Test suite for RH EPI (Equipamentos de Proteção Individual) module
Tests CBO search, EPI consultation, and related endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCBOSearch:
    """Tests for /api/rh/epi/cbo/buscar endpoint"""
    
    def test_search_cbo_by_code(self):
        """Test searching CBO by code (e.g., 7152-10 for Pedreiro)"""
        response = requests.get(f"{BASE_URL}/api/rh/epi/cbo/buscar?q=7152-10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify first result is Pedreiro
        first_result = data[0]
        assert "codigo" in first_result
        assert "ocupacao" in first_result
        assert "7152-10" in first_result["codigo"]
        assert "Pedreiro" in first_result["ocupacao"]
    
    def test_search_cbo_by_name(self):
        """Test searching CBO by occupation name"""
        response = requests.get(f"{BASE_URL}/api/rh/epi/cbo/buscar?q=pedreiro")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify results contain pedreiro
        found_pedreiro = any("pedreiro" in item["ocupacao"].lower() for item in data)
        assert found_pedreiro, "Should find occupations containing 'pedreiro'"
    
    def test_search_cbo_by_partial_code(self):
        """Test searching CBO by partial code"""
        response = requests.get(f"{BASE_URL}/api/rh/epi/cbo/buscar?q=7152")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # All results should have codes starting with 7152
        for item in data:
            assert item["codigo"].replace("-", "").startswith("7152")
    
    def test_search_cbo_soldador(self):
        """Test searching for Soldador occupation"""
        response = requests.get(f"{BASE_URL}/api/rh/epi/cbo/buscar?q=soldador")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert any("soldador" in item["ocupacao"].lower() for item in data)
    
    def test_search_cbo_eletricista(self):
        """Test searching for Eletricista occupation"""
        response = requests.get(f"{BASE_URL}/api/rh/epi/cbo/buscar?q=eletricista")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert any("eletricista" in item["ocupacao"].lower() for item in data)
    
    def test_search_cbo_no_results(self):
        """Test searching for non-existent occupation"""
        response = requests.get(f"{BASE_URL}/api/rh/epi/cbo/buscar?q=xyznonexistent123")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestConsultarEPIsCBO:
    """Tests for /api/rh/epi/consultar-epis-cbo endpoint"""
    
    def test_consultar_epis_pedreiro(self):
        """Test consulting EPIs for Pedreiro (CBO 7152-10) - should use local database"""
        response = requests.post(
            f"{BASE_URL}/api/rh/epi/consultar-epis-cbo",
            json={"codigo_cbo": "7152-10", "ocupacao": "Pedreiro"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "epis" in data
        assert "mapa_risco" in data
        assert isinstance(data["epis"], list)
        assert len(data["epis"]) > 0
        
        # Verify EPI structure
        first_epi = data["epis"][0]
        assert "nome" in first_epi
        assert "ca" in first_epi
        assert "validade_meses" in first_epi
        assert "prioridade" in first_epi
        
        # Verify source is local database
        assert data.get("fonte") == "CBO_DATABASE"
    
    def test_consultar_epis_soldador(self):
        """Test consulting EPIs for Soldador (CBO 7241-10)"""
        response = requests.post(
            f"{BASE_URL}/api/rh/epi/consultar-epis-cbo",
            json={"codigo_cbo": "7241-10", "ocupacao": "Soldador"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "epis" in data
        assert len(data["epis"]) > 0
        
        # Soldador should have specific EPIs like welding mask
        epi_names = [epi["nome"].lower() for epi in data["epis"]]
        # Check for welding-related EPIs
        has_welding_epi = any("solda" in name or "raspa" in name for name in epi_names)
        assert has_welding_epi, f"Soldador should have welding EPIs. Found: {epi_names}"
    
    def test_consultar_epis_eletricista(self):
        """Test consulting EPIs for Eletricista (CBO 7156-10)"""
        response = requests.post(
            f"{BASE_URL}/api/rh/epi/consultar-epis-cbo",
            json={"codigo_cbo": "7156-10", "ocupacao": "Eletricista de instalações prediais"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "epis" in data
        assert len(data["epis"]) > 0
        
        # Eletricista should have insulating EPIs
        epi_names = [epi["nome"].lower() for epi in data["epis"]]
        has_insulating_epi = any("isolante" in name for name in epi_names)
        assert has_insulating_epi, f"Eletricista should have insulating EPIs. Found: {epi_names}"
    
    def test_consultar_epis_mapa_risco(self):
        """Test that mapa_risco is properly returned"""
        response = requests.post(
            f"{BASE_URL}/api/rh/epi/consultar-epis-cbo",
            json={"codigo_cbo": "7152-10", "ocupacao": "Pedreiro"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "mapa_risco" in data
        assert isinstance(data["mapa_risco"], list)
        assert len(data["mapa_risco"]) > 0
        
        # Verify mapa_risco structure
        first_risk = data["mapa_risco"][0]
        assert "risco" in first_risk
        assert "prioridade" in first_risk
        assert "epi_recomendado" in first_risk
    
    def test_consultar_epis_unknown_cbo_uses_ai_or_fallback(self):
        """Test consulting EPIs for unknown CBO - should use AI or fallback"""
        response = requests.post(
            f"{BASE_URL}/api/rh/epi/consultar-epis-cbo",
            json={"codigo_cbo": "9999-99", "ocupacao": "Ocupação Desconhecida"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "epis" in data
        assert len(data["epis"]) > 0
        
        # Should be from AI or FALLBACK
        assert data.get("fonte") in ["IA", "FALLBACK"], f"Unknown CBO should use AI or FALLBACK. Got: {data.get('fonte')}"


class TestRHDashboard:
    """Tests for /api/rh/dashboard endpoint"""
    
    def test_dashboard_returns_stats(self):
        """Test that RH dashboard returns expected statistics"""
        response = requests.get(f"{BASE_URL}/api/rh/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify expected fields
        assert "total_funcionarios" in data
        assert "funcionarios_ativos" in data
        assert "funcionarios_ferias" in data
        assert "funcionarios_afastados" in data
        assert "total_folha" in data
        assert "aniversariantes_mes" in data
        assert "alertas_ferias" in data
        assert "alertas_epi" in data
        assert "ponto_hoje" in data
        
        # Verify types
        assert isinstance(data["total_funcionarios"], int)
        assert isinstance(data["aniversariantes_mes"], list)
        assert isinstance(data["ponto_hoje"], dict)


class TestRHFuncionarios:
    """Tests for /api/rh/funcionarios endpoints"""
    
    def test_list_funcionarios(self):
        """Test listing funcionarios"""
        response = requests.get(f"{BASE_URL}/api/rh/funcionarios")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_funcionarios_ativos(self):
        """Test listing active funcionarios"""
        response = requests.get(f"{BASE_URL}/api/rh/funcionarios?status=ativo")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestRHEPIFichas:
    """Tests for /api/rh/epi/fichas endpoints"""
    
    def test_list_fichas_epi(self):
        """Test listing EPI fichas"""
        response = requests.get(f"{BASE_URL}/api/rh/epi/fichas")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestAuthLogin:
    """Tests for authentication"""
    
    def test_login_success(self):
        """Test successful login with test credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@test.com", "password": "password"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@test.com"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
