"""Tests for bulk abono (abono em massa) endpoints in RH/Ponto module."""
import os
import io
import json
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://erp-financeiro-fixes.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

# Funcionário JOSÉ DA COSTA conforme contexto do main agent
FUNCIONARIO_ID = "cf6a8933-1a4e-4005-b4bc-d386f29ca827"

# Datas usadas pelos testes — mês/ano com folga: usar 2026-04 (Abril) que tem dias úteis
DATAS_VALIDAS = ["2026-04-06", "2026-04-07", "2026-04-08"]


@pytest.fixture(scope="module")
def auth_headers():
    """Login com credenciais de teste"""
    r = requests.post(f"{API}/auth/login", json={"email": "test@test.com", "password": "password"}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"Login falhou: {r.status_code} {r.text[:200]}")
    token = r.json().get("token") or r.json().get("access_token")
    if not token:
        pytest.skip("Sem token na resposta de login")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def cleanup(auth_headers):
    """Após o módulo, deleta abonos criados nas datas de teste"""
    yield
    try:
        r = requests.get(
            f"{API}/rh/ponto/abonos",
            params={"funcionario_id": FUNCIONARIO_ID, "mes": 4, "ano": 2026},
            headers=auth_headers, timeout=15,
        )
        if r.status_code == 200:
            for a in r.json() or []:
                if a.get("data") in DATAS_VALIDAS:
                    requests.delete(f"{API}/rh/ponto/abono/{a['id']}", headers=auth_headers, timeout=10)
    except Exception as e:
        print(f"Cleanup error: {e}")


# ==================== Bulk creation - JSON ====================
class TestAbonoEmMassaJSON:
    def test_criar_3_abonos_em_massa(self, auth_headers, cleanup):
        payload = {
            "funcionario_id": FUNCIONARIO_ID,
            "datas": DATAS_VALIDAS,
            "tipo": "atestado",
            "motivo": "Teste massa - atestado médico",
        }
        r = requests.post(f"{API}/rh/ponto/abono-em-massa", json=payload, headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Esperado 200 — recebido {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("criados") == 3
        assert sorted(data.get("datas") or []) == sorted(DATAS_VALIDAS)
        abonos = data.get("abonos") or []
        assert len(abonos) == 3
        for a in abonos:
            assert a.get("funcionario_id") == FUNCIONARIO_ID
            assert a.get("tipo") == "atestado"
            assert a.get("motivo") == "Teste massa - atestado médico"
            assert "id" in a and a["id"]
            assert "_id" not in a  # ObjectId NÃO deve aparecer

    def test_idempotencia_nao_duplica(self, auth_headers, cleanup):
        payload = {
            "funcionario_id": FUNCIONARIO_ID,
            "datas": DATAS_VALIDAS,
            "tipo": "justificativa",
            "motivo": "Re-execução idempotente",
        }
        # Primeira chamada
        r1 = requests.post(f"{API}/rh/ponto/abono-em-massa", json=payload, headers=auth_headers, timeout=15)
        assert r1.status_code == 200
        # Segunda chamada — deve substituir, não duplicar
        r2 = requests.post(f"{API}/rh/ponto/abono-em-massa", json=payload, headers=auth_headers, timeout=15)
        assert r2.status_code == 200
        # Buscar e verificar quantidade
        rg = requests.get(
            f"{API}/rh/ponto/abonos",
            params={"funcionario_id": FUNCIONARIO_ID, "mes": 4, "ano": 2026},
            headers=auth_headers, timeout=15,
        )
        assert rg.status_code == 200
        abonos_nas_datas = [a for a in rg.json() if a.get("data") in DATAS_VALIDAS]
        assert len(abonos_nas_datas) == 3, f"Esperado 3 abonos únicos — recebido {len(abonos_nas_datas)}"
        # Após 2ª chamada o tipo deve ser 'justificativa'
        assert all(a.get("tipo") == "justificativa" for a in abonos_nas_datas)

    def test_listar_abonos(self, auth_headers, cleanup):
        # Garantir que há abonos
        requests.post(f"{API}/rh/ponto/abono-em-massa", json={
            "funcionario_id": FUNCIONARIO_ID,
            "datas": DATAS_VALIDAS,
            "tipo": "folga",
            "motivo": "para listagem",
        }, headers=auth_headers, timeout=15)
        r = requests.get(f"{API}/rh/ponto/abonos",
                         params={"funcionario_id": FUNCIONARIO_ID, "mes": 4, "ano": 2026},
                         headers=auth_headers, timeout=15)
        assert r.status_code == 200
        lst = r.json()
        assert isinstance(lst, list)
        datas_retornadas = {a["data"] for a in lst}
        for d in DATAS_VALIDAS:
            assert d in datas_retornadas

    def test_delete_apenas_um(self, auth_headers, cleanup):
        # Criar 3 fresh
        r0 = requests.post(f"{API}/rh/ponto/abono-em-massa", json={
            "funcionario_id": FUNCIONARIO_ID,
            "datas": DATAS_VALIDAS,
            "tipo": "outros",
            "motivo": "para delete parcial",
        }, headers=auth_headers, timeout=15)
        assert r0.status_code == 200
        abonos = r0.json()["abonos"]
        target = abonos[0]
        rd = requests.delete(f"{API}/rh/ponto/abono/{target['id']}", headers=auth_headers, timeout=10)
        assert rd.status_code in (200, 204)
        # GET — os outros 2 ainda existem
        rg = requests.get(f"{API}/rh/ponto/abonos",
                          params={"funcionario_id": FUNCIONARIO_ID, "mes": 4, "ano": 2026},
                          headers=auth_headers, timeout=15)
        assert rg.status_code == 200
        ids_restantes = {a["id"] for a in rg.json()}
        assert target["id"] not in ids_restantes
        assert abonos[1]["id"] in ids_restantes
        assert abonos[2]["id"] in ids_restantes


# ==================== Validações ====================
class TestAbonoEmMassaValidations:
    def test_datas_vazia_400(self, auth_headers):
        r = requests.post(f"{API}/rh/ponto/abono-em-massa", json={
            "funcionario_id": FUNCIONARIO_ID, "datas": [], "tipo": "atestado", "motivo": "x",
        }, headers=auth_headers, timeout=10)
        assert r.status_code == 400

    def test_tipo_invalido_400(self, auth_headers):
        r = requests.post(f"{API}/rh/ponto/abono-em-massa", json={
            "funcionario_id": FUNCIONARIO_ID, "datas": ["2026-04-06"],
            "tipo": "invalido_xyz", "motivo": "x",
        }, headers=auth_headers, timeout=10)
        assert r.status_code == 400

    def test_motivo_vazio_400(self, auth_headers):
        r = requests.post(f"{API}/rh/ponto/abono-em-massa", json={
            "funcionario_id": FUNCIONARIO_ID, "datas": ["2026-04-06"],
            "tipo": "atestado", "motivo": "   ",
        }, headers=auth_headers, timeout=10)
        assert r.status_code == 400

    def test_data_invalida_400(self, auth_headers):
        r = requests.post(f"{API}/rh/ponto/abono-em-massa", json={
            "funcionario_id": FUNCIONARIO_ID, "datas": ["31/12/2026"],
            "tipo": "atestado", "motivo": "x",
        }, headers=auth_headers, timeout=10)
        assert r.status_code == 400

    def test_funcionario_id_vazio_400(self, auth_headers):
        r = requests.post(f"{API}/rh/ponto/abono-em-massa", json={
            "funcionario_id": "", "datas": ["2026-04-06"],
            "tipo": "atestado", "motivo": "x",
        }, headers=auth_headers, timeout=10)
        assert r.status_code == 400


# ==================== Multipart com anexo (datas como JSON string) ====================
class TestAbonoEmMassaMultipart:
    def test_multipart_sem_arquivo(self, auth_headers, cleanup):
        """Envia multipart sem arquivo — deve criar todos abonos com anexo=null."""
        files = {
            "funcionario_id": (None, FUNCIONARIO_ID),
            "datas": (None, json.dumps(DATAS_VALIDAS)),
            "tipo": (None, "atestado"),
            "motivo": (None, "Teste multipart sem arquivo"),
        }
        r = requests.post(f"{API}/rh/ponto/abono-em-massa-com-anexo",
                          files=files, headers=auth_headers, timeout=20)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("criados") == 3
        assert data.get("anexo_compartilhado") is False
        for a in data["abonos"]:
            assert a.get("anexo") in (None, {})

    def test_multipart_com_pdf(self, auth_headers, cleanup):
        """Envia multipart com PDF pequeno — todos abonos compartilham mesmo storage_path."""
        # PDF mínimo válido (~ minimal stub)
        pdf_bytes = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                     b"2 0 obj<</Type/Pages/Count 0>>endobj\n"
                     b"trailer<</Root 1 0 R>>\n%%EOF\n")
        files = {
            "funcionario_id": (None, FUNCIONARIO_ID),
            "datas": (None, json.dumps(DATAS_VALIDAS)),
            "tipo": (None, "atestado"),
            "motivo": (None, "Teste multipart com PDF"),
            "arquivo": ("teste.pdf", pdf_bytes, "application/pdf"),
        }
        r = requests.post(f"{API}/rh/ponto/abono-em-massa-com-anexo",
                          files=files, headers=auth_headers, timeout=30)
        if r.status_code == 502:
            pytest.skip(f"Storage não configurado neste ambiente: {r.text[:200]}")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("criados") == 3
        assert data.get("anexo_compartilhado") is True
        # storage_path deve ser o mesmo em todos
        paths = [a["anexo"]["storage_path"] for a in data["abonos"]]
        assert len(set(paths)) == 1, f"storage_path divergente entre abonos: {paths}"

    def test_multipart_datas_invalida_400(self, auth_headers):
        files = {
            "funcionario_id": (None, FUNCIONARIO_ID),
            "datas": (None, "nao_e_json"),
            "tipo": (None, "atestado"),
            "motivo": (None, "x"),
        }
        r = requests.post(f"{API}/rh/ponto/abono-em-massa-com-anexo",
                          files=files, headers=auth_headers, timeout=10)
        assert r.status_code == 400
