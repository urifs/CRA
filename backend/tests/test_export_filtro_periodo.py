"""Regressão: filtro de período no /export/items/{collection} (Sessão 46.2).

Bug reportado: ao escolher período de hoje em Exportação de Relatórios,
a lista de "Contas Pendentes" continuava mostrando todos os itens em aberto,
incluindo contas vencendo em meses anteriores. Causa: o endpoint
/api/export/items/{collection} não aceitava data_inicio/data_fim.
"""
import os
import requests

API = os.environ.get("REACT_APP_BACKEND_URL", "https://os-multiplos-valores.preview.emergentagent.com")
URL = f"{API}/api"


def _login():
    r = requests.post(
        f"{URL}/auth/login",
        json={"email": "test@test.com", "password": "password"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def test_export_items_sem_filtro_retorna_todos():
    token = _login()
    r = requests.get(
        f"{URL}/export/items/contas_pagar_pendente",
        headers=_h(token),
        timeout=30,
    )
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert len(items) > 0  # ambiente seed tem contas pendentes


def test_export_items_filtra_por_data_inicio_data_fim_dia_unico():
    """Período de 1 único dia onde NÃO há contas — deve retornar lista vazia."""
    token = _login()
    r = requests.get(
        f"{URL}/export/items/contas_pagar_pendente",
        params={"data_inicio": "2030-12-25", "data_fim": "2030-12-25"},
        headers=_h(token),
        timeout=30,
    )
    assert r.status_code == 200
    items = r.json()
    assert items == []


def test_export_items_filtra_periodo_intervalo_inclui_apenas_data_no_range():
    """Verifica que somente itens cujo data_vencimento está no intervalo aparecem."""
    token = _login()
    r = requests.get(
        f"{URL}/export/items/contas_pagar_pendente",
        params={"data_inicio": "2026-04-01", "data_fim": "2026-04-30"},
        headers=_h(token),
        timeout=30,
    )
    assert r.status_code == 200
    items = r.json()
    for it in items:
        dv = it.get("data_vencimento") or ""
        assert "2026-04-01" <= dv <= "2026-04-30", f"item fora do range: {it}"


def test_export_items_contas_receber_pendente_aceita_filtro():
    token = _login()
    r = requests.get(
        f"{URL}/export/items/contas_receber_pendente",
        params={"data_inicio": "2030-01-01", "data_fim": "2030-01-31"},
        headers=_h(token),
        timeout=30,
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)
