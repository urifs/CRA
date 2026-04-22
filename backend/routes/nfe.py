"""
NF-e (Notas Fiscais Eletrônicas) — endpoints extraídos de server.py
na Sessão 32 de refatoração. Gerencia certificados, NF-es importadas,
downloads (XML + DANFE) e criação de contas a pagar.

NOTA: Os endpoints de IMPORTAÇÃO (POST /nfe/importar/{cert_id} e
POST /nfse/importar/{cert_id}) permanecem em server.py por enquanto pois
dependem do scheduler de importação automática. Serão extraídos em fase futura.
"""
from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict

from utils.audit import create_audit_log
from utils.auth import get_current_user
from utils.database import db

logger = logging.getLogger(__name__)
nfe_router = APIRouter(prefix="/nfe", tags=["NF-e"])


# ============================================================================
# MODELS
# ============================================================================

class NFeCertificadoCreate(BaseModel):
    cnpj: str
    razao_social: str
    uf: str = "SP"
    ambiente: str = "producao"
    certificado_base64: str
    senha_certificado: str
    ativo: bool = True
    inscricao_municipal: Optional[str] = None
    url_nfse: Optional[str] = None


class NFeCertificadoUpdate(BaseModel):
    razao_social: Optional[str] = None
    uf: Optional[str] = None
    ambiente: Optional[str] = None
    ativo: Optional[bool] = None
    inscricao_municipal: Optional[str] = None
    url_nfse: Optional[str] = None
    senha_certificado: Optional[str] = None
    certificado_base64: Optional[str] = None


# ============================================================================
# CERTIFICADOS (CRUD)
# ============================================================================

@nfe_router.get("/certificados")
async def list_nfe_certificados(current_user: dict = Depends(get_current_user)):
    """Lista todos os certificados/CNPJs cadastrados"""
    certificados = await db.nfe_certificados.find(
        {},
        {"_id": 0, "certificado_base64": 0, "senha_certificado": 0},
    ).to_list(100)

    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for cert in certificados:
        if cert.get("data_consultas") != hoje:
            await db.nfe_certificados.update_one(
                {"id": cert["id"]},
                {"$set": {"consultas_hoje": 0, "data_consultas": hoje}},
            )
            cert["consultas_hoje"] = 0
            cert["data_consultas"] = hoje

        cert.setdefault("consultas_hoje", 0)
        cert.setdefault("bloqueado_ate", None)
        cert.setdefault("inscricao_municipal", "")
        cert.setdefault("url_nfse", "")

    return certificados


@nfe_router.post("/certificados")
async def create_nfe_certificado(
    certificado: NFeCertificadoCreate,
    current_user: dict = Depends(get_current_user),
):
    """Cadastra um novo CNPJ com certificado para importação de NF-e"""
    existing = await db.nfe_certificados.find_one({"cnpj": certificado.cnpj})
    if existing:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado")

    try:
        from cryptography import x509
        from cryptography.hazmat.primitives.serialization import pkcs12

        cert_data = base64.b64decode(certificado.certificado_base64)
        _, cert_obj, _ = pkcs12.load_key_and_certificates(
            cert_data, certificado.senha_certificado.encode()
        )

        if cert_obj is None:
            raise ValueError("Certificado não encontrado no arquivo")

        subject = cert_obj.subject
        cn = subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
        logger.info(f"Certificado válido para: {cn[0].value if cn else 'N/A'}")

    except Exception as e:
        logger.error(f"Erro ao validar certificado: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Certificado inválido ou senha incorreta: {str(e)}",
        )

    doc = {
        "id": str(uuid.uuid4()),
        "cnpj": certificado.cnpj,
        "razao_social": certificado.razao_social,
        "uf": certificado.uf,
        "ambiente": certificado.ambiente,
        "certificado_base64": certificado.certificado_base64,
        "senha_certificado": certificado.senha_certificado,
        "ativo": certificado.ativo,
        "inscricao_municipal": certificado.inscricao_municipal or "",
        "url_nfse": certificado.url_nfse or "",
        "ultimo_nsu": "000000000000000",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
        "consultas_hoje": 0,
        "data_consultas": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "bloqueado_ate": None,
    }
    await db.nfe_certificados.insert_one(doc)

    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="nfe_certificado",
        entity_id=doc["id"],
        entity_name=f"{certificado.razao_social} ({certificado.cnpj})",
        details="Certificado cadastrado para importação de NF-e",
        module="Financeiro",
    )
    return {"id": doc["id"], "cnpj": doc["cnpj"], "razao_social": doc["razao_social"]}


@nfe_router.patch("/certificados/{certificado_id}")
async def update_nfe_certificado(
    certificado_id: str,
    data: NFeCertificadoUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Atualiza campos do certificado (Inscrição Municipal, URL NFS-e, etc.)."""
    certificado = await db.nfe_certificados.find_one({"id": certificado_id})
    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")

    update_fields = {}
    for key in ("razao_social", "uf", "ambiente", "ativo", "inscricao_municipal", "url_nfse"):
        value = getattr(data, key)
        if value is not None:
            update_fields[key] = value

    if data.certificado_base64 and data.senha_certificado:
        try:
            from cryptography.hazmat.primitives.serialization import pkcs12
            cert_data = base64.b64decode(data.certificado_base64)
            pkcs12.load_key_and_certificates(cert_data, data.senha_certificado.encode())
            update_fields["certificado_base64"] = data.certificado_base64
            update_fields["senha_certificado"] = data.senha_certificado
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Certificado inválido ou senha incorreta: {str(e)}",
            )
    elif data.senha_certificado and not data.certificado_base64:
        try:
            from cryptography.hazmat.primitives.serialization import pkcs12
            cert_data = base64.b64decode(certificado.get("certificado_base64", ""))
            pkcs12.load_key_and_certificates(cert_data, data.senha_certificado.encode())
            update_fields["senha_certificado"] = data.senha_certificado
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Senha incorreta para o certificado atual: {str(e)}",
            )

    if not update_fields:
        return {"message": "Nada para atualizar"}

    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.nfe_certificados.update_one(
        {"id": certificado_id},
        {"$set": update_fields},
    )

    await create_audit_log(
        user=current_user,
        action="editar",
        entity_type="nfe_certificado",
        entity_id=certificado_id,
        entity_name=f"{certificado.get('razao_social')} ({certificado.get('cnpj')})",
        details=f"Campos atualizados: {', '.join(k for k in update_fields if k not in ('senha_certificado', 'certificado_base64', 'updated_at'))}",
        module="Financeiro",
    )

    atualizado = await db.nfe_certificados.find_one(
        {"id": certificado_id},
        {"_id": 0, "certificado_base64": 0, "senha_certificado": 0},
    )
    return atualizado


@nfe_router.delete("/certificados/{certificado_id}")
async def delete_nfe_certificado(
    certificado_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove um certificado cadastrado"""
    certificado = await db.nfe_certificados.find_one({"id": certificado_id})
    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")

    await db.nfe_certificados.delete_one({"id": certificado_id})

    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type="nfe_certificado",
        entity_id=certificado_id,
        entity_name=f"{certificado['razao_social']} ({certificado['cnpj']})",
        details="Certificado removido",
        module="Financeiro",
    )
    return {"message": "Certificado removido com sucesso"}


# ============================================================================
# NF-e IMPORTADAS (listagem / consulta / mutações)
# ============================================================================

@nfe_router.get("/importadas")
async def list_nfe_importadas(
    certificado_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Lista todas as NF-e importadas"""
    filtro: dict = {}
    if certificado_id:
        filtro["certificado_id"] = certificado_id
    if status:
        filtro["status"] = status
    return await db.nfe_importadas.find(filtro, {"_id": 0}).sort("data_emissao", -1).to_list(500)


@nfe_router.get("/importadas/{nfe_id}")
async def get_nfe_importada(nfe_id: str, current_user: dict = Depends(get_current_user)):
    """Retorna detalhes de uma NF-e importada"""
    nfe = await db.nfe_importadas.find_one({"id": nfe_id}, {"_id": 0})
    if not nfe:
        raise HTTPException(status_code=404, detail="NF-e não encontrada")
    return nfe


@nfe_router.post("/importadas/{nfe_id}/criar-conta-pagar")
async def criar_conta_pagar_from_nfe(
    nfe_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cria uma conta a pagar a partir de uma NF-e importada"""
    nfe = await db.nfe_importadas.find_one({"id": nfe_id})
    if not nfe:
        raise HTTPException(status_code=404, detail="NF-e não encontrada")

    if nfe.get("conta_pagar_id"):
        raise HTTPException(status_code=400, detail="Esta NF-e já possui uma conta a pagar vinculada")

    cadastro = await db.cadastros.find_one({"cpf_cnpj": nfe["cnpj_emitente"]})
    if not cadastro:
        cadastro_doc = {
            "id": str(uuid.uuid4()),
            "tipo": "fornecedor",
            "nome_razao": nfe["razao_social_emitente"],
            "cpf_cnpj": nfe["cnpj_emitente"],
            "telefone": "",
            "email": "",
            "endereco": "",
            "cidade": "",
            "estado": "",
            "cep": "",
            "observacoes": "Cadastrado automaticamente via importação de NF-e",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.cadastros.insert_one(cadastro_doc)
        cadastro = cadastro_doc

    conta_pagar_doc = {
        "id": str(uuid.uuid4()),
        "descricao": f"NF-e {nfe['numero_nf']} - {nfe['razao_social_emitente']}",
        "cadastro_id": cadastro["id"],
        "cadastro_nome": cadastro["nome_razao"],
        "valor": nfe["valor_total"],
        "desconto": 0,
        "juros": 0,
        "multa": 0,
        "data_vencimento": nfe["data_emissao"],
        "data_pagamento": None,
        "status": "pendente",
        "categoria": "fornecedores",
        "observacoes": f"Importada automaticamente da NF-e. Chave: {nfe['chave_acesso']}",
        "centro_custo_id": None,
        "plano_conta_id": None,
        "forma_pagamento_id": None,
        "conta_bancaria_id": None,
        "nfe_id": nfe_id,
        "nfe_chave": nfe["chave_acesso"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.contas_pagar.insert_one(conta_pagar_doc)
    await db.nfe_importadas.update_one(
        {"id": nfe_id},
        {"$set": {"conta_pagar_id": conta_pagar_doc["id"], "status": "processada"}},
    )

    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="conta_pagar",
        entity_id=conta_pagar_doc["id"],
        entity_name=conta_pagar_doc["descricao"],
        details=f"Conta a pagar criada a partir da NF-e {nfe['numero_nf']}",
        module="Financeiro",
    )

    return {
        "message": "Conta a pagar criada com sucesso",
        "conta_pagar_id": conta_pagar_doc["id"],
        "nfe_id": nfe_id,
    }


@nfe_router.patch("/importadas/{nfe_id}/status")
async def update_nfe_status(
    nfe_id: str,
    status: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user),
):
    """Atualiza o status de uma NF-e importada"""
    if status not in ["nova", "processada", "ignorada"]:
        raise HTTPException(status_code=400, detail="Status inválido")

    result = await db.nfe_importadas.update_one(
        {"id": nfe_id},
        {"$set": {"status": status}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="NF-e não encontrada")
    return {"message": "Status atualizado"}


@nfe_router.get("/novas-count")
async def count_novas_nfes(current_user: dict = Depends(get_current_user)):
    """Retorna contagem de NF-e novas para notificações"""
    count = await db.nfe_importadas.count_documents({"status": "nova"})
    return {"count": count}


# ============================================================================
# DOWNLOAD
# ============================================================================

@nfe_router.get("/importadas/{nfe_id}/download-xml")
async def download_nfe_xml(nfe_id: str, current_user: dict = Depends(get_current_user)):
    """Download do XML da NF-e"""
    nfe = await db.nfe_importadas.find_one({"id": nfe_id})
    if not nfe:
        raise HTTPException(status_code=404, detail="NF-e não encontrada")

    xml_base64 = nfe.get("xml_base64")
    if not xml_base64:
        raise HTTPException(status_code=404, detail="XML não disponível para esta NF-e")

    try:
        xml_content = base64.b64decode(xml_base64)
        filename = f"NFe_{nfe.get('numero_nf', 'sem_numero')}_{nfe.get('chave_acesso', '')[:20]}.xml"
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar XML: {str(e)}")


@nfe_router.get("/importadas/{nfe_id}/download-pdf")
async def download_nfe_danfe(nfe_id: str, current_user: dict = Depends(get_current_user)):
    """Download do DANFE (PDF) da NF-e — layout oficial padronizado.
    Renderiza o DANFE a partir do XML quando disponível, via Jinja2 + WeasyPrint.
    Se o PDF original estiver armazenado, ele é retornado.
    """
    nfe = await db.nfe_importadas.find_one({"id": nfe_id})
    if not nfe:
        raise HTTPException(status_code=404, detail="NF-e não encontrada")

    pdf_base64 = nfe.get("pdf_base64")
    if pdf_base64:
        try:
            pdf_content = base64.b64decode(pdf_base64)
            filename = f"DANFE_NFe_{nfe.get('numero_nf', 'sem_numero')}.pdf"
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except Exception as e:
            logger.warning(f"Erro ao decodificar PDF armazenado: {e}")

    try:
        from utils.danfe_generator import render_danfe_pdf
        pdf_bytes = render_danfe_pdf(nfe)
        filename = f"DANFE_NFe_{nfe.get('numero_nf', 'sem_numero')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.exception("Erro ao gerar DANFE")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar DANFE: {str(e)}")
