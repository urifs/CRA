"""E2E tests for Folha de Pagamento (PDF Importation) module.

Covers RH endpoints + Financeiro acceptance flow.
"""
import os
import io
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback: parse from /app/frontend/.env
    try:
        with open("/app/frontend/.env") as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL"):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                    break
    except Exception:
        pass
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"

PDF_URL = (
    "https://customer-assets.emergentagent.com/job_21e279ba-21c4-411a-94e8-db609ecbdb3a/"
    "artifacts/nnufixlx_1341_3_RECIBO%20DE%20PAGAMENTO%20%281%29.pdf"
)
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "password"


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    return s


@pytest.fixture(scope="module")
def auth_token(session):
    r = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} {r.text[:200]}")
    data = r.json()
    token = data.get("token") or data.get("access_token")
    if not token:
        pytest.skip("No token returned from login")
    session.headers.update({"Authorization": f"Bearer {token}"})
    return token


@pytest.fixture(scope="module")
def pdf_bytes():
    r = requests.get(PDF_URL, timeout=60)
    assert r.status_code == 200, f"Could not download test PDF: {r.status_code}"
    assert len(r.content) > 1000
    return r.content


@pytest.fixture(scope="module")
def plano_contas_id(session, auth_token):
    r = session.get(f"{BASE_URL}/api/admin/plano-contas", timeout=30)
    if r.status_code != 200:
        pytest.skip(f"plano-contas list failed: {r.status_code}")
    items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
    if not items:
        pytest.skip("No plano-contas available")
    # Prefer one labeled DESPESA or first
    for it in items:
        if "FOLHA" in (it.get("nome") or "").upper() or "PESSOAL" in (it.get("nome") or "").upper():
            return it["id"]
    return items[0]["id"]


@pytest.fixture(scope="module")
def state():
    """Shared state across ordered tests."""
    return {}


# ---------- Sanity ----------
class TestFolhaSanity:
    def test_list_initially_works(self, session, auth_token):
        r = session.get(f"{BASE_URL}/api/folha-pagamento", timeout=30)
        assert r.status_code == 200, r.text[:300]
        assert isinstance(r.json(), list)

    def test_solicitacoes_endpoint_works(self, session, auth_token):
        r = session.get(
            f"{BASE_URL}/api/financeiro/solicitacoes-folha?status=pendente", timeout=30
        )
        assert r.status_code == 200, r.text[:300]
        assert isinstance(r.json(), list)


# ---------- Importação OCR ----------
class TestFolhaImportar:
    def test_importar_via_ocr_gemini(self, session, auth_token, pdf_bytes, state):
        files = {"arquivo": ("folha_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        # Retry once for transient preview-env 502s
        r = None
        for attempt in range(3):
            try:
                r = session.post(
                    f"{BASE_URL}/api/folha-pagamento/importar",
                    files={"arquivo": ("folha_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                    timeout=240,
                )
                if r.status_code == 200:
                    break
                # Transient gateway -> wait and retry
                if r.status_code in (502, 503, 504):
                    time.sleep(10)
                    continue
                break
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                time.sleep(10)
                continue
        assert r is not None and r.status_code == 200, f"Import failed: {getattr(r, 'status_code', '?')} {getattr(r, 'text', '')[:500]}"
        doc = r.json()
        assert doc["status"] == "em_revisao"
        assert isinstance(doc["funcionarios"], list)
        assert doc["total_funcionarios"] == len(doc["funcionarios"])
        # PDF has 6 unique employees
        assert doc["total_funcionarios"] == 6, f"Expected 6 employees, got {doc['total_funcionarios']}"
        # Total ~22215.20 (allow small tolerance)
        total = float(doc.get("total_geral_liquido") or 0)
        assert 22000 <= total <= 22500, f"Total mismatch: {total}"
        assert doc.get("master_pdf_path"), "master_pdf_path missing"
        # Each func must have linha_id and either anexo or paginas
        for f in doc["funcionarios"]:
            assert f.get("linha_id")
            assert "match_status" in f
        state["folha_id"] = doc["id"]
        state["funcionarios"] = doc["funcionarios"]

    def test_get_folha(self, session, auth_token, state):
        fid = state.get("folha_id")
        if not fid:
            pytest.skip("import didn't run")
        r = session.get(f"{BASE_URL}/api/folha-pagamento/{fid}", timeout=30)
        assert r.status_code == 200
        assert r.json()["id"] == fid

    def test_master_pdf_download(self, session, auth_token, state):
        fid = state.get("folha_id")
        if not fid:
            pytest.skip("import didn't run")
        r = session.get(f"{BASE_URL}/api/folha-pagamento/{fid}/master-pdf", timeout=60)
        assert r.status_code == 200
        ct = r.headers.get("content-type", "")
        assert "pdf" in ct.lower(), ct
        assert r.content[:4] == b"%PDF", "Not a PDF response"

    def test_holerite_individual_download(self, session, auth_token, state):
        fid = state.get("folha_id")
        funcs = state.get("funcionarios") or []
        if not fid or not funcs:
            pytest.skip("import didn't run")
        # Find a func with anexo path (paginas)
        target = next((f for f in funcs if f.get("anexo_holerite_path")), funcs[0])
        lid = target["linha_id"]
        r = session.get(
            f"{BASE_URL}/api/folha-pagamento/{fid}/holerite/{lid}", timeout=60
        )
        if r.status_code == 404 and not target.get("anexo_holerite_path"):
            pytest.skip("This linha had no anexo")
        assert r.status_code == 200, r.text[:200]
        assert "pdf" in r.headers.get("content-type", "").lower()
        assert r.content[:4] == b"%PDF"


# ---------- Resolver matches + Envio ----------
class TestResolverEEnvio:
    def test_enviar_modo_cheio_bloqueia_se_low_match(self, session, auth_token, state):
        """If any funcionario has no match, sending with modo=cheio must return 400."""
        fid = state.get("folha_id")
        funcs = state.get("funcionarios") or []
        if not fid:
            pytest.skip("no folha")
        sem_match = [f for f in funcs if not f.get("funcionario_id")]
        if not sem_match:
            pytest.skip("All matched on import - cannot validate 400 path")
        r = session.post(
            f"{BASE_URL}/api/folha-pagamento/{fid}/enviar-financeiro",
            json={"modo": "cheio"},
            timeout=30,
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text[:200]}"
        assert "mapping" in r.text.lower() or "match" in r.text.lower()

    def test_resolver_matches_para_low(self, session, auth_token, state):
        """For any funcionario without match, force-map to any active funcionario."""
        fid = state.get("folha_id")
        funcs = state.get("funcionarios") or []
        if not fid:
            pytest.skip("no folha")
        sem_match = [f for f in funcs if not f.get("funcionario_id")]
        if not sem_match:
            pytest.skip("nothing to resolve")
        # Get an active funcionario id
        r = session.get(f"{BASE_URL}/api/rh/funcionarios", timeout=30)
        assert r.status_code == 200, r.text[:200]
        all_funcs = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
        ativos = [x for x in all_funcs if (x.get("status") or "").lower() == "ativo"]
        if not ativos:
            ativos = all_funcs
        assert ativos, "No funcionarios in DB to map onto"
        any_id = ativos[0]["id"]
        payload = {
            "funcionarios": [
                {"linha_id": f["linha_id"], "funcionario_id": any_id} for f in sem_match
            ]
        }
        r = session.post(
            f"{BASE_URL}/api/folha-pagamento/{fid}/resolver-matches",
            json=payload,
            timeout=30,
        )
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert body["ok"] is True
        assert body["atualizados"] == len(sem_match)

        # Re-fetch to confirm
        r2 = session.get(f"{BASE_URL}/api/folha-pagamento/{fid}", timeout=30)
        assert r2.status_code == 200
        d2 = r2.json()
        ainda_sem = [f for f in d2["funcionarios"] if not f.get("funcionario_id")]
        assert not ainda_sem, "Still missing matches after resolver"
        state["funcionarios"] = d2["funcionarios"]

    def test_enviar_individual_apos_resolver(self, session, auth_token, state):
        fid = state.get("folha_id")
        if not fid:
            pytest.skip("no folha")
        r = session.post(
            f"{BASE_URL}/api/folha-pagamento/{fid}/enviar-financeiro",
            json={"modo": "individual", "observacao": "TEST_envio_individual"},
            timeout=30,
        )
        assert r.status_code == 200, r.text[:300]
        sol = r.json()
        assert sol["status"] == "pendente"
        assert sol["modo"] == "individual"
        assert sol["folha_id"] == fid
        state["sol_id"] = sol["id"]

        # Folha now in 'enviada'
        r2 = session.get(f"{BASE_URL}/api/folha-pagamento/{fid}", timeout=30)
        assert r2.json()["status"] == "enviada"


# ---------- Financeiro: aceitar/rejeitar ----------
class TestFinanceiroAceite:
    def test_listar_solicitacoes_pendente(self, session, auth_token, state):
        sol_id = state.get("sol_id")
        if not sol_id:
            pytest.skip("no solicitacao")
        r = session.get(
            f"{BASE_URL}/api/financeiro/solicitacoes-folha?status=pendente", timeout=30
        )
        assert r.status_code == 200
        ids = [s["id"] for s in r.json()]
        assert sol_id in ids
        # Each must have funcionarios_preview enriched
        target = next(s for s in r.json() if s["id"] == sol_id)
        assert "funcionarios_preview" in target

    def test_aceitar_modo_individual(self, session, auth_token, state, plano_contas_id):
        sol_id = state.get("sol_id")
        if not sol_id:
            pytest.skip("no solicitacao")
        payload = {
            "plano_contas_id": plano_contas_id,
            "data_vencimento": "2026-06-05",
            "observacao": "TEST_aceite_individual",
        }
        r = session.post(
            f"{BASE_URL}/api/financeiro/solicitacoes-folha/{sol_id}/aceitar",
            json=payload,
            timeout=60,
        )
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        assert body["ok"] is True
        assert body["modo"] == "individual"
        # Should create N contas where N == total_funcionarios (6)
        assert body["total"] == 6, f"Expected 6 contas, got {body['total']}"
        assert len(body["contas_criadas"]) == 6
        state["contas_pagar_ids"] = body["contas_criadas"]

        # Verify solicitacao now 'aceita'
        r2 = session.get(
            f"{BASE_URL}/api/financeiro/solicitacoes-folha/{sol_id}", timeout=30
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "aceita"

        # Verify folha now 'aceita'
        fid = state["folha_id"]
        r3 = session.get(f"{BASE_URL}/api/folha-pagamento/{fid}", timeout=30)
        assert r3.json()["status"] == "aceita"

    def test_contas_pagar_criadas_com_anexos(self, session, auth_token, state):
        ids = state.get("contas_pagar_ids") or []
        if not ids:
            pytest.skip("no contas")
        # Query MongoDB directly since GET /admin/contas-pagar/{id} doesn't exist
        from pymongo import MongoClient
        mongo_url = os.environ["MONGO_URL"].strip().strip('"').strip("'")
        db_name = os.environ["DB_NAME"].strip().strip('"').strip("'")
        mc = MongoClient(mongo_url)
        db = mc[db_name]
        contas = list(db["contas_pagar"].find({"id": {"$in": ids}}, {"_id": 0}))
        mc.close()
        assert len(contas) == len(ids), f"Found {len(contas)}/{len(ids)} contas"
        total_valor = 0.0
        contas_com_anexo = 0
        for c in contas:
            total_valor += float(c.get("valor") or 0)
            anexos = c.get("anexos") or []
            if anexos:
                contas_com_anexo += 1
            assert c.get("origem") == "folha_pagamento"
            assert c.get("data_vencimento") == "2026-06-05"
        # Total close to ~22215.20
        assert 22000 <= total_valor <= 22500, f"Sum mismatch: {total_valor}"
        assert contas_com_anexo == len(ids), f"Only {contas_com_anexo}/{len(ids)} have anexo"

    def test_rejeitar_path_independente(self, session, auth_token, pdf_bytes, plano_contas_id):
        """Reimport a small flow and reject. Uses minimal cycle to validate /rejeitar."""
        # Import again
        files = {"arquivo": ("folha_rej.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        r = session.post(
            f"{BASE_URL}/api/folha-pagamento/importar", files=files, timeout=180
        )
        if r.status_code != 200:
            pytest.skip(f"reimport for reject test failed: {r.status_code}")
        d = r.json()
        fid2 = d["id"]
        # Resolve any low matches
        funcs = d["funcionarios"]
        sem = [f for f in funcs if not f.get("funcionario_id")]
        if sem:
            rf = session.get(f"{BASE_URL}/api/rh/funcionarios", timeout=30)
            allf = rf.json() if isinstance(rf.json(), list) else rf.json().get("items", [])
            if not allf:
                pytest.skip("no funcionarios in DB")
            target_id = allf[0]["id"]
            session.post(
                f"{BASE_URL}/api/folha-pagamento/{fid2}/resolver-matches",
                json={"funcionarios": [{"linha_id": f["linha_id"], "funcionario_id": target_id} for f in sem]},
                timeout=30,
            )
        # Enviar
        re = session.post(
            f"{BASE_URL}/api/folha-pagamento/{fid2}/enviar-financeiro",
            json={"modo": "cheio"},
            timeout=30,
        )
        assert re.status_code == 200, re.text[:200]
        sol2 = re.json()["id"]
        # Rejeitar
        rj = session.post(
            f"{BASE_URL}/api/financeiro/solicitacoes-folha/{sol2}/rejeitar",
            json={"motivo": "TEST_motivo_rejeicao"},
            timeout=30,
        )
        assert rj.status_code == 200, rj.text[:200]
        # Verify status
        rs = session.get(
            f"{BASE_URL}/api/financeiro/solicitacoes-folha/{sol2}", timeout=30
        )
        assert rs.json()["status"] == "rejeitada"
        rfh = session.get(f"{BASE_URL}/api/folha-pagamento/{fid2}", timeout=30)
        assert rfh.json()["status"] == "rejeitada"
        # Save for cleanup
        os.environ["_TEST_REJ_FOLHA_ID"] = fid2
        os.environ["_TEST_REJ_SOL_ID"] = sol2


# ---------- Cleanup ----------
class TestCleanup:
    def test_cleanup_test_data(self, session, auth_token, state):
        """Best-effort cleanup of folha + solicitacao + contas_pagar."""
        from pymongo import MongoClient
        try:
            mc = MongoClient(os.environ["MONGO_URL"].strip().strip('"').strip("'"))
            dbn = os.environ["DB_NAME"].strip().strip('"').strip("'")
            db = mc[dbn]
            fids = [state.get("folha_id"), os.environ.get("_TEST_REJ_FOLHA_ID")]
            sids = [state.get("sol_id"), os.environ.get("_TEST_REJ_SOL_ID")]
            cids = state.get("contas_pagar_ids") or []
            fids = [x for x in fids if x]
            sids = [x for x in sids if x]
            if cids:
                db["contas_pagar"].delete_many({"id": {"$in": cids}})
            if sids:
                db["solicitacoes_folha_financeiro"].delete_many({"id": {"$in": sids}})
            if fids:
                db["contas_pagar"].delete_many({"folha_id": {"$in": fids}})
                db["solicitacoes_folha_financeiro"].delete_many({"folha_id": {"$in": fids}})
                db["folhas_importadas"].delete_many({"id": {"$in": fids}})
            mc.close()
        except Exception as e:
            print(f"Cleanup warning: {e}")
        assert True
