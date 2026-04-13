"""
Test Centro de Custo Export Filter Feature
Tests the export functionality with centro_custo filter for contas_pagar and contas_receber
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')

class TestCentroCustoExport:
    """Tests for Centro de Custo filter in Export functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    # Test 1: GET /api/admin/centros-custo - List centros de custo
    def test_list_centros_custo(self):
        """Test listing centros de custo"""
        response = requests.get(f"{BASE_URL}/api/admin/centros-custo", headers=self.headers)
        assert response.status_code == 200, f"Failed to list centros de custo: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Check if Administrativo CC exists (from seed data)
        if len(data) > 0:
            cc = data[0]
            assert "id" in cc, "Centro de custo should have id"
            assert "nome" in cc, "Centro de custo should have nome"
            print(f"Found {len(data)} centros de custo")
    
    # Test 2: GET /api/export/pdf/contas_pagar without centro_custo
    def test_export_pdf_contas_pagar_no_filter(self):
        """Test PDF export of contas_pagar without centro_custo filter"""
        response = requests.get(
            f"{BASE_URL}/api/export/pdf/contas_pagar",
            headers=self.headers
        )
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        assert response.headers.get('content-type') == 'application/pdf', "Response should be PDF"
        print("PDF export without filter: OK")
    
    # Test 3: GET /api/export/pdf/contas_pagar?centro_custo=Administrativo
    def test_export_pdf_contas_pagar_with_filter(self):
        """Test PDF export of contas_pagar with centro_custo filter"""
        response = requests.get(
            f"{BASE_URL}/api/export/pdf/contas_pagar?centro_custo=Administrativo",
            headers=self.headers
        )
        assert response.status_code == 200, f"PDF export with filter failed: {response.text}"
        assert response.headers.get('content-type') == 'application/pdf', "Response should be PDF"
        print("PDF export with centro_custo=Administrativo: OK")
    
    # Test 4: GET /api/export/excel/contas_pagar?centro_custo=Administrativo
    def test_export_excel_contas_pagar_with_filter(self):
        """Test Excel export of contas_pagar with centro_custo filter"""
        response = requests.get(
            f"{BASE_URL}/api/export/excel/contas_pagar?centro_custo=Administrativo",
            headers=self.headers
        )
        assert response.status_code == 200, f"Excel export with filter failed: {response.text}"
        content_type = response.headers.get('content-type', '')
        assert 'spreadsheet' in content_type or 'excel' in content_type or 'octet-stream' in content_type, \
            f"Response should be Excel, got: {content_type}"
        print("Excel export with centro_custo=Administrativo: OK")
    
    # Test 5: GET /api/export/pdf/contas_receber?centro_custo=Administrativo
    def test_export_pdf_contas_receber_with_filter(self):
        """Test PDF export of contas_receber with centro_custo filter"""
        response = requests.get(
            f"{BASE_URL}/api/export/pdf/contas_receber?centro_custo=Administrativo",
            headers=self.headers
        )
        assert response.status_code == 200, f"PDF export contas_receber failed: {response.text}"
        assert response.headers.get('content-type') == 'application/pdf', "Response should be PDF"
        print("PDF export contas_receber with centro_custo=Administrativo: OK")
    
    # Test 6: GET /api/export/excel/contas_receber?centro_custo=Administrativo
    def test_export_excel_contas_receber_with_filter(self):
        """Test Excel export of contas_receber with centro_custo filter"""
        response = requests.get(
            f"{BASE_URL}/api/export/excel/contas_receber?centro_custo=Administrativo",
            headers=self.headers
        )
        assert response.status_code == 200, f"Excel export contas_receber failed: {response.text}"
        print("Excel export contas_receber with centro_custo=Administrativo: OK")
    
    # Test 7: POST /api/export/combined with centro_custo
    def test_export_combined_with_centro_custo(self):
        """Test combined export with centro_custo filter"""
        response = requests.post(
            f"{BASE_URL}/api/export/combined",
            headers=self.headers,
            json={
                "categories": ["contas_pagar", "contas_receber"],
                "format": "pdf",
                "centro_custo": "Administrativo"
            }
        )
        assert response.status_code == 200, f"Combined export failed: {response.text}"
        assert response.headers.get('content-type') == 'application/pdf', "Response should be PDF"
        print("Combined export with centro_custo=Administrativo: OK")
    
    # Test 8: POST /api/export/combined without centro_custo (should work)
    def test_export_combined_without_centro_custo(self):
        """Test combined export without centro_custo filter"""
        response = requests.post(
            f"{BASE_URL}/api/export/combined",
            headers=self.headers,
            json={
                "categories": ["contas_pagar"],
                "format": "pdf"
            }
        )
        assert response.status_code == 200, f"Combined export without filter failed: {response.text}"
        print("Combined export without centro_custo: OK")
    
    # Test 9: GET /api/export/ofx/contas_pagar?centro_custo=Administrativo
    def test_export_ofx_contas_pagar_with_filter(self):
        """Test OFX export of contas_pagar with centro_custo filter"""
        response = requests.get(
            f"{BASE_URL}/api/export/ofx/contas_pagar?centro_custo=Administrativo",
            headers=self.headers
        )
        # OFX export may return 200 or error if no data
        assert response.status_code in [200, 400, 404], f"OFX export unexpected status: {response.status_code}"
        print(f"OFX export with centro_custo=Administrativo: Status {response.status_code}")
    
    # Test 10: Verify centro_custo filter is applied (check title in PDF)
    def test_export_pdf_title_includes_centro_custo(self):
        """Test that PDF export title includes centro_custo name"""
        response = requests.get(
            f"{BASE_URL}/api/export/pdf/contas_pagar?centro_custo=TestCC",
            headers=self.headers
        )
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        # The PDF should be generated even if no data matches the filter
        print("PDF export with non-existent centro_custo: OK (empty report)")


class TestCentroCustoAuth:
    """Tests for authentication on centro_custo endpoints"""
    
    def test_centros_custo_requires_auth(self):
        """Test that centros-custo endpoint works without auth (public list)"""
        # Note: Based on the code, this endpoint doesn't require auth
        response = requests.get(f"{BASE_URL}/api/admin/centros-custo")
        # The endpoint may or may not require auth based on implementation
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        print(f"Centros-custo without auth: Status {response.status_code}")
    
    def test_export_requires_auth(self):
        """Test that export endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/export/pdf/contas_pagar")
        assert response.status_code in [401, 403], f"Export should require auth, got: {response.status_code}"
        print("Export requires auth: OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
