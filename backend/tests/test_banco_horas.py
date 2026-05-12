"""
Backend tests for Banco de Horas (Hour Bank) and Férias Alertas Dispensar features.

Coverage:
- POST /api/rh/banco-horas/ajustes (create manual adjustment)
- GET /api/rh/banco-horas/ajustes (list)
- DELETE /api/rh/banco-horas/ajustes/{id} (remove)
- GET /api/rh/banco-horas/resumo (summary)
- GET /api/rh/banco-horas/funcionarios/{id}/extrato (statement with `ajustes` field)
- POST/DELETE /api/rh/ferias/alertas/dispensar/{funcionario_id}
"""
import os
import pytest
import requests
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://erp-financeiro-fixes.preview.emergentagent.com").rstrip("/")
EMAIL = "test@test.com"
PASSWORD = "password"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("token") or data.get("access_token")
    assert token, f"Token not in response: {data}"
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="module")
def funcionario_id(session):
    r = session.get(f"{BASE_URL}/api/rh/funcionarios", timeout=20)
    assert r.status_code == 200
    funcs = r.json()
    assert len(funcs) > 0, "No funcionarios found - seed data needed"
    # Find first ativo
    for f in funcs:
        if f.get("status", "ativo") == "ativo":
            return f["id"]
    return funcs[0]["id"]


# ===== Banco de Horas Resumo =====
class TestBancoHorasResumo:
    def test_resumo_default(self, session):
        r = session.get(f"{BASE_URL}/api/rh/banco-horas/resumo", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "funcionarios" in data
        assert "total_funcionarios" in data
        assert "saldo_liquido_minutos" in data
        assert isinstance(data["funcionarios"], list)

    def test_resumo_with_period(self, session):
        hoje = datetime.now().strftime("%Y-%m-%d")
        primeiro = datetime.now().strftime("%Y-%m-01")
        r = session.get(
            f"{BASE_URL}/api/rh/banco-horas/resumo",
            params={"de_data": primeiro, "ate_data": hoje},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "funcionarios" in data


# ===== Ajustes CRUD =====
class TestBancoHorasAjustes:
    created_ids = []

    def test_create_ajuste_credito(self, session, funcionario_id):
        payload = {
            "funcionario_id": funcionario_id,
            "minutos": 120,  # +2h
            "data": datetime.now().strftime("%Y-%m-%d"),
            "motivo": "TEST_ Compensação por hora extra trabalhada",
            "tipo": "compensacao",
        }
        r = session.post(f"{BASE_URL}/api/rh/banco-horas/ajustes", json=payload, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["minutos"] == 120
        assert data["motivo"] == payload["motivo"]
        assert data["tipo"] == "compensacao"
        assert "id" in data
        TestBancoHorasAjustes.created_ids.append(data["id"])

    def test_create_ajuste_debito(self, session, funcionario_id):
        payload = {
            "funcionario_id": funcionario_id,
            "minutos": -60,  # -1h
            "data": datetime.now().strftime("%Y-%m-%d"),
            "motivo": "TEST_ Atraso justificado",
            "tipo": "ajuste",
        }
        r = session.post(f"{BASE_URL}/api/rh/banco-horas/ajustes", json=payload, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data["minutos"] == -60
        TestBancoHorasAjustes.created_ids.append(data["id"])

    def test_create_ajuste_zero_invalid(self, session, funcionario_id):
        payload = {
            "funcionario_id": funcionario_id,
            "minutos": 0,
            "motivo": "Zero",
        }
        r = session.post(f"{BASE_URL}/api/rh/banco-horas/ajustes", json=payload, timeout=20)
        assert r.status_code == 400

    def test_create_ajuste_no_motivo(self, session, funcionario_id):
        payload = {
            "funcionario_id": funcionario_id,
            "minutos": 30,
            "motivo": "   ",
        }
        r = session.post(f"{BASE_URL}/api/rh/banco-horas/ajustes", json=payload, timeout=20)
        assert r.status_code == 400

    def test_create_ajuste_func_inexistente(self, session):
        payload = {
            "funcionario_id": "nope-id-xxxx",
            "minutos": 30,
            "motivo": "TEST_ x",
        }
        r = session.post(f"{BASE_URL}/api/rh/banco-horas/ajustes", json=payload, timeout=20)
        assert r.status_code == 404

    def test_listar_ajustes_por_funcionario(self, session, funcionario_id):
        r = session.get(
            f"{BASE_URL}/api/rh/banco-horas/ajustes",
            params={"funcionario_id": funcionario_id},
            timeout=20,
        )
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        ids = [d["id"] for d in data]
        for cid in TestBancoHorasAjustes.created_ids:
            assert cid in ids, f"Created id {cid} not present in list"

    def test_extrato_inclui_ajustes(self, session, funcionario_id):
        r = session.get(
            f"{BASE_URL}/api/rh/banco-horas/funcionarios/{funcionario_id}/extrato",
            timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Required field per spec: `ajustes` (NOT `ajustes_manuais`)
        assert "ajustes" in data, f"Field 'ajustes' missing in extrato. Keys: {list(data.keys())}"
        assert "ajustes_minutos" in data
        assert "saldo_total_minutos" in data
        assert "evolucao_mensal" in data
        assert "detalhe_dias" in data
        # ajustes criados acima devem estar (filtra por funcionario_id, no período = ate_data default hoje)
        ids = [a["id"] for a in data["ajustes"]]
        for cid in TestBancoHorasAjustes.created_ids:
            assert cid in ids

    def test_delete_ajuste(self, session):
        # delete the credito ajuste
        if not TestBancoHorasAjustes.created_ids:
            pytest.skip("No created ajustes")
        aid = TestBancoHorasAjustes.created_ids[0]
        r = session.delete(f"{BASE_URL}/api/rh/banco-horas/ajustes/{aid}", timeout=20)
        assert r.status_code == 200
        assert r.json().get("ok") is True
        # confirm gone
        r2 = session.delete(f"{BASE_URL}/api/rh/banco-horas/ajustes/{aid}", timeout=20)
        assert r2.status_code == 404
        TestBancoHorasAjustes.created_ids.pop(0)

    def test_cleanup_remaining(self, session):
        for aid in list(TestBancoHorasAjustes.created_ids):
            session.delete(f"{BASE_URL}/api/rh/banco-horas/ajustes/{aid}", timeout=20)
        TestBancoHorasAjustes.created_ids.clear()


# ===== Férias Alertas Dispensar =====
class TestFeriasAlertasDispensar:
    def test_dispensar_alerta(self, session, funcionario_id):
        r = session.post(
            f"{BASE_URL}/api/rh/ferias/alertas/dispensar/{funcionario_id}", timeout=20
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        assert data.get("funcionario_id") == funcionario_id

    def test_lista_dispensados_inclui(self, session, funcionario_id):
        r = session.get(f"{BASE_URL}/api/rh/ferias/alertas/dispensados", timeout=20)
        assert r.status_code == 200
        ids = [d["funcionario_id"] for d in r.json()]
        assert funcionario_id in ids

    def test_reativar_alerta(self, session, funcionario_id):
        r = session.delete(
            f"{BASE_URL}/api/rh/ferias/alertas/dispensar/{funcionario_id}", timeout=20
        )
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_dispensar_func_inexistente(self, session):
        r = session.post(
            f"{BASE_URL}/api/rh/ferias/alertas/dispensar/no-such-id", timeout=20
        )
        assert r.status_code == 404
