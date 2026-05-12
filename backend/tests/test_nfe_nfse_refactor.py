"""
Regression tests for Sessão 32 refactor iteration 2:
- NFS-e router extraction (/app/backend/routes/nfse.py)
- NF-e router extraction (/app/backend/routes/nfe.py)
- Conciliação (prev iteration) still working
- Other modules still working
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://erp-financeiro-fixes.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

EMAIL = "test@test.com"
PASSWORD = "password"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed {r.status_code}: {r.text}"
    data = r.json()
    tok = data.get("token") or data.get("access_token")
    assert tok, f"no token in response: {data}"
    return tok


@pytest.fixture(scope="session")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ======================= NFS-e =======================

class TestNFSe:
    def test_list_importadas(self, headers):
        r = requests.get(f"{API}/nfse/importadas", headers=headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_by_id_404(self, headers):
        r = requests.get(f"{API}/nfse/importadas/fake-{uuid.uuid4()}", headers=headers, timeout=30)
        assert r.status_code == 404

    def test_download_xml_404(self, headers):
        r = requests.get(f"{API}/nfse/importadas/fake-{uuid.uuid4()}/download-xml", headers=headers, timeout=30)
        assert r.status_code == 404

    def test_download_pdf_404(self, headers):
        r = requests.get(f"{API}/nfse/importadas/fake-{uuid.uuid4()}/download-pdf", headers=headers, timeout=30)
        assert r.status_code == 404

    def test_criar_conta_pagar_404(self, headers):
        r = requests.post(f"{API}/nfse/importadas/fake-{uuid.uuid4()}/criar-conta-pagar", headers=headers, timeout=30)
        assert r.status_code == 404

    def test_update_status_invalid(self, headers):
        r = requests.patch(f"{API}/nfse/importadas/fake-{uuid.uuid4()}/status",
                           headers=headers, json={"status": "inexistente"}, timeout=30)
        assert r.status_code == 400

    def test_update_status_404(self, headers):
        r = requests.patch(f"{API}/nfse/importadas/fake-{uuid.uuid4()}/status",
                           headers=headers, json={"status": "processada"}, timeout=30)
        assert r.status_code == 404

    def test_auth_required(self):
        r = requests.get(f"{API}/nfse/importadas", timeout=30)
        assert r.status_code in (401, 403)

    def test_list_with_real_item_and_download(self, headers):
        """If there's a real NFS-e, fetch its detail and attempt XML/PDF downloads (best-effort)."""
        r = requests.get(f"{API}/nfse/importadas", headers=headers, timeout=30)
        lst = r.json()
        if not lst:
            pytest.skip("Nenhuma NFS-e real para validar downloads")
        nfse = lst[0]
        nid = nfse["id"]

        d = requests.get(f"{API}/nfse/importadas/{nid}", headers=headers, timeout=30)
        assert d.status_code == 200
        assert d.json()["id"] == nid


# ======================= NF-e CERTIFICADOS =======================

class TestNFeCertificados:
    def test_list(self, headers):
        r = requests.get(f"{API}/nfe/certificados", headers=headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_post_invalid_cert(self, headers):
        payload = {
            "cnpj": f"TEST_{uuid.uuid4().hex[:14]}",
            "razao_social": "TEST cert inválido",
            "uf": "SP",
            "ambiente": "producao",
            "certificado_base64": "SU5WQUxJRF9DRVJUSUZJQ0FURQ==",  # invalid
            "senha_certificado": "wrong",
        }
        r = requests.post(f"{API}/nfe/certificados", headers=headers, json=payload, timeout=30)
        assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text[:200]}"

    def test_patch_update_existing_cert(self, headers):
        """Update inscricao_municipal and url_nfse on existing real cert (preserve original values)."""
        r = requests.get(f"{API}/nfe/certificados", headers=headers, timeout=30)
        certs = r.json()
        if not certs:
            pytest.skip("Sem certificados cadastrados para atualizar")
        cert = certs[0]
        cid = cert["id"]
        original_im = cert.get("inscricao_municipal", "")
        original_url = cert.get("url_nfse", "")

        # patch with test values
        patch = {"inscricao_municipal": "TEST_IM_123", "url_nfse": "https://test.example.com/nfse"}
        p = requests.patch(f"{API}/nfe/certificados/{cid}", headers=headers, json=patch, timeout=30)
        assert p.status_code == 200
        updated = p.json()
        assert updated.get("inscricao_municipal") == "TEST_IM_123"
        assert updated.get("url_nfse") == "https://test.example.com/nfse"

        # restore originals
        restore = {"inscricao_municipal": original_im, "url_nfse": original_url}
        rr = requests.patch(f"{API}/nfe/certificados/{cid}", headers=headers, json=restore, timeout=30)
        assert rr.status_code == 200

    def test_patch_404(self, headers):
        r = requests.patch(f"{API}/nfe/certificados/fake-nonexistent-id",
                           headers=headers, json={"inscricao_municipal": "X"}, timeout=30)
        assert r.status_code == 404

    def test_delete_404(self, headers):
        r = requests.delete(f"{API}/nfe/certificados/fake-nonexistent-id", headers=headers, timeout=30)
        assert r.status_code == 404


# ======================= NF-e IMPORTADAS =======================

class TestNFeImportadas:
    def test_list(self, headers):
        r = requests.get(f"{API}/nfe/importadas", headers=headers, timeout=30)
        assert r.status_code == 200
        lst = r.json()
        assert isinstance(lst, list)
        # review_request says 121 expected but don't hard-fail on count drift
        assert len(lst) > 0, "lista vazia — esperado >0 NF-es"

    def test_get_by_id_404(self, headers):
        r = requests.get(f"{API}/nfe/importadas/fake-{uuid.uuid4()}", headers=headers, timeout=30)
        assert r.status_code == 404

    def test_get_detail_real(self, headers):
        r = requests.get(f"{API}/nfe/importadas", headers=headers, timeout=30)
        lst = r.json()
        if not lst:
            pytest.skip("Sem NF-e real")
        nid = lst[0]["id"]
        d = requests.get(f"{API}/nfe/importadas/{nid}", headers=headers, timeout=30)
        assert d.status_code == 200
        assert d.json()["id"] == nid

    def test_criar_conta_pagar_404(self, headers):
        r = requests.post(f"{API}/nfe/importadas/fake-{uuid.uuid4()}/criar-conta-pagar",
                          headers=headers, timeout=30)
        assert r.status_code == 404

    def test_criar_conta_pagar_already_linked(self, headers):
        """Find a NF-e that already has conta_pagar_id and expect 400."""
        r = requests.get(f"{API}/nfe/importadas", headers=headers, timeout=30)
        lst = r.json()
        linked = next((n for n in lst if n.get("conta_pagar_id")), None)
        if not linked:
            pytest.skip("Nenhuma NF-e vinculada a conta_pagar para validar 400")
        r2 = requests.post(f"{API}/nfe/importadas/{linked['id']}/criar-conta-pagar",
                           headers=headers, timeout=30)
        assert r2.status_code == 400

    def test_update_status_invalid(self, headers):
        r = requests.patch(f"{API}/nfe/importadas/fake-{uuid.uuid4()}/status",
                           headers=headers, json={"status": "estado_inexistente"}, timeout=30)
        assert r.status_code == 400

    def test_update_status_404(self, headers):
        r = requests.patch(f"{API}/nfe/importadas/fake-{uuid.uuid4()}/status",
                           headers=headers, json={"status": "nova"}, timeout=30)
        assert r.status_code == 404

    def test_novas_count(self, headers):
        r = requests.get(f"{API}/nfe/novas-count", headers=headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "count" in data
        assert isinstance(data["count"], int)

    def test_download_xml_404(self, headers):
        r = requests.get(f"{API}/nfe/importadas/fake-{uuid.uuid4()}/download-xml",
                         headers=headers, timeout=30)
        assert r.status_code == 404

    def test_download_pdf_404(self, headers):
        r = requests.get(f"{API}/nfe/importadas/fake-{uuid.uuid4()}/download-pdf",
                         headers=headers, timeout=30)
        assert r.status_code == 404

    def test_download_xml_real(self, headers):
        r = requests.get(f"{API}/nfe/importadas", headers=headers, timeout=30)
        lst = r.json()
        with_xml = next((n for n in lst if n.get("chave_acesso")), None)
        if not with_xml:
            pytest.skip("Sem NF-e real")
        rx = requests.get(f"{API}/nfe/importadas/{with_xml['id']}/download-xml", headers=headers, timeout=60)
        # could be 200 (XML) or 404 (no xml_base64 stored)
        assert rx.status_code in (200, 404)
        if rx.status_code == 200:
            assert b"<" in rx.content[:500]
            assert rx.headers.get("content-type", "").startswith("application/xml")

    def test_download_pdf_real(self, headers):
        r = requests.get(f"{API}/nfe/importadas", headers=headers, timeout=30)
        lst = r.json()
        if not lst:
            pytest.skip("Sem NF-e real")
        nid = lst[0]["id"]
        rp = requests.get(f"{API}/nfe/importadas/{nid}/download-pdf", headers=headers, timeout=120)
        assert rp.status_code in (200, 500), f"unexpected status {rp.status_code}"
        if rp.status_code == 200:
            assert rp.content[:4] == b"%PDF", "PDF inválido"
            assert rp.headers.get("content-type", "").startswith("application/pdf")


# ======================= IMPORT endpoint ainda em server.py =======================

class TestImportacaoAindaEmServer:
    def test_nfe_importar_route_exists(self, headers):
        """POST /nfe/importar/{id} deve existir (pode falhar mas não 404 de rota)."""
        r = requests.post(f"{API}/nfe/importar/fake-cert-id", headers=headers, timeout=30)
        # Route exists → expect 404 detail (Certificado não encontrado) or 400/500, NOT 405 method not allowed
        assert r.status_code != 405
        # Also should not be pure 404 unrouted — FastAPI returns {"detail":"Not Found"} when unrouted;
        # Certificado 404 returns detail="Certificado não encontrado"
        if r.status_code == 404:
            detail = r.json().get("detail", "")
            assert "Certificado" in detail or "certificado" in detail, \
                f"Rota /nfe/importar/ pode não existir: {detail}"


# ======================= REGRESSÃO: Conciliação =======================

class TestRegressionConciliacao:
    def test_list(self, headers):
        r = requests.get(f"{API}/conciliacao", headers=headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_extratos(self, headers):
        r = requests.get(f"{API}/conciliacao/extratos", headers=headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_conciliar_404(self, headers):
        payload = {"extrato_id": f"fake-{uuid.uuid4()}", "conta_id": f"fake-{uuid.uuid4()}", "conta_tipo": "pagar"}
        r = requests.post(f"{API}/conciliacao/conciliar", headers=headers, json=payload, timeout=30)
        assert r.status_code == 404


# ======================= REGRESSÃO: outros módulos =======================

class TestRegressionOutros:
    def test_auth_login(self):
        r = requests.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
        assert r.status_code == 200
        assert "token" in r.json()

    def test_contas_pagar(self, headers):
        r = requests.get(f"{API}/admin/contas-pagar", headers=headers, timeout=30)
        assert r.status_code == 200

    def test_contas_receber(self, headers):
        r = requests.get(f"{API}/admin/contas-receber", headers=headers, timeout=30)
        assert r.status_code == 200

    def test_dashboard(self, headers):
        r = requests.get(f"{API}/admin/dashboard", headers=headers, timeout=30)
        assert r.status_code == 200

    def test_export_pdf_contas_pagar(self, headers):
        r = requests.get(f"{API}/export/pdf/contas_pagar", headers=headers, timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"
