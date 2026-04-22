"""
Emissão de Notas Fiscais (NF-e / NFS-e) — endpoints extraídos de server.py
na Sessão 32 de refatoração (Fase 1 Parte 2). Inclui emissão, consulta de
tabelas (CFOPs, códigos de serviço LC 116/2003), download XML/PDF e exclusão
de rascunhos.
"""
from __future__ import annotations

import base64
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict

from utils.audit import create_audit_log
from utils.auth import get_current_user
from utils.database import db

logger = logging.getLogger(__name__)
emissao_router = APIRouter(tags=["Emissão NF-e/NFS-e"])


# ============================================================================
# MODELS — Emissão NF-e
# ============================================================================

class NFeItemEmissao(BaseModel):
    produto_id: Optional[str] = None
    codigo: str
    descricao: str
    ncm: str = "00000000"
    cfop: str = "5102"
    unidade: str = "UN"
    quantidade: float
    valor_unitario: float
    valor_total: float
    origem: str = "0"
    cst_icms: str = "00"
    aliquota_icms: float = 0
    valor_icms: float = 0
    cst_pis: str = "01"
    aliquota_pis: float = 0
    valor_pis: float = 0
    cst_cofins: str = "01"
    aliquota_cofins: float = 0
    valor_cofins: float = 0
    cst_ipi: str = "50"
    aliquota_ipi: float = 0
    valor_ipi: float = 0


class NFeEmissaoCreate(BaseModel):
    certificado_id: str
    dest_cpf_cnpj: str
    dest_razao_social: str
    dest_ie: Optional[str] = None
    dest_email: Optional[str] = None
    dest_telefone: Optional[str] = None
    dest_cep: str
    dest_logradouro: str
    dest_numero: str
    dest_complemento: Optional[str] = None
    dest_bairro: str
    dest_cidade: str
    dest_uf: str
    dest_codigo_municipio: Optional[str] = None
    natureza_operacao: str = "Venda de Mercadoria"
    tipo_operacao: str = "1"
    finalidade: str = "1"
    consumidor_final: str = "1"
    presenca_comprador: str = "1"
    forma_pagamento: str = "01"
    valor_pagamento: Optional[float] = None
    modalidade_frete: str = "9"
    transportador_cnpj: Optional[str] = None
    transportador_razao: Optional[str] = None
    itens: List[NFeItemEmissao]
    valor_produtos: float
    valor_frete: float = 0
    valor_seguro: float = 0
    valor_desconto: float = 0
    valor_outros: float = 0
    valor_total: float
    info_complementar: Optional[str] = None


# ============================================================================
# MODELS — Emissão NFS-e
# ============================================================================

class NFSeItemEmissao(BaseModel):
    produto_id: Optional[str] = None
    codigo_servico: str
    descricao: str
    quantidade: float = 1
    valor_unitario: float
    valor_total: float
    aliquota_iss: float = 0
    valor_iss: float = 0


class NFSeEmissaoCreate(BaseModel):
    certificado_id: str
    tomador_cpf_cnpj: str
    tomador_razao_social: str
    tomador_ie: Optional[str] = None
    tomador_im: Optional[str] = None
    tomador_email: Optional[str] = None
    tomador_telefone: Optional[str] = None
    tomador_cep: str
    tomador_logradouro: str
    tomador_numero: str
    tomador_complemento: Optional[str] = None
    tomador_bairro: str
    tomador_cidade: str
    tomador_uf: str
    tomador_codigo_municipio: Optional[str] = None
    codigo_cnae: Optional[str] = None
    codigo_tributario_municipio: str
    item_lista_servico: str
    discriminacao: str
    valor_servicos: float
    valor_deducoes: float = 0
    valor_pis: float = 0
    valor_cofins: float = 0
    valor_inss: float = 0
    valor_ir: float = 0
    valor_csll: float = 0
    outras_retencoes: float = 0
    valor_iss: float = 0
    aliquota_iss: float = 0
    valor_liquido: float
    iss_retido: bool = False
    info_complementar: Optional[str] = None
    itens: List[NFSeItemEmissao] = []


# ============================================================================
# TABELAS DE REFERÊNCIA
# ============================================================================

CFOPS_SAIDA = [
    {"codigo": "5101", "descricao": "Venda de produção do estabelecimento"},
    {"codigo": "5102", "descricao": "Venda de mercadoria adquirida ou recebida de terceiros"},
    {"codigo": "5103", "descricao": "Venda de produção, efetuada fora do estabelecimento"},
    {"codigo": "5104", "descricao": "Venda de mercadoria adquirida, efetuada fora do estabelecimento"},
    {"codigo": "5405", "descricao": "Venda de mercadoria adquirida, sujeita ao regime ST"},
    {"codigo": "5933", "descricao": "Prestação de serviço tributado pelo ISSQN"},
    {"codigo": "6101", "descricao": "Venda de produção - Interestadual"},
    {"codigo": "6102", "descricao": "Venda de mercadoria adquirida - Interestadual"},
]

CODIGOS_SERVICO_LC116 = [
    {"codigo": "01.01", "descricao": "Análise e desenvolvimento de sistemas"},
    {"codigo": "01.02", "descricao": "Programação"},
    {"codigo": "01.03", "descricao": "Processamento de dados e congêneres"},
    {"codigo": "01.04", "descricao": "Elaboração de programas de computadores"},
    {"codigo": "07.02", "descricao": "Execução por administração, empreitada ou subempreitada de obras de construção civil"},
    {"codigo": "07.04", "descricao": "Demolição"},
    {"codigo": "07.05", "descricao": "Reparação, conservação e reforma de edifícios"},
    {"codigo": "07.10", "descricao": "Limpeza, manutenção e conservação de vias e logradouros públicos"},
    {"codigo": "07.11", "descricao": "Decoração e jardinagem, inclusive corte e poda de árvores"},
    {"codigo": "07.12", "descricao": "Controle e tratamento de efluentes"},
    {"codigo": "07.16", "descricao": "Florestamento, reflorestamento, semeadura e conservação"},
    {"codigo": "07.19", "descricao": "Acompanhamento e fiscalização de obras de engenharia"},
    {"codigo": "14.01", "descricao": "Lubrificação, limpeza, lustração, revisão, carga e recarga"},
    {"codigo": "14.03", "descricao": "Recondicionamento de motores"},
    {"codigo": "14.06", "descricao": "Instalação e montagem de aparelhos, máquinas e equipamentos"},
    {"codigo": "17.01", "descricao": "Assessoria ou consultoria de qualquer natureza"},
    {"codigo": "17.02", "descricao": "Análise, exame, pesquisa, coleta, compilação de dados"},
    {"codigo": "17.05", "descricao": "Fornecimento de mão-de-obra"},
    {"codigo": "25.01", "descricao": "Funerais, inclusive fornecimento de caixão, urna ou esquife"},
]


@emissao_router.get("/nfe/cfops")
async def list_cfops(current_user: dict = Depends(get_current_user)):
    return CFOPS_SAIDA


@emissao_router.get("/nfse/codigos-servico")
async def list_codigos_servico(current_user: dict = Depends(get_current_user)):
    return CODIGOS_SERVICO_LC116


# ============================================================================
# LISTAGEM DE NOTAS EMITIDAS
# ============================================================================

@emissao_router.get("/nfe/emitidas")
async def list_nfes_emitidas(
    certificado_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    filtro: dict = {"tipo": "nfe"}
    if certificado_id:
        filtro["certificado_id"] = certificado_id
    if status:
        filtro["status"] = status
    return await db.notas_emitidas.find(filtro, {"_id": 0}).sort("created_at", -1).to_list(500)


@emissao_router.get("/nfse/emitidas")
async def list_nfses_emitidas(
    certificado_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    filtro: dict = {"tipo": "nfse"}
    if certificado_id:
        filtro["certificado_id"] = certificado_id
    if status:
        filtro["status"] = status
    return await db.notas_emitidas.find(filtro, {"_id": 0}).sort("created_at", -1).to_list(500)


@emissao_router.get("/notas-emitidas")
async def list_notas_emitidas(
    tipo: Optional[str] = None,
    certificado_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    filtro: dict = {}
    if tipo:
        filtro["tipo"] = tipo
    if certificado_id:
        filtro["certificado_id"] = certificado_id
    if status:
        filtro["status"] = status
    return await db.notas_emitidas.find(filtro, {"_id": 0}).sort("created_at", -1).to_list(500)


@emissao_router.get("/notas-emitidas/{nota_id}")
async def get_nota_emitida(nota_id: str, current_user: dict = Depends(get_current_user)):
    nota = await db.notas_emitidas.find_one({"id": nota_id}, {"_id": 0})
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada")
    return nota


# ============================================================================
# EMISSÃO NF-e
# ============================================================================

@emissao_router.post("/nfe/emitir")
async def emitir_nfe(data: NFeEmissaoCreate, current_user: dict = Depends(get_current_user)):
    """Emite uma NF-e. Atualmente salva como rascunho (emissão real requer PyNFe configurado)."""
    certificado = await db.nfe_certificados.find_one({"id": data.certificado_id})
    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")
    if not certificado.get("ativo"):
        raise HTTPException(status_code=400, detail="Certificado inativo")

    ultimo = await db.notas_emitidas.find_one(
        {"tipo": "nfe", "certificado_id": data.certificado_id},
        sort=[("numero", -1)],
    )
    numero = int(ultimo["numero"]) + 1 if ultimo else 1
    serie = "1"

    chave_acesso = None
    protocolo = None
    status_nota = "rascunho"
    mensagem = "Nota salva como rascunho"
    xml_base64 = None

    try:
        from pynfe.processamento.comunicacao import ComunicacaoSefaz
        import tempfile
        import os as _os

        cert_data = base64.b64decode(certificado["certificado_base64"])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pfx") as cert_file:
            cert_file.write(cert_data)
            cert_path = cert_file.name

        homologacao = certificado.get("ambiente", "producao") == "homologacao"
        try:
            con = ComunicacaoSefaz(
                uf=certificado.get("uf", "SP"),
                certificado=cert_path,
                certificado_senha=certificado["senha_certificado"],
                homologacao=homologacao,
            )
            status_servico = con.status_servico("nfe")
            if status_servico and hasattr(status_servico, "text"):
                logger.info(f"Status SEFAZ: {status_servico.text[:200]}")
        except Exception as status_err:
            logger.warning(f"Erro ao verificar status SEFAZ: {status_err}")

        mensagem = "Nota salva como rascunho. Emissão SEFAZ requer configuração adicional."
        try:
            _os.unlink(cert_path)
        except Exception:
            pass

    except ImportError:
        logger.warning("PyNFe não disponível para emissão")
        mensagem = "Nota salva como rascunho. Biblioteca PyNFe não disponível."
    except Exception as e:
        logger.error(f"Erro na emissão: {e}")
        mensagem = f"Nota salva como rascunho. Erro: {str(e)}"

    nota_doc = {
        "id": str(uuid.uuid4()),
        "tipo": "nfe",
        "certificado_id": data.certificado_id,
        "cnpj_emitente": certificado["cnpj"],
        "razao_social_emitente": certificado["razao_social"],
        "uf_emitente": certificado.get("uf", "SP"),
        "ambiente": certificado.get("ambiente", "producao"),
        "numero": str(numero),
        "serie": serie,
        "chave_acesso": chave_acesso,
        "protocolo": protocolo,
        "status": status_nota,
        "mensagem": mensagem,
        "dest_cpf_cnpj": data.dest_cpf_cnpj,
        "dest_razao_social": data.dest_razao_social,
        "dest_ie": data.dest_ie,
        "dest_email": data.dest_email,
        "dest_telefone": data.dest_telefone,
        "dest_endereco": {
            "cep": data.dest_cep,
            "logradouro": data.dest_logradouro,
            "numero": data.dest_numero,
            "complemento": data.dest_complemento,
            "bairro": data.dest_bairro,
            "cidade": data.dest_cidade,
            "uf": data.dest_uf,
            "codigo_municipio": data.dest_codigo_municipio,
        },
        "natureza_operacao": data.natureza_operacao,
        "tipo_operacao": data.tipo_operacao,
        "finalidade": data.finalidade,
        "consumidor_final": data.consumidor_final,
        "presenca_comprador": data.presenca_comprador,
        "forma_pagamento": data.forma_pagamento,
        "valor_pagamento": data.valor_pagamento or data.valor_total,
        "modalidade_frete": data.modalidade_frete,
        "transportador_cnpj": data.transportador_cnpj,
        "transportador_razao": data.transportador_razao,
        "itens": [item.model_dump() for item in data.itens],
        "valor_produtos": data.valor_produtos,
        "valor_frete": data.valor_frete,
        "valor_seguro": data.valor_seguro,
        "valor_desconto": data.valor_desconto,
        "valor_outros": data.valor_outros,
        "valor_total": data.valor_total,
        "info_complementar": data.info_complementar,
        "xml_base64": xml_base64,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
    }
    await db.notas_emitidas.insert_one(nota_doc)

    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="nfe_emitida",
        entity_id=nota_doc["id"],
        entity_name=f"NF-e {numero}",
        details=f"NF-e para {data.dest_razao_social} - R$ {data.valor_total:,.2f}",
        module="Financeiro",
    )

    return {
        "id": nota_doc["id"],
        "tipo": "nfe",
        "numero": str(numero),
        "serie": serie,
        "chave_acesso": chave_acesso,
        "protocolo": protocolo,
        "status": status_nota,
        "mensagem": mensagem,
        "created_at": nota_doc["created_at"],
    }


# ============================================================================
# EMISSÃO NFS-e
# ============================================================================

@emissao_router.post("/nfse/emitir")
async def emitir_nfse(data: NFSeEmissaoCreate, current_user: dict = Depends(get_current_user)):
    """Emite uma NFS-e via Webiss Palmas/TO (atualmente como rascunho)."""
    certificado = await db.nfe_certificados.find_one({"id": data.certificado_id})
    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")
    if not certificado.get("ativo"):
        raise HTTPException(status_code=400, detail="Certificado inativo")

    ultimo = await db.notas_emitidas.find_one(
        {"tipo": "nfse", "certificado_id": data.certificado_id},
        sort=[("numero", -1)],
    )
    numero_rps = int(ultimo["numero"]) + 1 if ultimo else 1
    serie_rps = "RPS"

    numero_nfse = None
    codigo_verificacao = None
    protocolo = None
    status_nota = "rascunho"
    mensagem = "Nota salva como rascunho"
    xml_base64 = None

    try:
        cnpj_limpo = certificado["cnpj"].replace(".", "").replace("/", "").replace("-", "")
        tomador_doc_limpo = data.tomador_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")
        doc_tag = (
            f"<Cnpj>{tomador_doc_limpo}</Cnpj>"
            if len(tomador_doc_limpo) == 14
            else f"<Cpf>{tomador_doc_limpo}</Cpf>"
        )
        tel = (data.tomador_telefone or "").replace("(", "").replace(")", "").replace("-", "").replace(" ", "")[:11]

        xml_rps = f"""<?xml version="1.0" encoding="UTF-8"?>
<EnviarLoteRpsEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">
    <LoteRps Id="lote{numero_rps}" versao="2.01">
        <NumeroLote>{numero_rps}</NumeroLote>
        <CpfCnpj><Cnpj>{cnpj_limpo}</Cnpj></CpfCnpj>
        <InscricaoMunicipal>{certificado.get('inscricao_municipal', '')}</InscricaoMunicipal>
        <QuantidadeRps>1</QuantidadeRps>
        <ListaRps>
            <Rps>
                <InfDeclaracaoPrestacaoServico Id="rps{numero_rps}">
                    <Rps>
                        <IdentificacaoRps>
                            <Numero>{numero_rps}</Numero>
                            <Serie>{serie_rps}</Serie>
                            <Tipo>1</Tipo>
                        </IdentificacaoRps>
                        <DataEmissao>{datetime.now().strftime('%Y-%m-%d')}</DataEmissao>
                        <Status>1</Status>
                    </Rps>
                    <Competencia>{datetime.now().strftime('%Y-%m-%d')}</Competencia>
                    <Servico>
                        <Valores>
                            <ValorServicos>{data.valor_servicos:.2f}</ValorServicos>
                            <ValorDeducoes>{data.valor_deducoes:.2f}</ValorDeducoes>
                            <ValorPis>{data.valor_pis:.2f}</ValorPis>
                            <ValorCofins>{data.valor_cofins:.2f}</ValorCofins>
                            <ValorInss>{data.valor_inss:.2f}</ValorInss>
                            <ValorIr>{data.valor_ir:.2f}</ValorIr>
                            <ValorCsll>{data.valor_csll:.2f}</ValorCsll>
                            <OutrasRetencoes>{data.outras_retencoes:.2f}</OutrasRetencoes>
                            <ValorIss>{data.valor_iss:.2f}</ValorIss>
                            <Aliquota>{data.aliquota_iss:.4f}</Aliquota>
                            <ValorLiquidoNfse>{data.valor_liquido:.2f}</ValorLiquidoNfse>
                        </Valores>
                        <IssRetido>{2 if data.iss_retido else 1}</IssRetido>
                        <ItemListaServico>{data.item_lista_servico.replace('.', '')}</ItemListaServico>
                        <CodigoCnae>{data.codigo_cnae or ''}</CodigoCnae>
                        <CodigoTributacaoMunicipio>{data.codigo_tributario_municipio}</CodigoTributacaoMunicipio>
                        <Discriminacao>{data.discriminacao[:2000]}</Discriminacao>
                        <CodigoMunicipio>1721000</CodigoMunicipio>
                    </Servico>
                    <Prestador>
                        <CpfCnpj><Cnpj>{cnpj_limpo}</Cnpj></CpfCnpj>
                        <InscricaoMunicipal>{certificado.get('inscricao_municipal', '')}</InscricaoMunicipal>
                    </Prestador>
                    <Tomador>
                        <IdentificacaoTomador>
                            <CpfCnpj>{doc_tag}</CpfCnpj>
                        </IdentificacaoTomador>
                        <RazaoSocial>{data.tomador_razao_social[:150]}</RazaoSocial>
                        <Endereco>
                            <Endereco>{data.tomador_logradouro[:125]}</Endereco>
                            <Numero>{data.tomador_numero[:10]}</Numero>
                            <Complemento>{(data.tomador_complemento or '')[:60]}</Complemento>
                            <Bairro>{data.tomador_bairro[:60]}</Bairro>
                            <CodigoMunicipio>{data.tomador_codigo_municipio or '1721000'}</CodigoMunicipio>
                            <Uf>{data.tomador_uf}</Uf>
                            <Cep>{data.tomador_cep.replace('-', '')}</Cep>
                        </Endereco>
                        <Contato>
                            <Telefone>{tel}</Telefone>
                            <Email>{data.tomador_email or ''}</Email>
                        </Contato>
                    </Tomador>
                </InfDeclaracaoPrestacaoServico>
            </Rps>
        </ListaRps>
    </LoteRps>
</EnviarLoteRpsEnvio>"""

        mensagem = "NFS-e salva como rascunho. A emissão via Webiss Palmas/TO requer configuração adicional de assinatura digital."
        xml_base64 = base64.b64encode(xml_rps.encode()).decode()

    except Exception as e:
        logger.error(f"Erro na emissão NFS-e: {e}")
        mensagem = f"Nota salva como rascunho. Erro: {str(e)}"

    nota_doc = {
        "id": str(uuid.uuid4()),
        "tipo": "nfse",
        "certificado_id": data.certificado_id,
        "cnpj_emitente": certificado["cnpj"],
        "razao_social_emitente": certificado["razao_social"],
        "uf_emitente": certificado.get("uf", "TO"),
        "ambiente": certificado.get("ambiente", "producao"),
        "numero": str(numero_rps),
        "numero_nfse": numero_nfse,
        "serie": serie_rps,
        "codigo_verificacao": codigo_verificacao,
        "protocolo": protocolo,
        "status": status_nota,
        "mensagem": mensagem,
        "tomador_cpf_cnpj": data.tomador_cpf_cnpj,
        "tomador_razao_social": data.tomador_razao_social,
        "tomador_ie": data.tomador_ie,
        "tomador_im": data.tomador_im,
        "tomador_email": data.tomador_email,
        "tomador_telefone": data.tomador_telefone,
        "tomador_endereco": {
            "cep": data.tomador_cep,
            "logradouro": data.tomador_logradouro,
            "numero": data.tomador_numero,
            "complemento": data.tomador_complemento,
            "bairro": data.tomador_bairro,
            "cidade": data.tomador_cidade,
            "uf": data.tomador_uf,
            "codigo_municipio": data.tomador_codigo_municipio,
        },
        "codigo_cnae": data.codigo_cnae,
        "codigo_tributario_municipio": data.codigo_tributario_municipio,
        "item_lista_servico": data.item_lista_servico,
        "discriminacao": data.discriminacao,
        "valor_servicos": data.valor_servicos,
        "valor_deducoes": data.valor_deducoes,
        "valor_pis": data.valor_pis,
        "valor_cofins": data.valor_cofins,
        "valor_inss": data.valor_inss,
        "valor_ir": data.valor_ir,
        "valor_csll": data.valor_csll,
        "outras_retencoes": data.outras_retencoes,
        "valor_iss": data.valor_iss,
        "aliquota_iss": data.aliquota_iss,
        "valor_liquido": data.valor_liquido,
        "valor_total": data.valor_servicos,
        "iss_retido": data.iss_retido,
        "itens": [item.model_dump() for item in data.itens] if data.itens else [],
        "info_complementar": data.info_complementar,
        "xml_base64": xml_base64,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
    }
    await db.notas_emitidas.insert_one(nota_doc)

    await create_audit_log(
        user=current_user,
        action="criar",
        entity_type="nfse_emitida",
        entity_id=nota_doc["id"],
        entity_name=f"NFS-e RPS {numero_rps}",
        details=f"NFS-e para {data.tomador_razao_social} - R$ {data.valor_servicos:,.2f}",
        module="Financeiro",
    )

    return {
        "id": nota_doc["id"],
        "tipo": "nfse",
        "numero": str(numero_rps),
        "numero_nfse": numero_nfse,
        "serie": serie_rps,
        "codigo_verificacao": codigo_verificacao,
        "protocolo": protocolo,
        "status": status_nota,
        "mensagem": mensagem,
        "created_at": nota_doc["created_at"],
    }


# ============================================================================
# EXCLUSÃO DE RASCUNHO
# ============================================================================

@emissao_router.delete("/notas-emitidas/{nota_id}")
async def delete_nota_emitida(nota_id: str, current_user: dict = Depends(get_current_user)):
    """Exclui uma nota fiscal emitida (apenas rascunhos ou rejeitadas)."""
    nota = await db.notas_emitidas.find_one({"id": nota_id})
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada")

    if nota.get("status") not in ["rascunho", "rejeitada"]:
        raise HTTPException(
            status_code=400,
            detail="Apenas notas com status 'rascunho' ou 'rejeitada' podem ser excluídas",
        )

    await db.notas_emitidas.delete_one({"id": nota_id})

    await create_audit_log(
        user=current_user,
        action="excluir",
        entity_type=f"{nota['tipo']}_emitida",
        entity_id=nota_id,
        entity_name=f"{nota['tipo'].upper()} {nota['numero']}",
        details="Nota fiscal excluída",
        module="Financeiro",
    )
    return {"message": "Nota fiscal excluída com sucesso"}


# ============================================================================
# DOWNLOAD XML / PDF
# ============================================================================

@emissao_router.get("/notas-emitidas/{nota_id}/download-xml")
async def download_nota_xml(nota_id: str, current_user: dict = Depends(get_current_user)):
    """Download do XML da nota fiscal emitida."""
    nota = await db.notas_emitidas.find_one({"id": nota_id})
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada")

    xml_base64 = nota.get("xml_base64")
    if not xml_base64:
        raise HTTPException(status_code=404, detail="XML não disponível para esta nota")

    try:
        xml_content = base64.b64decode(xml_base64)
        tipo = nota.get("tipo", "nf").upper()
        numero = nota.get("numero", "sem_numero")
        filename = f"{tipo}_{numero}.xml"
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar XML: {str(e)}")


def _fmt_brl(value):
    try:
        return f"R$ {float(value or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


@emissao_router.get("/notas-emitidas/{nota_id}/download-pdf")
async def download_nota_pdf(nota_id: str, current_user: dict = Depends(get_current_user)):
    """Download do PDF (DANFE simplificado/NFS-e) da nota fiscal emitida."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    nota = await db.notas_emitidas.find_one({"id": nota_id})
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada")

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=1 * cm, rightMargin=1 * cm,
            topMargin=1 * cm, bottomMargin=1 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=14, spaceAfter=6, alignment=1)
        subtitle_style = ParagraphStyle("Subtitle", parent=styles["Heading2"], fontSize=10, spaceAfter=4)
        normal_style = ParagraphStyle("Normal", parent=styles["Normal"], fontSize=8)

        elements = []
        tipo = nota.get("tipo", "nfe")

        if tipo == "nfe":
            elements.append(Paragraph("DOCUMENTO AUXILIAR DA NOTA FISCAL ELETRÔNICA", title_style))
            elements.append(Paragraph("DANFE", title_style))
            elements.append(Spacer(1, 10))

            chave_display = (nota.get("chave_acesso", "") or "Pendente")
            chave_display = chave_display[:22] + "..." if chave_display and chave_display != "Pendente" else "Pendente"

            nfe_info = [
                ["NF-e Nº:", nota.get("numero", "-"), "Série:", nota.get("serie", "-")],
                ["Data Emissão:", (nota.get("created_at") or "-")[:10], "Valor Total:", _fmt_brl(nota.get("valor_total", 0))],
                ["Status:", (nota.get("status") or "-").upper(), "Chave de Acesso:", chave_display],
            ]
            table = Table(nfe_info, colWidths=[3 * cm, 5 * cm, 3 * cm, 5 * cm])
            table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 10))

            elements.append(Paragraph("<b>EMITENTE</b>", subtitle_style))
            emit_info = [
                ["Razão Social:", nota.get("razao_social_emitente", "-")],
                ["CNPJ:", nota.get("cnpj_emitente", "-")],
            ]
            table = Table(emit_info, colWidths=[3 * cm, 13 * cm])
            table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 10))

            elements.append(Paragraph("<b>DESTINATÁRIO</b>", subtitle_style))
            dest_info = [
                ["Razão Social:", nota.get("dest_razao_social", "-")],
                ["CPF/CNPJ:", nota.get("dest_cpf_cnpj", "-")],
            ]
            table = Table(dest_info, colWidths=[3 * cm, 13 * cm])
            table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 10))

            elements.append(Paragraph("<b>ITENS</b>", subtitle_style))
            itens = nota.get("itens", [])
            if itens:
                itens_data = [["Cód.", "Descrição", "Qtd", "V.Unit", "V.Total"]]
                for item in itens:
                    itens_data.append([
                        (item.get("codigo", "-") or "")[:10],
                        Paragraph((item.get("descricao", "-") or "")[:50], normal_style),
                        str(item.get("quantidade", 0)),
                        _fmt_brl(item.get("valor_unitario", 0)),
                        _fmt_brl(item.get("valor_total", 0)),
                    ])
                table = Table(itens_data, colWidths=[2 * cm, 7 * cm, 1.5 * cm, 3 * cm, 3 * cm])
                table.setStyle(TableStyle([
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ]))
                elements.append(table)

            filename = f"DANFE_NFe_{nota.get('numero', 'sem_numero')}.pdf"
        else:
            elements.append(Paragraph("NOTA FISCAL DE SERVIÇOS ELETRÔNICA", title_style))
            elements.append(Paragraph("NFS-e", title_style))
            elements.append(Spacer(1, 10))

            nfse_info = [
                ["RPS Nº:", nota.get("numero", "-"), "NFS-e Nº:", nota.get("numero_nfse") or "Pendente"],
                ["Data Emissão:", (nota.get("created_at") or "-")[:10], "Valor Total:", _fmt_brl(nota.get("valor_servicos", 0))],
                ["Status:", (nota.get("status") or "-").upper(), "Cód. Verificação:", nota.get("codigo_verificacao") or "Pendente"],
            ]
            table = Table(nfse_info, colWidths=[3 * cm, 5 * cm, 3 * cm, 5 * cm])
            table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 10))

            elements.append(Paragraph("<b>PRESTADOR DO SERVIÇO</b>", subtitle_style))
            prest_info = [
                ["Razão Social:", nota.get("razao_social_emitente", "-")],
                ["CNPJ:", nota.get("cnpj_emitente", "-")],
            ]
            table = Table(prest_info, colWidths=[3 * cm, 13 * cm])
            table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 10))

            elements.append(Paragraph("<b>TOMADOR DO SERVIÇO</b>", subtitle_style))
            tomador_info = [
                ["Razão Social:", nota.get("tomador_razao_social", "-")],
                ["CPF/CNPJ:", nota.get("tomador_cpf_cnpj", "-")],
            ]
            table = Table(tomador_info, colWidths=[3 * cm, 13 * cm])
            table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 10))

            elements.append(Paragraph("<b>DISCRIMINAÇÃO DO SERVIÇO</b>", subtitle_style))
            elements.append(Paragraph(nota.get("discriminacao", "Não informado"), normal_style))
            elements.append(Spacer(1, 10))

            elements.append(Paragraph("<b>VALORES</b>", subtitle_style))
            valores_info = [
                ["Valor dos Serviços:", _fmt_brl(nota.get("valor_servicos", 0))],
                ["Deduções:", _fmt_brl(nota.get("valor_deducoes", 0))],
                ["ISS:", _fmt_brl(nota.get("valor_iss", 0))],
                ["Valor Líquido:", _fmt_brl(nota.get("valor_liquido", 0))],
            ]
            table = Table(valores_info, colWidths=[4 * cm, 5 * cm])
            table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ]))
            elements.append(table)

            filename = f"NFSe_RPS_{nota.get('numero', 'sem_numero')}.pdf"

        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            f"<i>Documento gerado pelo Sistema CRA em {datetime.now().strftime('%d/%m/%Y %H:%M')}</i>",
            normal_style,
        ))
        doc.build(elements)
        buffer.seek(0)

        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")
