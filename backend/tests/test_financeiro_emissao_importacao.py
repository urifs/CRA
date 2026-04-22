"""
Testes de regressão Sessão 32 Parte 2 — refatoração de:
- routes/financeiro.py (Contas a Pagar / Contas a Receber)
- routes/emissao_nf.py (Emissão NF-e/NFS-e + tabelas)
- routes/importacao_nf.py (Importação SEFAZ/ABRASF)
+ regressão Conciliação, NFS-e, NF-e, scheduler e endpoints gerais.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "http://localhost:8001"
EMAIL = "test@test.com"
PASSWORD = "password"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login falhou: {r.status_code} {r.text}"
    data = r.json()
    tk = data.get("token") or data.get("access_token")
    assert tk
    return tk


@pytest.fixture(scope="module")
def H(token):
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# FINANCEIRO — CONTAS A PAGAR
# =============================================================================
class TestContasPagar:
    created_ids = []

    def test_list_contas_pagar(self, H):
        r = requests.get(f"{BASE_URL}/api/admin/contas-pagar", headers=H, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_with_filters(self, H):
        r = requests.get(f"{BASE_URL}/api/admin/contas-pagar?status=em_aberto&vencimento=vencidas&search=teste",
                         headers=H, timeout=30)
        assert r.status_code == 200

    def test_create_minimal(self, H):
        payload = {
            "descricao": "TEST_CP_MIN",
            "valor": 100.0,
            "data_vencimento": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
        }
        r = requests.post(f"{BASE_URL}/api/admin/contas-pagar", headers=H, json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # BUG FIX iteration 29 verification: no _id leak, all new fields present
        assert "_id" not in data, f"_id leaked in response: {data}"
        assert data["descricao"] == "TEST_CP_MIN"
        assert data["valor"] == 100.0
        assert data["valor_final"] == 100.0, f"valor_final missing/wrong: {data}"
        assert "id" in data and "numero" in data
        assert isinstance(data["numero"], int)
        # Fields required by FIX — must be present (may be None)
        for f in ("created_by", "subconta_id", "subconta_nome",
                  "conta_bancaria_id", "conta_bancaria_nome",
                  "total_parcelas", "numero_parcela", "parcela_origem_id"):
            assert f in data, f"Campo obrigatório ausente no response: {f} — data={data}"
        TestContasPagar.created_ids.append(data["id"])

        # GET para confirmar persistência
        r2 = requests.get(f"{BASE_URL}/api/admin/contas-pagar?search=TEST_CP_MIN", headers=H, timeout=30)
        assert r2.status_code == 200
        assert any(c["id"] == data["id"] for c in r2.json())

    def test_parcelado_invalid(self, H):
        payload = {
            "descricao": "TEST_CP_PAR",
            "valor_total": 300.0,
            "data_primeiro_vencimento": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "total_parcelas": 0,
        }
        r = requests.post(f"{BASE_URL}/api/admin/contas-pagar/parcelado", headers=H, json=payload, timeout=30)
        # 0 parcelas viola constraint do código (>= 1) — deve dar 400.
        # Pydantic pode validar como 422 se houvesse constraint; aqui o check é manual.
        assert r.status_code == 400, r.text

    def test_parcelado_ok(self, H):
        payload = {
            "descricao": "TEST_CP_PAR_OK",
            "valor_total": 300.0,
            "data_primeiro_vencimento": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "total_parcelas": 3,
            "intervalo_dias": 30,
        }
        r = requests.post(f"{BASE_URL}/api/admin/contas-pagar/parcelado", headers=H, json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert len(data["parcelas"]) == 3
        # Verify each parcela has all required fields and no _id leak
        parent_id = None
        for idx, p in enumerate(data["parcelas"], start=1):
            assert "_id" not in p, f"_id leaked in parcela: {p}"
            assert p.get("total_parcelas") == 3, f"total_parcelas wrong in {p}"
            assert p.get("numero_parcela") == idx, f"numero_parcela wrong for idx={idx}: {p}"
            assert "valor_final" in p
            assert "created_by" in p
            assert "parcela_origem_id" in p
            if idx == 1:
                parent_id = p["parcela_origem_id"] or p["id"]
            TestContasPagar.created_ids.append(p["id"])

    def test_update(self, H):
        assert TestContasPagar.created_ids
        cid = TestContasPagar.created_ids[0]
        payload = {
            "descricao": "TEST_CP_MIN_UPDATED",
            "valor": 150.0,
            "data_vencimento": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
        }
        r = requests.put(f"{BASE_URL}/api/admin/contas-pagar/{cid}", headers=H, json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # PUT fix verification: no _id leak, valor_final recomputed
        assert "_id" not in data, f"_id leaked in PUT response: {data}"
        assert data["descricao"] == "TEST_CP_MIN_UPDATED"
        assert data["valor"] == 150.0
        assert data.get("valor_final") == 150.0, f"valor_final should be recalculated: {data}"

    def test_quitar(self, H):
        cid = TestContasPagar.created_ids[1]
        r = requests.patch(f"{BASE_URL}/api/admin/contas-pagar/{cid}/quitar", headers=H, json={}, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "quitada"

    def test_cancelar(self, H):
        cid = TestContasPagar.created_ids[2]
        r = requests.patch(f"{BASE_URL}/api/admin/contas-pagar/{cid}/cancelar", headers=H, timeout=30)
        assert r.status_code == 200

    def test_quitar_404(self, H):
        r = requests.patch(f"{BASE_URL}/api/admin/contas-pagar/fake-id-xyz/quitar", headers=H, json={}, timeout=30)
        assert r.status_code == 404

    def test_zzz_cleanup(self, H):
        """Cleanup last - delete all created test data"""
        for cid in TestContasPagar.created_ids:
            requests.delete(f"{BASE_URL}/api/admin/contas-pagar/{cid}", headers=H, timeout=30)
        # Confirm one delete returned 404 after
        if TestContasPagar.created_ids:
            r = requests.delete(f"{BASE_URL}/api/admin/contas-pagar/fake-deleted-xyz", headers=H, timeout=30)
            assert r.status_code == 404


# =============================================================================
# FINANCEIRO — CONTAS A RECEBER
# =============================================================================
class TestContasReceber:
    created_ids = []

    def test_list(self, H):
        r = requests.get(f"{BASE_URL}/api/admin/contas-receber", headers=H, timeout=30)
        assert r.status_code == 200

    def test_create_and_quitar(self, H):
        payload = {
            "descricao": "TEST_CR_MIN",
            "valor": 200.0,
            "data_vencimento": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
        }
        r = requests.post(f"{BASE_URL}/api/admin/contas-receber", headers=H, json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # BUG FIX verification for Contas a Receber as well
        assert "_id" not in data, f"_id leaked in response: {data}"
        assert data.get("valor_final") == 200.0, f"valor_final missing: {data}"
        for f in ("created_by", "subconta_id", "subconta_nome",
                  "conta_bancaria_id", "conta_bancaria_nome",
                  "total_parcelas", "numero_parcela", "parcela_origem_id"):
            assert f in data, f"Campo ausente no response CR: {f} — data={data}"
        cid = data["id"]
        TestContasReceber.created_ids.append(cid)

        r2 = requests.patch(f"{BASE_URL}/api/admin/contas-receber/{cid}/quitar", headers=H, json={}, timeout=30)
        assert r2.status_code == 200
        body = r2.json()
        assert "_id" not in body, f"_id leaked in quitar response: {body}"
        assert body["status"] == "quitada"

    def test_parcelado_ok_receber(self, H):
        payload = {
            "descricao": "TEST_CR_PAR_OK",
            "valor_total": 600.0,
            "data_primeiro_vencimento": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "total_parcelas": 2,
            "intervalo_dias": 30,
        }
        r = requests.post(f"{BASE_URL}/api/admin/contas-receber/parcelado", headers=H, json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert len(data["parcelas"]) == 2
        for idx, p in enumerate(data["parcelas"], start=1):
            assert "_id" not in p, f"_id leaked in CR parcela: {p}"
            assert p.get("total_parcelas") == 2
            assert p.get("numero_parcela") == idx
            assert "valor_final" in p
            assert "parcela_origem_id" in p
            TestContasReceber.created_ids.append(p["id"])

    def test_parcelado_invalid(self, H):
        payload = {
            "descricao": "TEST_CR_PAR",
            "valor_total": 100.0,
            "data_primeiro_vencimento": datetime.now().strftime("%Y-%m-%d"),
            "total_parcelas": 0,
        }
        r = requests.post(f"{BASE_URL}/api/admin/contas-receber/parcelado", headers=H, json=payload, timeout=30)
        assert r.status_code == 400

    def test_cancelar_and_delete_404(self, H):
        r = requests.patch(f"{BASE_URL}/api/admin/contas-receber/fake-xx/cancelar", headers=H, timeout=30)
        assert r.status_code == 404
        r2 = requests.delete(f"{BASE_URL}/api/admin/contas-receber/fake-xx", headers=H, timeout=30)
        assert r2.status_code == 404

    def test_zzz_cleanup(self, H):
        for cid in TestContasReceber.created_ids:
            requests.delete(f"{BASE_URL}/api/admin/contas-receber/{cid}", headers=H, timeout=30)


# =============================================================================
# EMISSÃO NF-e / NFS-e
# =============================================================================
class TestEmissaoTabelas:
    def test_cfops(self, H):
        r = requests.get(f"{BASE_URL}/api/nfe/cfops", headers=H, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) == 8
        assert all("codigo" in c and "descricao" in c for c in data)

    def test_codigos_servico(self, H):
        r = requests.get(f"{BASE_URL}/api/nfse/codigos-servico", headers=H, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0
        assert all("codigo" in c and "descricao" in c for c in data)


class TestNotasEmitidas:
    def test_list_nfe(self, H):
        r = requests.get(f"{BASE_URL}/api/nfe/emitidas", headers=H, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_nfse(self, H):
        r = requests.get(f"{BASE_URL}/api/nfse/emitidas", headers=H, timeout=30)
        assert r.status_code == 200

    def test_list_all(self, H):
        r = requests.get(f"{BASE_URL}/api/notas-emitidas", headers=H, timeout=30)
        assert r.status_code == 200

    def test_get_404(self, H):
        r = requests.get(f"{BASE_URL}/api/notas-emitidas/fake-id-xyz", headers=H, timeout=30)
        assert r.status_code == 404

    def test_emitir_nfe_cert_404(self, H):
        payload = {
            "certificado_id": "fake-cert",
            "dest_cpf_cnpj": "12345678900",
            "dest_razao_social": "TEST",
            "dest_cep": "00000000",
            "dest_logradouro": "rua",
            "dest_numero": "1",
            "dest_bairro": "x",
            "dest_cidade": "y",
            "dest_uf": "SP",
            "itens": [{
                "codigo": "1", "descricao": "x", "quantidade": 1,
                "valor_unitario": 1, "valor_total": 1
            }],
            "valor_produtos": 1, "valor_total": 1,
        }
        r = requests.post(f"{BASE_URL}/api/nfe/emitir", headers=H, json=payload, timeout=30)
        assert r.status_code == 404

    def test_emitir_nfse_cert_404(self, H):
        payload = {
            "certificado_id": "fake-cert",
            "tomador_cpf_cnpj": "12345678900",
            "tomador_razao_social": "T",
            "tomador_cep": "0", "tomador_logradouro": "x", "tomador_numero": "1",
            "tomador_bairro": "x", "tomador_cidade": "y", "tomador_uf": "TO",
            "codigo_tributario_municipio": "0701",
            "item_lista_servico": "07.02",
            "discriminacao": "x",
            "valor_servicos": 100, "valor_liquido": 100,
        }
        r = requests.post(f"{BASE_URL}/api/nfse/emitir", headers=H, json=payload, timeout=30)
        assert r.status_code == 404

    def test_delete_404(self, H):
        r = requests.delete(f"{BASE_URL}/api/notas-emitidas/fake-id", headers=H, timeout=30)
        assert r.status_code == 404

    def test_download_xml_404(self, H):
        r = requests.get(f"{BASE_URL}/api/notas-emitidas/fake-id/download-xml", headers=H, timeout=30)
        assert r.status_code == 404

    def test_download_pdf_404(self, H):
        r = requests.get(f"{BASE_URL}/api/notas-emitidas/fake-id/download-pdf", headers=H, timeout=30)
        assert r.status_code == 404


# =============================================================================
# IMPORTAÇÃO NF (apenas 404 — não bater real SEFAZ)
# =============================================================================
class TestImportacaoNF:
    def test_importar_nfe_404(self, H):
        r = requests.post(f"{BASE_URL}/api/nfe/importar/fake-id", headers=H, timeout=30)
        assert r.status_code == 404

    def test_importar_nfse_404(self, H):
        r = requests.post(f"{BASE_URL}/api/nfse/importar/fake-id", headers=H, timeout=30)
        assert r.status_code == 404


# =============================================================================
# REGRESSÃO Fase 1 Parte 1 + Scheduler + Geral
# =============================================================================
class TestRegressao:
    def test_conciliacao(self, H):
        r = requests.get(f"{BASE_URL}/api/conciliacao", headers=H, timeout=30)
        assert r.status_code == 200

    def test_nfse_importadas(self, H):
        r = requests.get(f"{BASE_URL}/api/nfse/importadas", headers=H, timeout=30)
        assert r.status_code == 200

    def test_nfe_importadas(self, H):
        r = requests.get(f"{BASE_URL}/api/nfe/importadas", headers=H, timeout=30)
        assert r.status_code == 200

    def test_nfe_certificados(self, H):
        r = requests.get(f"{BASE_URL}/api/nfe/certificados", headers=H, timeout=30)
        assert r.status_code == 200

    def test_nfe_novas_count(self, H):
        r = requests.get(f"{BASE_URL}/api/nfe/novas-count", headers=H, timeout=30)
        assert r.status_code == 200
        assert "count" in r.json()

    def test_nfe_download_pdf_404(self, H):
        r = requests.get(f"{BASE_URL}/api/nfe/importadas/fake-id/download-pdf", headers=H, timeout=30)
        assert r.status_code == 404

    def test_scheduler_status(self, H):
        r = requests.get(f"{BASE_URL}/api/nf/importacao-automatica/status", headers=H, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("scheduler_ativo") is True

    def test_scheduler_logs(self, H):
        r = requests.get(f"{BASE_URL}/api/nf/importacao-automatica/logs", headers=H, timeout=30)
        assert r.status_code == 200

    def test_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": EMAIL, "password": PASSWORD}, timeout=30)
        assert r.status_code == 200
        assert "token" in r.json()

    def test_dashboard(self, H):
        r = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=H, timeout=30)
        assert r.status_code == 200

    def test_centros_custo(self, H):
        r = requests.get(f"{BASE_URL}/api/admin/centros-custo", headers=H, timeout=30)
        assert r.status_code == 200

    def test_plano_contas(self, H):
        r = requests.get(f"{BASE_URL}/api/admin/plano-contas", headers=H, timeout=30)
        assert r.status_code == 200

    def test_export_pdf_contas_pagar(self, H):
        r = requests.get(f"{BASE_URL}/api/export/pdf/contas_pagar", headers=H, timeout=60)
        assert r.status_code == 200
        assert r.content[:5] == b"%PDF-"
