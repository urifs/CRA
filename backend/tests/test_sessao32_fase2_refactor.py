"""
Sessão 32 Fase 2 — Refactor validation.
Testa endpoints extraídos de server.py para routes modulares:
- routes/exports_all.py (todos os /api/export/*)
- routes/dashboard.py  (GET /api/dashboard)
- routes/medicoes.py   (/api/medicoes/*)
- routes/stock.py      (/api/stock/*)  — agora ÚNICO handler após remoção do duplicado
- routes/obras.py      (/api/obras/*)  — agora ÚNICO handler após remoção do duplicado
- Regressão Fase 1 (admin/contas-*, nfe, nfse, conciliacao, auth, etc.)
"""
import os
import io
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://danfe-export.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": "test@test.com", "password": "password"}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    return data.get("token") or data.get("access_token")


@pytest.fixture(scope="session")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def some_obra_id(auth_headers):
    r = requests.get(f"{API}/obras", headers=auth_headers, timeout=10)
    if r.status_code == 200 and isinstance(r.json(), list) and r.json():
        return r.json()[0]["id"]
    return None


# ---------- DASHBOARD ----------
class TestDashboard:
    def test_dashboard_get(self, auth_headers):
        r = requests.get(f"{API}/dashboard", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        # Validate ALL DashboardStats fields
        for f in [
            "total_machines", "total_maintenances", "preventive_count",
            "corrective_count", "total_spent", "recent_maintenances",
            "low_stock_count", "oil_change_alerts", "machines_by_category",
        ]:
            assert f in d, f"Field {f} missing in dashboard"
        assert isinstance(d["total_machines"], int)
        assert isinstance(d["total_maintenances"], int)
        assert isinstance(d["recent_maintenances"], list)
        assert isinstance(d["machines_by_category"], list)
        # No leaked _id in nested
        for m in d["recent_maintenances"]:
            assert "_id" not in m
        for c in d["machines_by_category"]:
            assert "_id" not in c
            for f in ["category_id", "category_name", "category_color", "count"]:
                assert f in c


# ---------- STOCK (modular) ----------
class TestStock:
    def test_stock_items(self, auth_headers):
        r = requests.get(f"{API}/stock/items", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        for item in data[:5]:
            assert "_id" not in item
            assert "id" in item

    def test_stock_categories(self, auth_headers):
        r = requests.get(f"{API}/stock/categories", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        for c in data[:5]:
            assert "_id" not in c

    def test_stock_subcategories(self, auth_headers):
        r = requests.get(f"{API}/stock/subcategories", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_stock_movements(self, auth_headers):
        r = requests.get(f"{API}/stock/movements", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_stock_alerts(self, auth_headers):
        r = requests.get(f"{API}/stock/alerts", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text


# ---------- OBRAS (modular) ----------
class TestObras:
    def test_obras_list(self, auth_headers):
        r = requests.get(f"{API}/obras", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        for o in data[:5]:
            assert "_id" not in o
            assert "id" in o
            assert "name" in o

    def test_obras_machines(self, auth_headers, some_obra_id):
        if not some_obra_id:
            pytest.skip("No obra available")
        r = requests.get(f"{API}/obras/{some_obra_id}/machines", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_obras_costs(self, auth_headers, some_obra_id):
        if not some_obra_id:
            pytest.skip("No obra available")
        r = requests.get(f"{API}/obras/{some_obra_id}/costs", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text

    def test_obras_invalid_id(self, auth_headers):
        r = requests.get(f"{API}/obras/non-existent-id-xyz/machines", headers=auth_headers, timeout=15)
        # Pode 404 ou retornar lista vazia dependendo da implementação
        assert r.status_code in [200, 404], r.text


# ---------- MEDIÇÕES ----------
class TestMedicoes:
    def test_medicoes_list(self, auth_headers):
        r = requests.get(f"{API}/medicoes", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_medicoes_resumo_existing_obra(self, auth_headers, some_obra_id):
        if not some_obra_id:
            pytest.skip("No obra available")
        r = requests.get(f"{API}/medicoes/resumo/{some_obra_id}", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for f in ["obra_id", "obra_nome", "total_medicoes", "maquinas"]:
            assert f in d, f"Field {f} missing"
        assert isinstance(d["maquinas"], list)

    def test_medicoes_resumo_invalid_obra(self, auth_headers):
        r = requests.get(f"{API}/medicoes/resumo/obra-inexistente-xyz", headers=auth_headers, timeout=15)
        assert r.status_code == 404, r.text

    def test_medicoes_get_invalid(self, auth_headers):
        r = requests.get(f"{API}/medicoes/non-existent-id-abc", headers=auth_headers, timeout=15)
        assert r.status_code == 404, r.text


# ---------- EXPORT ----------
class TestExport:
    def test_export_categories_gerenciamento(self, auth_headers):
        r = requests.get(f"{API}/export/categories/gerenciamento", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        # Deve retornar estrutura de categorias (lista ou dict)
        assert isinstance(d, (list, dict))

    def test_export_pdf_machines(self, auth_headers):
        r = requests.get(f"{API}/export/pdf/machines?centro_custo=todos", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        # Validar PDF binário
        assert r.content[:4] == b"%PDF", f"Not a valid PDF (got {r.content[:20]})"
        assert len(r.content) > 100

    def test_export_pdf_contas_pagar(self, auth_headers):
        r = requests.get(f"{API}/export/pdf/contas_pagar?centro_custo=todos", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        assert r.content[:4] == b"%PDF"

    def test_export_excel_contas_pagar(self, auth_headers):
        r = requests.get(f"{API}/export/excel/contas_pagar?centro_custo=todos", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        # XLSX é zip → começa com 'PK'
        assert r.content[:2] == b"PK", f"Not a valid XLSX (got {r.content[:20]})"
        assert len(r.content) > 200

    def test_export_ofx_contas_pagar(self, auth_headers):
        r = requests.get(f"{API}/export/ofx/contas_pagar?centro_custo=todos", headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text
        # OFX começa com header OFXHEADER ou tag <OFX>
        text = r.content.decode("latin-1", errors="ignore").upper()
        assert "OFX" in text[:500], f"OFX header not found in: {text[:200]}"

    def test_export_combined(self, auth_headers):
        payload = {
            "modules": ["gerenciamento"],
            "categories": ["machines"],
            "centro_custo": "todos",
            "format": "pdf",
        }
        r = requests.post(f"{API}/export/combined", json=payload, headers=auth_headers, timeout=60)
        # Aceitar 200 (sucesso), 400 (payload diferente), 422 (validação)
        assert r.status_code in [200, 400, 422], f"Unexpected: {r.status_code} {r.text[:300]}"


# ---------- REGRESSÃO Fase 1 ----------
class TestRegressaoFase1:
    @pytest.mark.parametrize("path", [
        "/admin/contas-pagar",
        "/admin/contas-receber",
        "/nfe/importadas",
        "/nfe/certificados",
        "/nfse/importadas",
        "/conciliacao",
        "/nfe/cfops",
        "/notas-emitidas",
        "/admin/dashboard",
        "/nf/importacao-automatica/status",
    ])
    def test_regression_get(self, auth_headers, path):
        r = requests.get(f"{API}{path}", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"GET {path} -> {r.status_code} {r.text[:200]}"

    def test_auth_login_again(self):
        r = requests.post(f"{API}/auth/login", json={"email": "test@test.com", "password": "password"}, timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d.get("token") or d.get("access_token")
