"""
Test Export APIs - Testing export functionality for Administrativo, Gerenciamento, and RH modules
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@test.com",
        "password": "password"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]

@pytest.fixture(scope="module")
def headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestExportCategoriesAPI:
    """Test /api/export/categories/{module} endpoint"""
    
    def test_export_categories_gerenciamento(self, headers):
        """Test GET /api/export/categories/gerenciamento returns categories"""
        response = requests.get(f"{BASE_URL}/api/export/categories/gerenciamento", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one category"
        
        # Check structure
        category_ids = [cat["id"] for cat in data]
        assert "maquinas" in category_ids, "Should have 'maquinas' category"
        assert "manutencoes" in category_ids, "Should have 'manutencoes' category"
        assert "estoque" in category_ids, "Should have 'estoque' category"
        
        # Check subcategories exist
        for cat in data:
            assert "subcategories" in cat, f"Category {cat['id']} should have subcategories"
            assert len(cat["subcategories"]) > 0, f"Category {cat['id']} should have at least one subcategory"
        
        print(f"✓ Gerenciamento has {len(data)} categories")
    
    def test_export_categories_administrativo(self, headers):
        """Test GET /api/export/categories/administrativo returns categories"""
        response = requests.get(f"{BASE_URL}/api/export/categories/administrativo", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one category"
        
        # Check structure
        category_ids = [cat["id"] for cat in data]
        assert "financeiro_pagar" in category_ids, "Should have 'financeiro_pagar' category"
        assert "financeiro_receber" in category_ids, "Should have 'financeiro_receber' category"
        assert "cadastros" in category_ids, "Should have 'cadastros' category"
        
        print(f"✓ Administrativo has {len(data)} categories")
    
    def test_export_categories_rh(self, headers):
        """Test GET /api/export/categories/rh returns 6 RH categories"""
        response = requests.get(f"{BASE_URL}/api/export/categories/rh", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 6, f"RH should have exactly 6 categories, got {len(data)}"
        
        # Check all 6 RH categories exist
        category_ids = [cat["id"] for cat in data]
        expected_categories = ["funcionarios_cat", "ponto_cat", "folha_cat", "ferias_cat", "epi_cat", "custos_cat"]
        for expected in expected_categories:
            assert expected in category_ids, f"Should have '{expected}' category"
        
        # Count total subcategories
        total_subcategories = sum(len(cat["subcategories"]) for cat in data)
        print(f"✓ RH has {len(data)} categories with {total_subcategories} total subcategories")
        
        # Verify subcategory structure
        for cat in data:
            for sub in cat["subcategories"]:
                assert "id" in sub, f"Subcategory should have 'id'"
                assert "label" in sub, f"Subcategory should have 'label'"
                assert "description" in sub, f"Subcategory should have 'description'"
    
    def test_export_categories_invalid_module(self, headers):
        """Test GET /api/export/categories/invalid returns 400"""
        response = requests.get(f"{BASE_URL}/api/export/categories/invalid_module", headers=headers)
        assert response.status_code == 400, f"Should return 400 for invalid module"


class TestExportPDFAPI:
    """Test /api/export/pdf/{category} endpoint"""
    
    # Gerenciamento categories
    def test_export_pdf_machines(self, headers):
        """Test PDF export for machines (Gerenciamento)"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/machines", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        assert len(response.content) > 0, "PDF should have content"
        print("✓ PDF export for machines works")
    
    def test_export_pdf_maintenances(self, headers):
        """Test PDF export for maintenances (Gerenciamento)"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/maintenances", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        print("✓ PDF export for maintenances works")
    
    # Administrativo categories
    def test_export_pdf_contas_pagar(self, headers):
        """Test PDF export for contas_pagar (Administrativo)"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/contas_pagar", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        print("✓ PDF export for contas_pagar works")
    
    def test_export_pdf_contas_receber(self, headers):
        """Test PDF export for contas_receber (Administrativo)"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/contas_receber", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        print("✓ PDF export for contas_receber works")
    
    # RH categories
    def test_export_pdf_funcionarios(self, headers):
        """Test PDF export for funcionarios (RH)"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/funcionarios", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        print("✓ PDF export for funcionarios (RH) works")
    
    def test_export_pdf_ponto_registros(self, headers):
        """Test PDF export for ponto_registros (RH)"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/ponto_registros", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        print("✓ PDF export for ponto_registros (RH) works")
    
    def test_export_pdf_folha_pagamento(self, headers):
        """Test PDF export for folha_pagamento (RH)"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/folha_pagamento", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        print("✓ PDF export for folha_pagamento (RH) works")
    
    def test_export_pdf_ferias(self, headers):
        """Test PDF export for ferias (RH)"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/ferias", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        print("✓ PDF export for ferias (RH) works")
    
    def test_export_pdf_epi_fichas(self, headers):
        """Test PDF export for epi_fichas (RH)"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/epi_fichas", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        print("✓ PDF export for epi_fichas (RH) works")
    
    def test_export_pdf_invalid_category(self, headers):
        """Test PDF export for invalid category returns 400"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/invalid_category", headers=headers)
        assert response.status_code == 400, f"Should return 400 for invalid category"


class TestExportCombinedAPI:
    """Test /api/export/combined endpoint"""
    
    def test_export_combined_gerenciamento(self, headers):
        """Test combined export for Gerenciamento categories"""
        response = requests.post(f"{BASE_URL}/api/export/combined", 
            headers=headers,
            json={
                "categories": ["machines", "maintenances"],
                "format": "pdf"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        print("✓ Combined export for Gerenciamento works")
    
    def test_export_combined_administrativo(self, headers):
        """Test combined export for Administrativo categories"""
        response = requests.post(f"{BASE_URL}/api/export/combined", 
            headers=headers,
            json={
                "categories": ["contas_pagar", "contas_receber"],
                "format": "pdf"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Should return PDF"
        print("✓ Combined export for Administrativo works")
    
    def test_export_combined_empty_categories(self, headers):
        """Test combined export with empty categories returns 400"""
        response = requests.post(f"{BASE_URL}/api/export/combined", 
            headers=headers,
            json={
                "categories": [],
                "format": "pdf"
            }
        )
        assert response.status_code == 400, f"Should return 400 for empty categories"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
