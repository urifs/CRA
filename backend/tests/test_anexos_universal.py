"""
Tests for universal AnexosManager backend integration.
Validates GET (lista vazia para IDs inválidos) e POST upload (multipart).
"""
import os
import io
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://erp-fixes-preview.preview.emergentagent.com").rstrip("/")

CREDS = {"email": "test@test.com", "password": "password"}


@pytest.fixture(scope="module")
def auth_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=CREDS, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("token") or data.get("access_token")
    assert token, f"No token in response: {data}"
    return token


@pytest.fixture(scope="module")
def headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# -------- GET lista vazia (IDs inexistentes) --------
@pytest.mark.parametrize("entity_type,entity_id", [
    ("manutencao", "nonexistent-id-12345"),
    ("epi_ficha", "nonexistent-id-12345"),
    ("folha_pagamento", "nonexistent-id-12345"),
    ("custo_rh", "config-global"),
    ("medicao", "nonexistent-id-12345"),
    ("horimetro", "nonexistent-id-12345"),
    ("combustivel", "nonexistent-id-12345"),
])
def test_list_anexos_empty(headers, entity_type, entity_id):
    r = requests.get(f"{BASE_URL}/api/anexos/{entity_type}/{entity_id}", headers=headers, timeout=30)
    assert r.status_code == 200, f"{entity_type}/{entity_id} -> {r.status_code} {r.text}"
    body = r.json()
    assert "items" in body and "count" in body
    assert isinstance(body["items"], list)
    # Para IDs claramente inexistentes count deve ser 0; custo_rh/config-global pode ter dados,
    # então só validamos estrutura para esse caso.
    if entity_id == "nonexistent-id-12345":
        assert body["count"] == 0


# -------- Validação entity_type inválido --------
def test_invalid_entity_type(headers):
    r = requests.get(f"{BASE_URL}/api/anexos/invalid_type_xyz/some-id", headers=headers, timeout=30)
    assert r.status_code == 400


# -------- POST upload (multipart) para manutencao --------
def test_upload_anexo_manutencao(headers):
    file_content = b"Hello world, test anexo manutencao - TEST_anexos_universal"
    files = {"file": ("test_anexo_manut.txt", io.BytesIO(file_content), "text/plain")}
    entity_id = "TEST_manut_id_anexos_universal"

    r = requests.post(
        f"{BASE_URL}/api/anexos/manutencao/{entity_id}/upload",
        headers=headers,
        files=files,
        timeout=30,
    )
    assert r.status_code == 200, f"Upload failed: {r.status_code} {r.text}"
    body = r.json()
    assert "anexo" in body
    anexo = body["anexo"]
    assert anexo["entity_type"] == "manutencao"
    assert anexo["entity_id"] == entity_id
    assert anexo["source"] == "local"
    assert anexo["original_name"] == "test_anexo_manut.txt"
    assert anexo["size"] == len(file_content)
    anexo_id = anexo["id"]

    # Verifica GET após criação
    r2 = requests.get(f"{BASE_URL}/api/anexos/manutencao/{entity_id}", headers=headers, timeout=30)
    assert r2.status_code == 200
    items = r2.json()["items"]
    assert any(a["id"] == anexo_id for a in items)

    # Cleanup: delete
    r3 = requests.delete(
        f"{BASE_URL}/api/anexos/manutencao/{entity_id}/{anexo_id}",
        headers=headers,
        timeout=30,
    )
    assert r3.status_code == 200

    # Confirma exclusão
    r4 = requests.get(f"{BASE_URL}/api/anexos/manutencao/{entity_id}", headers=headers, timeout=30)
    assert r4.status_code == 200
    assert all(a["id"] != anexo_id for a in r4.json()["items"])


# -------- POST upload epi_ficha (verifica nome correto, NÃO 'ficha_epi') --------
def test_upload_anexo_epi_ficha(headers):
    files = {"file": ("test_epi.txt", io.BytesIO(b"epi ficha test"), "text/plain")}
    entity_id = "TEST_epi_ficha_id"
    r = requests.post(
        f"{BASE_URL}/api/anexos/epi_ficha/{entity_id}/upload",
        headers=headers, files=files, timeout=30,
    )
    assert r.status_code == 200, f"{r.status_code} {r.text}"
    anexo_id = r.json()["anexo"]["id"]
    # cleanup
    requests.delete(
        f"{BASE_URL}/api/anexos/epi_ficha/{entity_id}/{anexo_id}",
        headers=headers, timeout=30,
    )


# -------- Reject ficha_epi (nome errado) --------
def test_reject_wrong_entity_name_ficha_epi(headers):
    r = requests.get(f"{BASE_URL}/api/anexos/ficha_epi/any-id", headers=headers, timeout=30)
    assert r.status_code == 400  # 'ficha_epi' NÃO está na lista; o correto é 'epi_ficha'


# -------- 401 sem token --------
def test_requires_auth():
    r = requests.get(f"{BASE_URL}/api/anexos/manutencao/any-id", timeout=30)
    assert r.status_code in (401, 403)
