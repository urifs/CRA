"""
Importação de Notas Fiscais (NF-e via SEFAZ / NFS-e via ABRASF webservice).
Extraído de server.py na Sessão 32 de refatoração (Fase 1 Parte 2).

NOTA: As funções importar_nfe e importar_nfse também são chamadas pelo scheduler
de importação automática em server.py (ver importar_nfe_automatico e
importar_nfse_automatico). Elas são importadas de volta por server.py.
"""
from __future__ import annotations

import base64
import gzip
import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from xml.etree import ElementTree as ET

import requests
from fastapi import APIRouter, Depends, HTTPException

from utils.audit import create_audit_log
from utils.auth import get_current_user
from utils.database import db

import logging
logger = logging.getLogger(__name__)

importacao_router = APIRouter(tags=["Importação NF-e/NFS-e"])


def _parse_nfse_soap_error(response_text: str) -> str:
    """Extrai mensagem legível de uma resposta SOAP de erro/falha do webservice NFS-e.
    Lida com SOAP Fault (faultstring/faultcode), ListaMensagemRetorno (ABRASF) e
    HTML/texto puro como fallback.
    Retorna string curta amigável ao usuário, sem XML cru."""
    if not response_text:
        return "Resposta vazia do webservice"

    text = response_text.strip()
    # Tentar parsear como XML
    try:
        # Limpar BOM e caracteres iniciais não-XML
        if text.lstrip().startswith("<"):
            root = ET.fromstring(text)
        else:
            return text[:300]

        partes: list[str] = []

        # 1) SOAP Fault (qualquer namespace)
        for el in root.iter():
            tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
            if tag in ("faultstring", "Reason", "Text"):
                if el.text and el.text.strip():
                    partes.append(el.text.strip())
            elif tag == "faultcode":
                if el.text and el.text.strip():
                    partes.append(f"[{el.text.strip()}]")
            elif tag == "Detail" or tag == "detail":
                # Detail às vezes contém mensagens estruturadas
                inner = "".join(
                    (c.text or "").strip()
                    for c in el.iter()
                    if (c.text or "").strip()
                )
                if inner:
                    partes.append(inner[:200])

        # 2) ListaMensagemRetorno (padrão ABRASF) — códigos de erro de negócio
        codigo = None
        descricao = None
        for el in root.iter():
            tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
            if tag == "Codigo" and el.text:
                codigo = el.text.strip()
            elif tag == "Descricao" and el.text:
                descricao = el.text.strip()
            elif tag == "Correcao" and el.text:
                if descricao:
                    descricao = f"{descricao} — {el.text.strip()}"

        if codigo and descricao:
            partes.append(f"[Cód {codigo}] {descricao}")
        elif descricao:
            partes.append(descricao)

        if partes:
            # Deduplica preservando ordem
            seen = set()
            unique = []
            for p in partes:
                if p not in seen:
                    seen.add(p)
                    unique.append(p)
            return " | ".join(unique)[:400]

    except ET.ParseError:
        pass

    # Fallback: HTML ou texto plano
    plain = re.sub(r"<[^>]+>", " ", text)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:300] if plain else text[:300]


# Lista ordenada de SOAPActions comuns em webservices NFS-e brasileiros.
# Quando o primeiro falha com "Server did not recognize SOAPAction",
# tentamos os seguintes. Cobre WebISS (Palmas, Araguaína...), Ginfes,
# ISSNet, Betha, Governa, ABRASF strict e variações "vazio"/sem namespace.
# O placeholder {OP} é substituído dinamicamente pela operação em uso.
NFSE_SOAPACTIONS_TEMPLATES = [
    "http://nfse.abrasf.org.br/{OP}",                              # ABRASF v2 (WebISS Palmas, maioria dos WebISS)
    "http://www.abrasf.org.br/nfse.xsd/{OP}",                       # ABRASF strict (padrão original)
    "{OP}",                                                         # WebISS e similares (só nome)
    '"{OP}"',                                                       # WebISS com aspas
    "",                                                             # vazio (alguns provedores aceitam)
    '""',                                                           # vazio com aspas
    "http://tempuri.org/{OP}",                                      # .NET default
]

# Lista de operações que o sistema pode usar. Ordenadas por preferência:
# ConsultarNfseServicoTomado é o nome ABRASF v2 para notas recebidas pelo tomador.
# ConsultarNfseRecebidos é um alias legado usado por alguns provedores.
NFSE_OPERACOES_CONSULTA = [
    "ConsultarNfseServicoTomado",   # ABRASF v2 — notas recebidas como TOMADOR
    "ConsultarNfseRecebidos",        # alias antigo
]


def _post_nfse_com_fallback_soapaction(
    url_nfse: str,
    soap_envelope_bytes: bytes,
    cert_tuple: tuple,
    base_headers: dict,
    timeout: int = 30,
    operation: str = "ConsultarNfseServicoTomado",
    preferred_soapaction: str = None,
):
    """Faz POST SOAP tentando múltiplos SOAPActions até o servidor aceitar.
    Se `preferred_soapaction` for fornecido (salvo de uma conexão bem-sucedida
    anterior), ele é testado primeiro, evitando retries.
    Retorna (response, soapaction_que_funcionou, tentativas)."""
    import requests as req_sync
    tentativas = []
    last_response = None

    soapactions = [tmpl.replace("{OP}", operation) for tmpl in NFSE_SOAPACTIONS_TEMPLATES]
    if preferred_soapaction is not None and preferred_soapaction in soapactions:
        soapactions = [preferred_soapaction] + [sa for sa in soapactions if sa != preferred_soapaction]
    elif preferred_soapaction is not None:
        soapactions = [preferred_soapaction] + soapactions

    for sa in soapactions:
        hdrs = dict(base_headers)
        hdrs["SOAPAction"] = sa
        try:
            r = req_sync.post(
                url_nfse,
                data=soap_envelope_bytes,
                headers=hdrs,
                cert=cert_tuple,
                verify=False,
                timeout=timeout,
            )
        except Exception as e:
            tentativas.append({"soapaction": sa, "erro": str(e)[:120]})
            continue

        last_response = r
        body_lower = (r.text or "").lower()
        # Se a resposta contém erro de SOAPAction, tenta o próximo
        if r.status_code == 500 and "soapaction" in body_lower and ("did not recognize" in body_lower or "não reconheceu" in body_lower):
            tentativas.append({"soapaction": sa, "erro": "SOAPAction não reconhecido (HTTP 500)"})
            continue
        # Sucesso aparente (HTTP 200) ou outro tipo de falha — para aqui
        tentativas.append({"soapaction": sa, "status": r.status_code, "ok": r.status_code == 200})
        return r, sa, tentativas

    return last_response, None, tentativas


@importacao_router.post("/nfe/importar/{certificado_id}")
async def importar_nfe(
    certificado_id: str,
    desde_inicio: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Consulta e importa NF-e da SEFAZ para o CNPJ especificado.

    Por padrão importa de forma incremental a partir do último NSU sincronizado.
    Passe `?desde_inicio=true` para forçar uma varredura completa do histórico
    (NSU=0). Duplicatas são detectadas pela chave de acesso.
    """
    certificado = await db.nfe_certificados.find_one({"id": certificado_id})
    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")
    
    if not certificado.get("ativo"):
        raise HTTPException(status_code=400, detail="Certificado inativo")
    
    # Verificar se está bloqueado
    bloqueado_ate = certificado.get("bloqueado_ate")
    if bloqueado_ate:
        bloqueio_dt = datetime.fromisoformat(bloqueado_ate.replace('Z', '+00:00')) if isinstance(bloqueado_ate, str) else bloqueado_ate
        if datetime.now(timezone.utc) < bloqueio_dt:
            tempo_restante = (bloqueio_dt - datetime.now(timezone.utc)).total_seconds()
            minutos = int(tempo_restante // 60)
            raise HTTPException(
                status_code=429, 
                detail=f"Certificado bloqueado. Aguarde {minutos} minutos para tentar novamente."
            )
        else:
            # Desbloquear se o tempo passou
            await db.nfe_certificados.update_one(
                {"id": certificado_id},
                {"$set": {"bloqueado_ate": None}}
            )
    
    # Verificar limite diário (3 consultas por dia)
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    consultas_hoje = certificado.get("consultas_hoje", 0)
    data_consultas = certificado.get("data_consultas")
    
    # Resetar contador se mudou o dia
    if data_consultas != hoje:
        consultas_hoje = 0
        await db.nfe_certificados.update_one(
            {"id": certificado_id},
            {"$set": {"consultas_hoje": 0, "data_consultas": hoje}}
        )
    
    LIMITE_DIARIO = 3
    if consultas_hoje >= LIMITE_DIARIO:
        raise HTTPException(
            status_code=429,
            detail=f"Limite diário de {LIMITE_DIARIO} consultas atingido. Tente novamente amanhã."
        )
    
    novas_importadas = 0
    ultimo_nsu_processado = certificado.get("ultimo_nsu", "000000000000000")
    
    try:
        import tempfile
        import gzip
        from xml.etree import ElementTree as ET
        
        cert_data = base64.b64decode(certificado["certificado_base64"])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pfx') as cert_file:
            cert_file.write(cert_data)
            cert_path = cert_file.name
        
        ns = {
            'nfe': 'http://www.portalfiscal.inf.br/nfe',
            'res': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe'
        }
        
        async def processar_nfe_xml(xml_content, nsu):
            try:
                root = ET.fromstring(xml_content)
                nfe = root.find('.//nfe:NFe', ns) or root.find('.//NFe') or root
                inf_nfe = nfe.find('.//nfe:infNFe', ns) or nfe.find('.//infNFe') or root.find('.//infNFe')
                
                if inf_nfe is None:
                    res_nfe = root.find('.//nfe:resNFe', ns) or root.find('.//resNFe')
                    if res_nfe is not None:
                        chave = res_nfe.findtext('.//nfe:chNFe', '', ns) or res_nfe.findtext('.//chNFe', '')
                        cnpj_emit = res_nfe.findtext('.//nfe:CNPJ', '', ns) or res_nfe.findtext('.//CNPJ', '')
                        razao_emit = res_nfe.findtext('.//nfe:xNome', '', ns) or res_nfe.findtext('.//xNome', '')
                        valor = res_nfe.findtext('.//nfe:vNF', '0', ns) or res_nfe.findtext('.//vNF', '0')
                        data_emissao = res_nfe.findtext('.//nfe:dhEmi', '', ns) or res_nfe.findtext('.//dhEmi', '')
                        
                        existing = await db.nfe_importadas.find_one({"chave_acesso": chave})
                        if existing:
                            return False
                        
                        numero_nf = chave[25:34].lstrip('0') if len(chave) >= 34 else ""
                        serie = chave[22:25].lstrip('0') if len(chave) >= 25 else "1"
                        
                        doc = {
                            "id": str(uuid.uuid4()),
                            "certificado_id": certificado_id,
                            "cnpj_destinatario": certificado["cnpj"],
                            "chave_acesso": chave,
                            "numero_nf": numero_nf or "N/A",
                            "serie": serie or "1",
                            "data_emissao": data_emissao[:10] if data_emissao else datetime.now(timezone.utc).isoformat()[:10],
                            "cnpj_emitente": cnpj_emit,
                            "razao_social_emitente": razao_emit or "Emitente não identificado",
                            "valor_total": float(valor) if valor else 0.0,
                            "itens": [],
                            "xml_base64": base64.b64encode(xml_content.encode()).decode() if isinstance(xml_content, str) else base64.b64encode(xml_content).decode(),
                            "nsu": nsu,
                            "conta_pagar_id": None,
                            "status": "nova",
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                        await db.nfe_importadas.insert_one(doc)
                        return True
                    return False
                
                ide = inf_nfe.find('.//nfe:ide', ns) or inf_nfe.find('.//ide')
                emit = inf_nfe.find('.//nfe:emit', ns) or inf_nfe.find('.//emit')
                total = inf_nfe.find('.//nfe:total', ns) or inf_nfe.find('.//total')
                
                chave = inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe.get('Id') else ''
                
                if chave:
                    existing = await db.nfe_importadas.find_one({"chave_acesso": chave})
                    if existing:
                        return False
                
                numero_nf = ide.findtext('.//nfe:nNF', '', ns) if ide else '' or ide.findtext('.//nNF', '') if ide else ''
                serie = ide.findtext('.//nfe:serie', '1', ns) if ide else '1' or ide.findtext('.//serie', '1') if ide else '1'
                data_emissao = ide.findtext('.//nfe:dhEmi', '', ns) if ide else '' or ide.findtext('.//dhEmi', '') if ide else ''
                
                cnpj_emit = emit.findtext('.//nfe:CNPJ', '', ns) if emit else '' or emit.findtext('.//CNPJ', '') if emit else ''
                razao_emit = emit.findtext('.//nfe:xNome', '', ns) if emit else '' or emit.findtext('.//xNome', '') if emit else ''
                
                icms_tot = total.find('.//nfe:ICMSTot', ns) if total else None or total.find('.//ICMSTot') if total else None
                valor_nf = icms_tot.findtext('.//nfe:vNF', '0', ns) if icms_tot else '0' or icms_tot.findtext('.//vNF', '0') if icms_tot else '0'
                
                itens = []
                det_list = inf_nfe.findall('.//nfe:det', ns) or inf_nfe.findall('.//det')
                for det in det_list:
                    prod = det.find('.//nfe:prod', ns) or det.find('.//prod')
                    if prod:
                        item = {
                            "codigo": prod.findtext('.//nfe:cProd', '', ns) or prod.findtext('.//cProd', ''),
                            "descricao": prod.findtext('.//nfe:xProd', '', ns) or prod.findtext('.//xProd', ''),
                            "ncm": prod.findtext('.//nfe:NCM', '', ns) or prod.findtext('.//NCM', ''),
                            "cfop": prod.findtext('.//nfe:CFOP', '', ns) or prod.findtext('.//CFOP', ''),
                            "unidade": prod.findtext('.//nfe:uCom', '', ns) or prod.findtext('.//uCom', ''),
                            "quantidade": float(prod.findtext('.//nfe:qCom', '0', ns) or prod.findtext('.//qCom', '0')),
                            "valor_unitario": float(prod.findtext('.//nfe:vUnCom', '0', ns) or prod.findtext('.//vUnCom', '0')),
                            "valor_total": float(prod.findtext('.//nfe:vProd', '0', ns) or prod.findtext('.//vProd', '0'))
                        }
                        itens.append(item)
                
                doc = {
                    "id": str(uuid.uuid4()),
                    "certificado_id": certificado_id,
                    "cnpj_destinatario": certificado["cnpj"],
                    "chave_acesso": chave,
                    "numero_nf": numero_nf or "N/A",
                    "serie": serie or "1",
                    "data_emissao": data_emissao[:10] if data_emissao else datetime.now(timezone.utc).isoformat()[:10],
                    "cnpj_emitente": cnpj_emit,
                    "razao_social_emitente": razao_emit or "Emitente não identificado",
                    "valor_total": float(valor_nf) if valor_nf else 0.0,
                    "itens": itens,
                    "xml_base64": base64.b64encode(xml_content.encode()).decode() if isinstance(xml_content, str) else base64.b64encode(xml_content).decode(),
                    "nsu": nsu,
                    "conta_pagar_id": None,
                    "status": "nova",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.nfe_importadas.insert_one(doc)
                return True
                
            except Exception as e:
                logger.error(f"Erro ao processar XML da NF-e: {e}")
                return False
        
        consulta_realizada = False
        try:
            from pynfe.processamento.comunicacao import ComunicacaoSefaz
            
            con = ComunicacaoSefaz(
                uf=certificado.get("uf", "SP"),
                certificado=cert_path,
                certificado_senha=certificado["senha_certificado"],
                homologacao=(certificado.get("ambiente", "producao") == "homologacao")
            )
            
            ultimo_nsu = "000000000000000" if desde_inicio else certificado.get("ultimo_nsu", "000000000000000")
            
            # Importação completa: SEFAZ retorna até ~50 docs/chamada via cursor NSU.
            # Iteramos até esgotar o cursor (ultNSU >= maxNSU) ou bater o teto de segurança.
            # Teto de 100 iterações ≈ 5.000 NF-e em uma única importação.
            max_iteracoes = 100
            iteracoes_realizadas = 0
            for i in range(max_iteracoes):
                iteracoes_realizadas = i + 1
                try:
                    resposta = con.consulta_distribuicao(
                        cnpj=certificado["cnpj"],
                        nsu=int(ultimo_nsu) if ultimo_nsu.isdigit() else 0
                    )
                    
                    if resposta:
                        if hasattr(resposta, 'text'):
                            xml_resposta = resposta.text
                        elif hasattr(resposta, 'content'):
                            xml_resposta = resposta.content.decode('utf-8')
                        elif isinstance(resposta, bytes):
                            xml_resposta = resposta.decode('utf-8')
                        elif isinstance(resposta, str):
                            xml_resposta = resposta
                        else:
                            xml_resposta = str(resposta)
                        
                        logger.info(f"Resposta SEFAZ recebida, tamanho: {len(xml_resposta)} bytes")
                        
                        root = ET.fromstring(xml_resposta)
                        
                        cStat = root.findtext('.//cStat') or root.findtext('.//{http://www.portalfiscal.inf.br/nfe}cStat')
                        
                        if cStat == '138':
                            docs = root.findall('.//docZip') or root.findall('.//{http://www.portalfiscal.inf.br/nfe}docZip')
                            
                            for doc in docs:
                                nsu = doc.get('NSU', '')
                                
                                try:
                                    content_b64 = doc.text
                                    if content_b64:
                                        content_gzip = base64.b64decode(content_b64)
                                        xml_content = gzip.decompress(content_gzip).decode('utf-8')
                                        
                                        if await processar_nfe_xml(xml_content, nsu):
                                            novas_importadas += 1
                                        
                                        if nsu > ultimo_nsu_processado:
                                            ultimo_nsu_processado = nsu
                                except Exception as doc_error:
                                    logger.warning(f"Erro ao processar documento NSU {nsu}: {doc_error}")
                            
                            ultNSU = root.findtext('.//ultNSU') or root.findtext('.//{http://www.portalfiscal.inf.br/nfe}ultNSU')
                            maxNSU = root.findtext('.//maxNSU') or root.findtext('.//{http://www.portalfiscal.inf.br/nfe}maxNSU')
                            
                            if ultNSU and maxNSU and ultNSU >= maxNSU:
                                break
                            
                            ultimo_nsu = ultNSU or ultimo_nsu
                            
                        elif cStat == '137':
                            logger.info("Nenhum novo documento encontrado na SEFAZ")
                            break
                        elif cStat == '656':
                            xMotivo = root.findtext('.//xMotivo') or root.findtext('.//{http://www.portalfiscal.inf.br/nfe}xMotivo')
                            logger.warning(f"SEFAZ: Consumo Indevido - {xMotivo}")
                            
                            # Bloquear por 1 hora
                            bloqueio_ate = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                            await db.nfe_certificados.update_one(
                                {"id": certificado_id},
                                {"$set": {"bloqueado_ate": bloqueio_ate}}
                            )
                            
                            return {
                                "message": "SEFAZ: Limite de consultas excedido",
                                "novas_nfes": 0,
                                "total_novas": await db.nfe_importadas.count_documents({"certificado_id": certificado_id, "status": "nova"}),
                                "certificado_id": certificado_id,
                                "ultimo_nsu": ultimo_nsu_processado,
                                "aviso": "O certificado atingiu o limite de consultas da SEFAZ. Aguarde 1 hora e tente novamente.",
                                "bloqueado_ate": bloqueio_ate
                            }
                        elif cStat == '593':
                            xMotivo = root.findtext('.//xMotivo') or root.findtext('.//{http://www.portalfiscal.inf.br/nfe}xMotivo')
                            logger.warning(f"SEFAZ: CNPJ não autorizado - {xMotivo}")
                            break
                        else:
                            xMotivo = root.findtext('.//xMotivo') or root.findtext('.//{http://www.portalfiscal.inf.br/nfe}xMotivo') or "Sem descrição"
                            logger.warning(f"Resposta da SEFAZ com status: {cStat} - {xMotivo}")
                            break
                    else:
                        break
                        
                except Exception as iter_error:
                    logger.warning(f"Erro na iteração {i}: {iter_error}")
                    break
            
            consulta_realizada = True
            
            # Incrementar contador de consultas do dia
            await db.nfe_certificados.update_one(
                {"id": certificado_id},
                {"$inc": {"consultas_hoje": 1}}
            )
            
        except ImportError:
            logger.warning("PyNFe não disponível")
        except Exception as pynfe_error:
            logger.warning(f"Erro ao consultar SEFAZ via PyNFe: {pynfe_error}")
        
        import os as os_module
        try:
            os_module.unlink(cert_path)
        except:
            pass
        
        if ultimo_nsu_processado != certificado.get("ultimo_nsu", "000000000000000"):
            await db.nfe_certificados.update_one(
                {"id": certificado_id},
                {"$set": {
                    "ultimo_nsu": ultimo_nsu_processado,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        else:
            await db.nfe_certificados.update_one(
                {"id": certificado_id},
                {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
            )
        
        total_novas = await db.nfe_importadas.count_documents({
            "certificado_id": certificado_id,
            "status": "nova"
        })
        
        if novas_importadas > 0:
            await db.notifications.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": current_user.get("id"),
                "title": f"{novas_importadas} nova(s) NF-e importada(s)",
                "message": f"Foram importadas {novas_importadas} notas fiscais para {certificado['razao_social']}",
                "type": "info",
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        status_message = "Consulta realizada com sucesso" if consulta_realizada else "Consulta realizada (modo offline)"
        if desde_inicio:
            status_message += " (varredura completa do histórico)"
        
        return {
            "message": status_message,
            "novas_nfes": novas_importadas,
            "total_novas": total_novas,
            "certificado_id": certificado_id,
            "ultimo_nsu": ultimo_nsu_processado,
            "iteracoes_realizadas": iteracoes_realizadas if 'iteracoes_realizadas' in locals() else 0,
            "desde_inicio": desde_inicio,
            "aviso": None
        }
        
    except Exception as e:
        logger.error(f"Erro ao importar NF-e: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar SEFAZ: {str(e)}")


@importacao_router.post("/nfse/importar/{certificado_id}")
async def importar_nfse(certificado_id: str, current_user: dict = Depends(get_current_user)):
    """Consulta e importa NFS-e do webservice municipal (padrão ABRASF) para o CNPJ especificado"""
    certificado = await db.nfe_certificados.find_one({"id": certificado_id})
    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")

    if not certificado.get("ativo"):
        raise HTTPException(status_code=400, detail="Certificado inativo")

    url_nfse = (certificado.get("url_nfse") or "").strip()
    if not url_nfse:
        return {
            "message": "Importação NFS-e ignorada: URL do webservice não configurada",
            "novas_nfses": 0,
            "aviso": "Para importar NFS-e, configure a URL do webservice NFS-e da prefeitura no cadastro do certificado."
        }

    cnpj_limpo = certificado["cnpj"].replace(".", "").replace("/", "").replace("-", "")
    inscricao_municipal = (certificado.get("inscricao_municipal") or "").strip()
    novas_importadas = 0
    erros = []

    try:
        import tempfile
        import requests as req_sync
        from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption, PublicFormat
        from xml.etree import ElementTree as ET

        cert_data = base64.b64decode(certificado["certificado_base64"])
        senha = certificado.get("senha_certificado", "")

        # Converter PFX para PEM para uso com requests
        private_key, certificate_obj, _ = pkcs12.load_key_and_certificates(
            cert_data, senha.encode() if senha else None
        )
        key_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        cert_pem_bytes = certificate_obj.public_bytes(Encoding.PEM)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as f:
            f.write(cert_pem_bytes)
            cert_pem_path = f.name
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as f:
            f.write(key_pem)
            key_pem_path = f.name

        # Período: últimos 5 ANOS, dividido em chunks de 90 dias (limite típico ABRASF v2)
        data_final_total = datetime.now()
        data_inicial_total = data_final_total - timedelta(days=365 * 5)
        CHUNK_DAYS = 90

        # Construir lista de janelas (mais antigas primeiro)
        janelas: list[tuple[datetime, datetime]] = []
        cursor = data_inicial_total
        while cursor < data_final_total:
            fim = min(cursor + timedelta(days=CHUNK_DAYS - 1), data_final_total)
            janelas.append((cursor, fim))
            cursor = fim + timedelta(days=1)

        cabecalho_xml = '<?xml version="1.0" encoding="UTF-8"?><cabecalho versao="2.01" xmlns="http://www.abrasf.org.br/nfse.xsd"><versaoDados>2.01</versaoDados></cabecalho>'
        im_tag = f"<InscricaoMunicipal>{inscricao_municipal}</InscricaoMunicipal>" if inscricao_municipal else ""

        headers_soap_base = {
            "Content-Type": "text/xml; charset=utf-8",
        }

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        total_encontradas = 0
        duplicadas = 0
        soapaction_persistido = certificado.get("soapaction_nfse")
        ultimo_response_erro = None
        ultima_tentativas_sa: list = []
        chunks_processados = 0
        chunks_falhados = 0

        # NFSE_NS para parsing das respostas
        NFSE_NS = "http://www.abrasf.org.br/nfse.xsd"

        def find_text(el, tag):
            for child in el.iter():
                local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if local == tag:
                    return (child.text or "").strip()
            return ""

        for janela_ini, janela_fim in janelas:
            dados_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ConsultarNfseServicoTomadoEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">
  <Consulente>
    <CpfCnpj><Cnpj>{cnpj_limpo}</Cnpj></CpfCnpj>
    {im_tag}
  </Consulente>
  <PeriodoEmissao>
    <DataInicial>{janela_ini.strftime('%Y-%m-%d')}</DataInicial>
    <DataFinal>{janela_fim.strftime('%Y-%m-%d')}</DataFinal>
  </PeriodoEmissao>
</ConsultarNfseServicoTomadoEnvio>"""

            soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:nfse="http://nfse.abrasf.org.br">
  <soap:Header/>
  <soap:Body>
    <nfse:ConsultarNfseServicoTomadoRequest>
      <nfseCabecMsg>{cabecalho_xml.replace('<','&lt;').replace('>','&gt;')}</nfseCabecMsg>
      <nfseDadosMsg>{dados_xml.replace('<','&lt;').replace('>','&gt;')}</nfseDadosMsg>
    </nfse:ConsultarNfseServicoTomadoRequest>
  </soap:Body>
</soap:Envelope>"""

            try:
                response, soapaction_usado, tentativas_sa = _post_nfse_com_fallback_soapaction(
                    url_nfse=url_nfse,
                    soap_envelope_bytes=soap_envelope.encode("utf-8"),
                    cert_tuple=(cert_pem_path, key_pem_path),
                    base_headers=headers_soap_base,
                    timeout=30,
                    operation="ConsultarNfseServicoTomado",
                    preferred_soapaction=soapaction_persistido,
                )
            except Exception as call_err:
                logger.warning(f"NFS-e chunk {janela_ini.date()}-{janela_fim.date()} falhou: {call_err}")
                chunks_falhados += 1
                continue

            if response is None:
                ultima_tentativas_sa = tentativas_sa
                chunks_falhados += 1
                # Se primeiro chunk falhou catastroficamente (mTLS/SSL), interrompe
                if chunks_processados == 0:
                    break
                continue

            if response.status_code != 200:
                ultimo_response_erro = response
                chunks_falhados += 1
                if chunks_processados == 0:
                    break
                continue

            body_lower = (response.text or "").lower()
            if "<soap:fault" in body_lower or "<s:fault" in body_lower or "<faultstring" in body_lower:
                ultimo_response_erro = response
                chunks_falhados += 1
                if chunks_processados == 0:
                    break
                continue

            # Atualiza SOAPAction persistido (na primeira chamada bem-sucedida)
            if soapaction_usado and soapaction_persistido != soapaction_usado:
                soapaction_persistido = soapaction_usado

            # Parse XML
            try:
                root = ET.fromstring(response.text)
            except ET.ParseError:
                inner = re.search(r'<\?xml.*?</\w+Resposta>', response.text, re.DOTALL)
                if inner:
                    try:
                        root = ET.fromstring(inner.group())
                    except Exception:
                        chunks_falhados += 1
                        continue
                else:
                    chunks_falhados += 1
                    continue

            # Mensagens de retorno (avisos do webservice)
            lista_mensagens = root.findall(f".//{{{NFSE_NS}}}ListaMensagemRetorno") or root.findall(".//ListaMensagemRetorno")
            if lista_mensagens:
                for msg in lista_mensagens:
                    codigo = find_text(msg, "Codigo")
                    descricao = find_text(msg, "Descricao")
                    if codigo and codigo not in ("0", "S"):
                        msg_chunk = f"[{codigo}] {descricao}"
                        if msg_chunk not in erros:
                            erros.append(msg_chunk)

            # Extrair NFS-e do chunk
            comp_nfses = root.findall(f".//{{{NFSE_NS}}}CompNfse") or root.findall(".//CompNfse")
            total_encontradas += len(comp_nfses)

            for comp in comp_nfses:
                try:
                    numero = find_text(comp, "Numero")
                    codigo_verificacao = find_text(comp, "CodigoVerificacao")
                    data_emissao = find_text(comp, "DataEmissao")
                    discriminacao = find_text(comp, "Discriminacao")
                    valor_servicos = find_text(comp, "ValorServicos") or find_text(comp, "ValorLiquidoNfse")
                    valor_iss = find_text(comp, "ValorIss") or "0"
                    cnpj_prestador = find_text(comp, "Cnpj")
                    razao_prestador = find_text(comp, "RazaoSocial")
                    inscricao_prestador = find_text(comp, "InscricaoMunicipal")

                    if not numero:
                        continue

                    existente = await db.nfse_importadas.find_one({
                        "numero_nota": numero,
                        "cnpj_emitente": cnpj_prestador or numero
                    })
                    if existente:
                        duplicadas += 1
                        continue

                    try:
                        valor_float = float(valor_servicos.replace(",", ".")) if valor_servicos else 0.0
                    except (ValueError, TypeError):
                        valor_float = 0.0

                    nfse_id = str(uuid.uuid4())
                    nfse_doc = {
                        "id": nfse_id,
                        "numero_nota": numero,
                        "serie": "1",
                        "chave_acesso": codigo_verificacao or f"{cnpj_limpo}-{numero}",
                        "data_emissao": data_emissao[:10] if data_emissao else datetime.now().strftime("%Y-%m-%d"),
                        "cnpj_emitente": cnpj_prestador,
                        "razao_social_emitente": razao_prestador,
                        "prestador_nome": razao_prestador,
                        "cnpj_destinatario": cnpj_limpo,
                        "valor_total": valor_float,
                        "valor_servicos": valor_float,
                        "valor_iss": float(valor_iss.replace(",", ".")) if valor_iss else 0.0,
                        "descricao_servico": discriminacao,
                        "inscricao_municipal_prestador": inscricao_prestador,
                        "certificado_id": certificado_id,
                        "importacao_manual": False,
                        "status": "nova",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.nfse_importadas.insert_one(nfse_doc)
                    novas_importadas += 1

                except Exception as e_item:
                    logger.warning(f"Erro ao processar NFS-e item: {e_item}")
                    continue

            chunks_processados += 1

        # Limpar temporários (uma vez no fim)
        for p in [cert_pem_path, key_pem_path]:
            try:
                os.unlink(p)
            except Exception:
                pass

        # Persistir SOAPAction caso tenha sido descoberto
        if soapaction_persistido and certificado.get("soapaction_nfse") != soapaction_persistido:
            try:
                await db.nfe_certificados.update_one(
                    {"id": certificado_id},
                    {"$set": {"soapaction_nfse": soapaction_persistido}},
                )
            except Exception:
                pass

        # Diagnóstico se NENHUM chunk teve sucesso
        if chunks_processados == 0:
            if ultimo_response_erro is not None:
                erro_legivel = _parse_nfse_soap_error(ultimo_response_erro.text)
                return {
                    "message": f"Webservice NFS-e retornou erro HTTP {ultimo_response_erro.status_code}",
                    "novas_nfses": 0,
                    "aviso": f"Detalhes do servidor: {erro_legivel}",
                    "chunks_processados": 0,
                    "chunks_falhados": chunks_falhados,
                }
            ultima_tentativa = ultima_tentativas_sa[-1] if ultima_tentativas_sa else {}
            ultimo_erro = (ultima_tentativa.get("erro", "") or "").lower()
            if "remote end closed" in ultimo_erro or "connection reset" in ultimo_erro or "ssl" in ultimo_erro or "handshake" in ultimo_erro:
                aviso_clara = (
                    "O servidor da Prefeitura FECHOU a conexão TLS imediatamente — isto indica que o "
                    "CERTIFICADO DIGITAL A1 foi REJEITADO (mTLS). Causas mais comuns: "
                    "1) Certificado expirado ou senha incorreta; "
                    "2) Certificado é de OUTRO CNPJ (deve ser e-CNPJ exato da empresa tomadora); "
                    "3) CNPJ não está cadastrado como contribuinte em Palmas-TO; "
                    "4) Inscrição Municipal incorreta. "
                    "Acesse https://palmasto.webiss.com.br/ , faça login com o certificado "
                    "que você uploadou aqui e verifique se a empresa aparece corretamente."
                )
            else:
                aviso_clara = f"Nenhum SOAPAction foi aceito pelo servidor. Última mensagem: {ultima_tentativa}"
            return {
                "message": "Falha de conexão com o webservice NFS-e",
                "novas_nfses": 0,
                "aviso": aviso_clara,
                "diagnostico_tecnico": str(ultima_tentativas_sa)[:500],
                "chunks_processados": 0,
                "chunks_falhados": chunks_falhados,
            }

    except req_sync.exceptions.SSLError as e:
        return {
            "message": "Erro SSL ao conectar ao webservice NFS-e",
            "novas_nfses": 0,
            "aviso": f"Verifique o certificado e a URL NFS-e. Detalhes: {str(e)[:200]}"
        }
    except req_sync.exceptions.ConnectionError as e:
        return {
            "message": "Não foi possível conectar ao webservice NFS-e",
            "novas_nfses": 0,
            "aviso": f"Verifique a URL NFS-e: {url_nfse}. Erro: {str(e)[:200]}"
        }
    except Exception as e:
        logger.error(f"Erro ao importar NFS-e: {e}")
        return {
            "message": f"Erro na importação NFS-e: {str(e)[:200]}",
            "novas_nfses": 0,
            "aviso": str(e)[:300]
        }

    mensagem = f"{novas_importadas} nova(s) NFS-e importada(s)"
    if erros:
        mensagem += f" | Avisos: {'; '.join(erros[:2])}"

    resp = {
        "message": mensagem,
        "novas_nfses": novas_importadas,
        "erros": erros,
        "total_encontradas": total_encontradas if 'total_encontradas' in locals() else 0,
        "duplicadas": duplicadas if 'duplicadas' in locals() else 0,
        "chunks_processados": chunks_processados if 'chunks_processados' in locals() else 0,
        "chunks_falhados": chunks_falhados if 'chunks_falhados' in locals() else 0,
    }
    # Se webservice respondeu OK mas 0 NFS-e foram encontradas, sinaliza isso ao usuário
    if novas_importadas == 0 and not erros and resp["total_encontradas"] == 0:
        resp["aviso"] = (
            f"Webservice respondeu OK em {resp['chunks_processados']} janelas (5 anos retroativos), mas não retornou nenhuma NFS-e para "
            f"CNPJ {cnpj_limpo} (IM {inscricao_municipal or 'não informada'}). "
            f"Verifique: 1) Inscrição Municipal correta; 2) CNPJ é tomador de algum serviço; "
            f"3) Notas foram emitidas em PALMAS-TO. Use o botão 'Testar Conexão' para diagnóstico."
        )
    elif novas_importadas == 0 and resp["total_encontradas"] > 0:
        resp["aviso"] = (
            f"Encontradas {resp['total_encontradas']} NFS-e no webservice mas todas já estavam importadas (duplicadas: {resp['duplicadas']})."
        )
    return resp



@importacao_router.post("/nfse/testar-conexao/{certificado_id}")
async def testar_conexao_nfse(certificado_id: str, current_user: dict = Depends(get_current_user)):
    """Testa a conectividade e autenticação do certificado contra o webservice NFS-e
    e conta o total de NFS-e disponíveis no histórico (varre últimos 5 anos em chunks
    de 90 dias — limite ABRASF v2). NÃO importa notas — apenas valida e contabiliza."""
    certificado = await db.nfe_certificados.find_one({"id": certificado_id}, {"_id": 0})
    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")

    if not certificado.get("ativo"):
        return {"ok": False, "etapa": "certificado", "mensagem": "Certificado inativo. Ative-o antes de testar."}

    url_nfse = (certificado.get("url_nfse") or "").strip()
    if not url_nfse:
        return {"ok": False, "etapa": "configuracao", "mensagem": "URL do webservice NFS-e não configurada. Preencha o campo 'URL Webservice' no cadastro do certificado."}

    cnpj_limpo = (certificado.get("cnpj") or "").replace(".", "").replace("/", "").replace("-", "")
    inscricao_municipal = (certificado.get("inscricao_municipal") or "").strip()

    try:
        import tempfile
        import requests as req_sync
        from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Etapa 1: carregar certificado A1
        try:
            cert_data = base64.b64decode(certificado.get("certificado_base64") or "")
            senha = certificado.get("senha_certificado", "")
            private_key, certificate_obj, _ = pkcs12.load_key_and_certificates(
                cert_data, senha.encode() if senha else None
            )
        except Exception as ce:
            return {
                "ok": False,
                "etapa": "certificado",
                "mensagem": f"Falha ao abrir certificado A1: {str(ce)[:200]}. Verifique arquivo .pfx e senha.",
            }

        key_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        cert_pem_bytes = certificate_obj.public_bytes(Encoding.PEM)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as f:
            f.write(cert_pem_bytes)
            cert_pem_path = f.name
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as f:
            f.write(key_pem)
            key_pem_path = f.name

        # Etapa 2: montar janelas de 90 dias cobrindo os últimos 5 anos
        data_final_total = datetime.now()
        data_inicial_total = data_final_total - timedelta(days=365 * 5)
        CHUNK_DAYS = 90
        janelas: list[tuple[datetime, datetime]] = []
        cursor = data_inicial_total
        while cursor < data_final_total:
            fim = min(cursor + timedelta(days=CHUNK_DAYS - 1), data_final_total)
            janelas.append((cursor, fim))
            cursor = fim + timedelta(days=1)

        cabecalho_xml = '<?xml version="1.0" encoding="UTF-8"?><cabecalho versao="2.01" xmlns="http://www.abrasf.org.br/nfse.xsd"><versaoDados>2.01</versaoDados></cabecalho>'
        im_tag = f"<InscricaoMunicipal>{inscricao_municipal}</InscricaoMunicipal>" if inscricao_municipal else ""
        headers_soap_base = {"Content-Type": "text/xml; charset=utf-8"}

        total_nfses = 0
        chunks_ok = 0
        chunks_falhados = 0
        soapaction_persistido = certificado.get("soapaction_nfse")
        primeiro_erro_response = None
        primeiro_erro_tentativas: list = []
        primeiro_erro_excecao: Optional[str] = None
        msgs_negocio: list[str] = []

        for janela_ini, janela_fim in janelas:
            dados_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ConsultarNfseServicoTomadoEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">
  <Consulente>
    <CpfCnpj><Cnpj>{cnpj_limpo}</Cnpj></CpfCnpj>
    {im_tag}
  </Consulente>
  <PeriodoEmissao>
    <DataInicial>{janela_ini.strftime('%Y-%m-%d')}</DataInicial>
    <DataFinal>{janela_fim.strftime('%Y-%m-%d')}</DataFinal>
  </PeriodoEmissao>
</ConsultarNfseServicoTomadoEnvio>"""
            soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:nfse="http://nfse.abrasf.org.br">
  <soap:Header/>
  <soap:Body>
    <nfse:ConsultarNfseServicoTomadoRequest>
      <nfseCabecMsg>{cabecalho_xml.replace('<','&lt;').replace('>','&gt;')}</nfseCabecMsg>
      <nfseDadosMsg>{dados_xml.replace('<','&lt;').replace('>','&gt;')}</nfseDadosMsg>
    </nfse:ConsultarNfseServicoTomadoRequest>
  </soap:Body>
</soap:Envelope>"""

            try:
                response, soapaction_usado, tentativas_sa = _post_nfse_com_fallback_soapaction(
                    url_nfse=url_nfse,
                    soap_envelope_bytes=soap_envelope.encode("utf-8"),
                    cert_tuple=(cert_pem_path, key_pem_path),
                    base_headers=headers_soap_base,
                    timeout=15,
                    operation="ConsultarNfseServicoTomado",
                    preferred_soapaction=soapaction_persistido,
                )
            except req_sync.exceptions.SSLError as e:
                primeiro_erro_excecao = f"SSL: {str(e)[:200]}"
                chunks_falhados += 1
                if chunks_ok == 0:
                    break
                continue
            except (req_sync.exceptions.ConnectTimeout, req_sync.exceptions.ConnectionError) as e:
                primeiro_erro_excecao = f"Conexão: {str(e)[:200]}"
                chunks_falhados += 1
                if chunks_ok == 0:
                    break
                continue

            if response is None:
                if not primeiro_erro_tentativas:
                    primeiro_erro_tentativas = tentativas_sa
                chunks_falhados += 1
                if chunks_ok == 0:
                    break
                continue

            if response.status_code != 200:
                if primeiro_erro_response is None:
                    primeiro_erro_response = response
                chunks_falhados += 1
                if chunks_ok == 0:
                    break
                continue

            body_lower = (response.text or "").lower()
            if "<soap:fault" in body_lower or "<s:fault" in body_lower or "<faultstring" in body_lower:
                if primeiro_erro_response is None:
                    primeiro_erro_response = response
                chunks_falhados += 1
                if chunks_ok == 0:
                    break
                continue

            # Sucesso de SOAPAction → persiste
            if soapaction_usado and soapaction_persistido != soapaction_usado:
                soapaction_persistido = soapaction_usado

            try:
                root = ET.fromstring(response.text)
            except ET.ParseError:
                inner = re.search(r'<\?xml.*?</\w+Resposta>', response.text, re.DOTALL)
                if inner:
                    try:
                        root = ET.fromstring(inner.group())
                    except Exception:
                        chunks_falhados += 1
                        continue
                else:
                    chunks_falhados += 1
                    continue

            for msg in root.iter():
                tag = msg.tag.split('}')[-1] if '}' in msg.tag else msg.tag
                if tag == "MensagemRetorno":
                    codigo = ""
                    descricao = ""
                    for c in msg.iter():
                        ctag = c.tag.split('}')[-1] if '}' in c.tag else c.tag
                        if ctag == "Codigo" and c.text:
                            codigo = c.text.strip()
                        elif ctag == "Descricao" and c.text:
                            descricao = c.text.strip()
                    if codigo and codigo not in ("0", "S") and descricao:
                        msg_chunk = f"[Cód {codigo}] {descricao}"
                        if msg_chunk not in msgs_negocio:
                            msgs_negocio.append(msg_chunk)
                elif tag == "CompNfse":
                    total_nfses += 1

            chunks_ok += 1

        # Limpar temporários
        for p in [cert_pem_path, key_pem_path]:
            try:
                os.unlink(p)
            except Exception:
                pass

        # Persistir SOAPAction caso descoberto
        if soapaction_persistido and certificado.get("soapaction_nfse") != soapaction_persistido:
            try:
                await db.nfe_certificados.update_one(
                    {"id": certificado_id},
                    {"$set": {"soapaction_nfse": soapaction_persistido}},
                )
            except Exception:
                pass

        # Diagnóstico se NENHUM chunk teve sucesso
        if chunks_ok == 0:
            if primeiro_erro_response is not None:
                return {
                    "ok": False,
                    "etapa": "http" if primeiro_erro_response.status_code != 200 else "soap_fault",
                    "mensagem": f"HTTP {primeiro_erro_response.status_code}: {_parse_nfse_soap_error(primeiro_erro_response.text)}",
                }
            if primeiro_erro_excecao:
                return {"ok": False, "etapa": "ssl_ou_conexao", "mensagem": primeiro_erro_excecao}
            ultima_tentativa = primeiro_erro_tentativas[-1] if primeiro_erro_tentativas else {}
            ultimo_erro = (ultima_tentativa.get("erro", "") or "").lower()
            if "remote end closed" in ultimo_erro or "connection reset" in ultimo_erro or "ssl" in ultimo_erro or "handshake" in ultimo_erro:
                return {
                    "ok": False,
                    "etapa": "mtls_rejeitado",
                    "mensagem": (
                        "O servidor da Prefeitura FECHOU a conexão TLS imediatamente — o certificado A1 "
                        "foi REJEITADO. Verifique: 1) Se o .pfx é o e-CNPJ da empresa tomadora; "
                        "2) Se a senha do certificado está correta; 3) Se o certificado está dentro "
                        "da validade; 4) Se o CNPJ está cadastrado como contribuinte em Palmas-TO. "
                        "Faça login em https://palmasto.webiss.com.br/ com o mesmo .pfx para confirmar."
                    ),
                    "diagnostico_tecnico": str(primeiro_erro_tentativas)[:500],
                }
            return {
                "ok": False,
                "etapa": "conexao",
                "mensagem": f"Nenhum SOAPAction aceito em {len(primeiro_erro_tentativas)} tentativas. Detalhe: {ultima_tentativa}",
            }

        # Sucesso: pelo menos 1 chunk respondeu OK
        if msgs_negocio:
            return {
                "ok": False,
                "etapa": "negocio",
                "mensagem": "Conexão e certificado OK, mas o webservice rejeitou parte da consulta: "
                            + " | ".join(msgs_negocio[:3])
                            + f" — {chunks_ok}/{len(janelas)} janelas processadas com sucesso.",
                "soapaction_usado": soapaction_persistido,
                "total_nfses": total_nfses,
                "chunks_ok": chunks_ok,
                "chunks_falhados": chunks_falhados,
            }

        return {
            "ok": True,
            "etapa": "sucesso",
            "mensagem": f"Conexão OK! Certificado válido e webservice respondendo. "
                        f"{total_nfses} NFS-e encontrada(s) no histórico (últimos 5 anos, "
                        f"{chunks_ok}/{len(janelas)} janelas processadas)."
                        + (f" SOAPAction aceito: '{soapaction_persistido}'" if soapaction_persistido else ""),
            "soapaction_usado": soapaction_persistido,
            "total_nfses": total_nfses,
            "chunks_ok": chunks_ok,
            "chunks_falhados": chunks_falhados,
        }

    except Exception as e:
        logger.error(f"Erro em testar_conexao_nfse: {e}")
        return {"ok": False, "etapa": "inesperado", "mensagem": f"Erro inesperado: {str(e)[:300]}"}
