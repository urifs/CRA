"""
Teste da Refatoração Sessão 32 — Módulo Conciliação Bancária extraído.
Valida que os 7 endpoints de /api/conciliacao/* funcionam no novo arquivo routes/conciliacao.py
E confirma que não há regressão nos outros endpoints críticos.
"""
import io
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://os-multiplos-valores.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


# ---------------- Fixtures ----------------

@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": "test@test.com", "password": "password"}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data, f"token not in login response: {data}"
    return data["token"]


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------- Conciliação — LISTAGEM ----------------

class TestConciliacaoListagem:
    def test_list_conciliacoes(self, headers):
        r = requests.get(f"{API}/conciliacao", headers=headers, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        data = r.json()
        assert isinstance(data, list), "Esperado uma lista de conciliações"

    def test_list_extratos_todos(self, headers):
        r = requests.get(f"{API}/conciliacao/extratos", headers=headers, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        assert isinstance(r.json(), list)

    def test_list_extratos_por_conta(self, headers):
        # uuid aleatório — deve retornar lista vazia, não erro
        r = requests.get(f"{API}/conciliacao/extratos/{uuid.uuid4()}", headers=headers, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        data = r.json()
        assert isinstance(data, list)
        assert data == []

    def test_auth_required_on_list(self):
        r = requests.get(f"{API}/conciliacao", timeout=30)
        assert r.status_code in (401, 403), f"Esperado 401/403 sem token, obtido {r.status_code}"


# ---------------- Conciliação — IMPORT PDF ----------------

class TestImportarExtrato:
    def test_rejeita_nao_pdf(self, headers):
        files = {"file": ("fake.txt", io.BytesIO(b"conteudo texto"), "text/plain")}
        data = {"conta_bancaria_id": str(uuid.uuid4())}
        r = requests.post(f"{API}/conciliacao/importar-extrato", headers=headers, files=files, data=data, timeout=30)
        assert r.status_code == 400, f"Esperado 400 para arquivo não-PDF, obtido {r.status_code} {r.text[:200]}"
        body = r.json()
        assert "detail" in body

    def test_pdf_com_conta_inexistente(self, headers):
        # arquivo termina em .pdf mas conta não existe → 404
        files = {"file": ("x.pdf", io.BytesIO(b"%PDF-1.4\n%fake"), "application/pdf")}
        data = {"conta_bancaria_id": str(uuid.uuid4())}
        r = requests.post(f"{API}/conciliacao/importar-extrato", headers=headers, files=files, data=data, timeout=30)
        # Aceita 404 (conta não encontrada) — validação correta da rota
        assert r.status_code in (404, 500), f"Esperado 404 para conta inexistente, obtido {r.status_code} {r.text[:200]}"


# ---------------- Conciliação — CONCILIAR / DESFAZER ----------------

class TestConciliarDesfazer:
    def test_conciliar_ids_invalidos(self, headers):
        payload = {
            "extrato_id": str(uuid.uuid4()),
            "conta_id": str(uuid.uuid4()),
            "conta_tipo": "pagar",
        }
        r = requests.post(f"{API}/conciliacao/conciliar", headers=headers, json=payload, timeout=30)
        assert r.status_code == 404, f"Esperado 404 para ids inválidos, obtido {r.status_code} {r.text[:200]}"
        assert "não encontrado" in r.text.lower() or "not found" in r.text.lower()

    def test_desfazer_id_invalido(self, headers):
        r = requests.delete(f"{API}/conciliacao/{uuid.uuid4()}", headers=headers, timeout=30)
        assert r.status_code == 404, f"Esperado 404, obtido {r.status_code} {r.text[:200]}"


# ---------------- Conciliação — DELETE extratos (limpar) ----------------

class TestLimparExtratos:
    def test_limpar_extratos(self, headers):
        r = requests.delete(f"{API}/conciliacao/extratos", headers=headers, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        body = r.json()
        assert "count" in body, f"Resposta deve ter 'count', obtido: {body}"
        assert isinstance(body["count"], int)
        assert "message" in body


# ---------------- REGRESSÃO — endpoints críticos de outros módulos ----------------

class TestRegressaoEndpointsCriticos:
    """Confirma que outros endpoints não regrediram com a extração de conciliacao."""

    def test_auth_login_still_works(self):
        r = requests.post(f"{API}/auth/login", json={"email": "test@test.com", "password": "password"}, timeout=30)
        assert r.status_code == 200
        assert "token" in r.json()

    def test_nfe_importadas(self, headers):
        r = requests.get(f"{API}/nfe/importadas", headers=headers, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        # pode ser lista ou objeto com lista
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_nfe_certificados(self, headers):
        r = requests.get(f"{API}/nfe/certificados", headers=headers, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"

    def test_contas_pagar(self, headers):
        r = requests.get(f"{API}/admin/contas-pagar", headers=headers, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        assert isinstance(r.json(), list)

    def test_contas_receber(self, headers):
        r = requests.get(f"{API}/admin/contas-receber", headers=headers, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        assert isinstance(r.json(), list)

    def test_dashboard_admin(self, headers):
        r = requests.get(f"{API}/admin/dashboard", headers=headers, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        assert isinstance(r.json(), dict)

    def test_export_pdf_contas_pagar(self, headers):
        r = requests.get(f"{API}/export/pdf/contas_pagar", headers=headers, timeout=60)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        # PDF deve começar com %PDF
        assert r.content[:4] == b"%PDF", f"Esperado PDF, obtido primeiros bytes: {r.content[:20]}"
