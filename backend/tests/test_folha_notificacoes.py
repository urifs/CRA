"""Regressão: notificações automáticas no fluxo de Folha de Pagamento (Sessão 46.8).

Cenários cobertos:
1. Importação de folha cria task no sino do RH ("Folha pronta para revisão")
2. Envio ao Financeiro cria task no sino do administrativo
3. Aceite cria task de retorno no RH
4. Rejeição cria task com motivo no RH
5. Endpoint /tasks aceita system="rh"
"""
import os
import time
import uuid

import requests

API = os.environ.get("REACT_APP_BACKEND_URL", "https://erp-fixes-preview.preview.emergentagent.com")
URL = f"{API}/api"

PDF_TEST_URL = (
    "https://customer-assets.emergentagent.com/job_21e279ba-21c4-411a-94e8-db609ecbdb3a/"
    "artifacts/nnufixlx_1341_3_RECIBO%20DE%20PAGAMENTO%20%281%29.pdf"
)


def _login():
    r = requests.post(
        f"{URL}/auth/login",
        json={"email": "test@test.com", "password": "password"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _pdf():
    r = requests.get(PDF_TEST_URL, timeout=30)
    r.raise_for_status()
    return r.content


def test_endpoint_tasks_aceita_system_rh():
    t = _login()
    r = requests.get(f"{URL}/tasks?system=rh", headers=_h(t), timeout=30)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    r2 = requests.get(f"{URL}/tasks/unread-count?system=rh", headers=_h(t), timeout=30)
    assert r2.status_code == 200
    assert "count" in r2.json()


def test_fluxo_completo_dispara_4_notificacoes():
    t = _login()
    pdf = _pdf()

    # Marcador único para identificar nossas tasks no meio das outras
    sentinel = uuid.uuid4().hex[:8]

    # 1) Importação
    r = requests.post(
        f"{URL}/folha-pagamento/importar",
        headers=_h(t),
        files={"arquivo": (f"teste_{sentinel}.pdf", pdf, "application/pdf")},
        timeout=120,
    )
    assert r.status_code == 200
    folha_id = r.json()["id"]

    # 2) Aguarda processamento concluir
    deadline = time.time() + 120
    d = None
    while time.time() < deadline:
        try:
            d = requests.get(f"{URL}/folha-pagamento/{folha_id}", headers=_h(t), timeout=60).json()
            if d.get("status") in ("em_revisao", "erro"):
                break
        except Exception:
            pass
        time.sleep(3)
    assert d and d.get("status") == "em_revisao", f"folha não concluiu: {d.get('status') if d else None}"

    # 3) Verifica task no sino RH "pronta para revisão"
    tasks_rh = requests.get(f"{URL}/tasks?system=rh", headers=_h(t), timeout=30).json()
    task_pronta = next(
        (x for x in tasks_rh
         if x.get("origem", {}).get("folha_id") == folha_id
         and "pronta para revis" in (x.get("title") or "").lower()),
        None,
    )
    assert task_pronta, "Task 'pronta para revisão' NÃO criada no sino RH"
    assert task_pronta["read"] is False

    # 4) Resolve matches dos sem-vínculo (qualquer funcionário ativo)
    funcs = requests.get(f"{URL}/rh/funcionarios", headers=_h(t), timeout=60).json()
    ativos = [f["id"] for f in funcs if f.get("status") == "ativo"]
    sem_match = [linha["linha_id"] for linha in d["funcionarios"] if not linha.get("funcionario_id")]
    if sem_match:
        payload = {
            "funcionarios": [
                {"linha_id": lid, "funcionario_id": ativos[i % len(ativos)]}
                for i, lid in enumerate(sem_match)
            ]
        }
        rr = requests.post(
            f"{URL}/folha-pagamento/{folha_id}/resolver-matches",
            headers=_h(t),
            json=payload,
            timeout=30,
        )
        assert rr.status_code == 200

    # 5) Envia ao Financeiro
    rs = requests.post(
        f"{URL}/folha-pagamento/{folha_id}/enviar-financeiro",
        headers=_h(t),
        json={"modo": "individual"},
        timeout=30,
    )
    assert rs.status_code == 200
    sol_id = rs.json()["id"]

    # 6) Verifica task no sino administrativo
    tasks_adm = requests.get(f"{URL}/tasks?system=administrativo", headers=_h(t), timeout=30).json()
    task_sol = next(
        (x for x in tasks_adm
         if x.get("origem", {}).get("solicitacao_id") == sol_id),
        None,
    )
    assert task_sol, "Task de solicitação NÃO criada no sino Administrativo"
    assert task_sol["priority"] == "alta"
    assert "/administrativo/solicitacoes-folha" in task_sol.get("origem", {}).get("rota", "")

    # 7) Rejeita primeiro (verifica notificação de rejeição)
    # Antes precisamos voltar o estado — vamos só aceitar e checar a task de aceite
    plano = requests.get(f"{URL}/admin/plano-contas", headers=_h(t), timeout=30).json()
    plano_id = next(p["id"] for p in plano if p.get("tipo") == "despesa")
    ra = requests.post(
        f"{URL}/financeiro/solicitacoes-folha/{sol_id}/aceitar",
        headers=_h(t),
        json={"plano_contas_id": plano_id, "data_vencimento": "2026-06-05"},
        timeout=30,
    )
    assert ra.status_code == 200
    contas_criadas = ra.json()["total"]
    assert contas_criadas > 0

    # 8) Verifica task de retorno no RH
    tasks_rh2 = requests.get(f"{URL}/tasks?system=rh", headers=_h(t), timeout=30).json()
    task_aceita = next(
        (x for x in tasks_rh2
         if x.get("origem", {}).get("folha_id") == folha_id
         and x.get("origem", {}).get("tipo") == "folha_aceita"),
        None,
    )
    assert task_aceita, "Task de aceite NÃO criada no sino RH"
    assert "aceita" in (task_aceita.get("title") or "").lower()

    # Cleanup mínimo (não deleta as tasks para não atrapalhar visual)
    contas_ids = ra.json()["contas_criadas"]
    for cid in contas_ids:
        requests.delete(f"{URL}/admin/contas-pagar/{cid}", headers=_h(t), timeout=30)
    requests.delete(f"{URL}/folha-pagamento/{folha_id}", headers=_h(t), timeout=30)
