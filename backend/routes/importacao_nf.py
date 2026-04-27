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


@importacao_router.post("/nfe/importar/{certificado_id}")
async def importar_nfe(certificado_id: str, current_user: dict = Depends(get_current_user)):
    """Consulta e importa NF-e da SEFAZ para o CNPJ especificado"""
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
            
            ultimo_nsu = certificado.get("ultimo_nsu", "000000000000000")
            
            max_iteracoes = 10
            for i in range(max_iteracoes):
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
        
        return {
            "message": status_message,
            "novas_nfes": novas_importadas,
            "total_novas": total_novas,
            "certificado_id": certificado_id,
            "ultimo_nsu": ultimo_nsu_processado,
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

        # Período: últimos 90 dias
        data_final = datetime.now()
        data_inicial = data_final - timedelta(days=90)

        # Montar SOAP envelope ABRASF v2.01
        cabecalho_xml = '<?xml version="1.0" encoding="UTF-8"?><cabecalho versao="2.01" xmlns="http://www.abrasf.org.br/nfse.xsd"><versaoDados>2.01</versaoDados></cabecalho>'
        
        im_tag = f"<InscricaoMunicipal>{inscricao_municipal}</InscricaoMunicipal>" if inscricao_municipal else ""
        dados_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ConsultarNfseRecebidosEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">
  <Consulente>
    <CpfCnpj><Cnpj>{cnpj_limpo}</Cnpj></CpfCnpj>
    {im_tag}
  </Consulente>
  <PeriodoEmissao>
    <DataInicial>{data_inicial.strftime('%Y-%m-%d')}</DataInicial>
    <DataFinal>{data_final.strftime('%Y-%m-%d')}</DataFinal>
  </PeriodoEmissao>
</ConsultarNfseRecebidosEnvio>"""

        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:nfse="http://www.abrasf.org.br/nfse.xsd">
  <soap:Header/>
  <soap:Body>
    <nfse:ConsultarNfseRecebidos>
      <nfse:nfseCabecMsg><![CDATA[{cabecalho_xml}]]></nfse:nfseCabecMsg>
      <nfse:nfseDadosMsg><![CDATA[{dados_xml}]]></nfse:nfseDadosMsg>
    </nfse:ConsultarNfseRecebidos>
  </soap:Body>
</soap:Envelope>"""

        headers_soap = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://www.abrasf.org.br/nfse.xsd/ConsultarNfseRecebidos"
        }

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = req_sync.post(
            url_nfse,
            data=soap_envelope.encode("utf-8"),
            headers=headers_soap,
            cert=(cert_pem_path, key_pem_path),
            verify=False,
            timeout=30
        )

        # Limpar temporários
        for p in [cert_pem_path, key_pem_path]:
            try:
                os.unlink(p)
            except Exception:
                pass

        if response.status_code != 200:
            # Tenta extrair mensagem útil do SOAP Fault / ListaMensagemRetorno
            erro_legivel = _parse_nfse_soap_error(response.text)
            return {
                "message": f"Webservice NFS-e retornou erro HTTP {response.status_code}",
                "novas_nfses": 0,
                "aviso": f"Detalhes do servidor: {erro_legivel}"
            }

        # Mesmo com status 200, resposta pode conter SOAP Fault ou erros de negócio:
        # detecta antes de tentar o parser de NFS-e e dá erro amigável.
        body_lower = response.text.lower()
        if "<soap:fault" in body_lower or "<s:fault" in body_lower or "<faultstring" in body_lower:
            erro_legivel = _parse_nfse_soap_error(response.text)
            return {
                "message": "Webservice NFS-e retornou um erro (SOAP Fault)",
                "novas_nfses": 0,
                "aviso": erro_legivel
            }

        # Parsear resposta XML
        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            # Tentar extrair conteúdo CDATA
            import re
            inner = re.search(r'<\?xml.*?</\w+Resposta>', response.text, re.DOTALL)
            if inner:
                root = ET.fromstring(inner.group())
            else:
                return {"message": "Resposta XML inválida do webservice NFS-e", "novas_nfses": 0,
                        "aviso": _parse_nfse_soap_error(response.text)}

        # Namespace ABRASF
        NFSE_NS = "http://www.abrasf.org.br/nfse.xsd"

        def find_text(el, tag):
            """Busca recursiva por tag ignorando namespace"""
            for child in el.iter():
                local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if local == tag:
                    return (child.text or "").strip()
            return ""

        # Verificar erros na resposta
        lista_mensagens = root.findall(f".//{{{NFSE_NS}}}ListaMensagemRetorno") or root.findall(".//ListaMensagemRetorno")
        if lista_mensagens:
            for msg in lista_mensagens:
                codigo = find_text(msg, "Codigo")
                descricao = find_text(msg, "Descricao")
                if codigo and codigo not in ("0", "S"):
                    erros.append(f"[{codigo}] {descricao}")

        # Extrair NFS-e
        comp_nfses = root.findall(f".//{{{NFSE_NS}}}CompNfse") or root.findall(".//CompNfse")

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

                # Verificar duplicata
                existente = await db.nfse_importadas.find_one({
                    "numero_nota": numero,
                    "cnpj_emitente": cnpj_prestador or numero
                })
                if existente:
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

    return {
        "message": mensagem,
        "novas_nfses": novas_importadas,
        "erros": erros
    }



@importacao_router.post("/nfse/testar-conexao/{certificado_id}")
async def testar_conexao_nfse(certificado_id: str, current_user: dict = Depends(get_current_user)):
    """Testa a conectividade e autenticação do certificado contra o webservice NFS-e.
    Faz uma chamada leve (últimos 7 dias) e interpreta a resposta, retornando diagnóstico.
    NÃO importa notas — apenas valida URL + certificado + inscrição municipal."""
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

        # Etapa 2: montar requisição curta (últimos 7 dias)
        data_final = datetime.now()
        data_inicial = data_final - timedelta(days=7)
        cabecalho_xml = '<?xml version="1.0" encoding="UTF-8"?><cabecalho versao="2.01" xmlns="http://www.abrasf.org.br/nfse.xsd"><versaoDados>2.01</versaoDados></cabecalho>'
        im_tag = f"<InscricaoMunicipal>{inscricao_municipal}</InscricaoMunicipal>" if inscricao_municipal else ""
        dados_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ConsultarNfseRecebidosEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">
  <Consulente>
    <CpfCnpj><Cnpj>{cnpj_limpo}</Cnpj></CpfCnpj>
    {im_tag}
  </Consulente>
  <PeriodoEmissao>
    <DataInicial>{data_inicial.strftime('%Y-%m-%d')}</DataInicial>
    <DataFinal>{data_final.strftime('%Y-%m-%d')}</DataFinal>
  </PeriodoEmissao>
</ConsultarNfseRecebidosEnvio>"""
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:nfse="http://www.abrasf.org.br/nfse.xsd">
  <soap:Header/>
  <soap:Body>
    <nfse:ConsultarNfseRecebidos>
      <nfse:nfseCabecMsg><![CDATA[{cabecalho_xml}]]></nfse:nfseCabecMsg>
      <nfse:nfseDadosMsg><![CDATA[{dados_xml}]]></nfse:nfseDadosMsg>
    </nfse:ConsultarNfseRecebidos>
  </soap:Body>
</soap:Envelope>"""
        headers_soap = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://www.abrasf.org.br/nfse.xsd/ConsultarNfseRecebidos",
        }

        # Etapa 3: chamada HTTP
        response = None
        try:
            response = req_sync.post(
                url_nfse,
                data=soap_envelope.encode("utf-8"),
                headers=headers_soap,
                cert=(cert_pem_path, key_pem_path),
                verify=False,
                timeout=15,
            )
        except req_sync.exceptions.SSLError as e:
            return {"ok": False, "etapa": "ssl",
                    "mensagem": f"Erro SSL ao conectar. Certificado pode estar expirado ou URL incorreta. Detalhes: {str(e)[:200]}"}
        except req_sync.exceptions.ConnectTimeout:
            return {"ok": False, "etapa": "timeout",
                    "mensagem": f"Timeout ao conectar em {url_nfse}. Verifique se o endpoint está online."}
        except req_sync.exceptions.ConnectionError as e:
            return {"ok": False, "etapa": "conexao",
                    "mensagem": f"Falha ao conectar em {url_nfse}: {str(e)[:200]}"}
        finally:
            for p in [cert_pem_path, key_pem_path]:
                try:
                    os.unlink(p)
                except Exception:
                    pass

        # Etapa 4: interpretar resposta
        body_lower = (response.text or "").lower()
        if response.status_code != 200:
            return {
                "ok": False,
                "etapa": "http",
                "mensagem": f"HTTP {response.status_code}: {_parse_nfse_soap_error(response.text)}",
            }

        if "<soap:fault" in body_lower or "<s:fault" in body_lower or "<faultstring" in body_lower:
            return {
                "ok": False,
                "etapa": "soap_fault",
                "mensagem": f"SOAP Fault: {_parse_nfse_soap_error(response.text)}",
            }

        try:
            root = ET.fromstring(response.text)
            msgs_with_error = []
            total_nfses = 0
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
                        msgs_with_error.append(f"[Cód {codigo}] {descricao}")
                elif tag == "CompNfse":
                    total_nfses += 1
            if msgs_with_error:
                return {
                    "ok": False,
                    "etapa": "negocio",
                    "mensagem": "Conexão e certificado OK, mas o webservice rejeitou a consulta: "
                                + " | ".join(msgs_with_error[:3]),
                }
            return {
                "ok": True,
                "etapa": "sucesso",
                "mensagem": f"Conexão OK! Certificado válido e webservice respondendo. {total_nfses} NFS-e encontrada(s) nos últimos 7 dias.",
            }
        except ET.ParseError:
            return {
                "ok": False,
                "etapa": "parse",
                "mensagem": f"Resposta não é XML válido. Verifique se a URL aponta para o endpoint correto. Amostra: {_parse_nfse_soap_error(response.text)}",
            }

    except Exception as e:
        logger.error(f"Erro em testar_conexao_nfse: {e}")
        return {"ok": False, "etapa": "inesperado", "mensagem": f"Erro inesperado: {str(e)[:300]}"}
