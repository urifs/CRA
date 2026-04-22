"""
DANFE (Documento Auxiliar da Nota Fiscal Eletrônica) Generator
Usa Jinja2 para renderizar um template HTML e WeasyPrint para converter em PDF.
Faz parse do XML da NF-e (padrão SEFAZ) quando disponível para preencher os campos oficiais.
"""
from __future__ import annotations

import base64
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

MOD_FRETE = {
    "0": "0 - Por conta do Emitente",
    "1": "1 - Por conta do Destinatário",
    "2": "2 - Por conta de Terceiros",
    "3": "3 - Transp. Próprio (Remetente)",
    "4": "4 - Transp. Próprio (Destinatário)",
    "9": "9 - Sem Frete",
}


def _fmt_brl(value: Any) -> str:
    """Formata valor como moeda BRL sem símbolo (padrão DANFE)."""
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        v = 0.0
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_qty(value: Any) -> str:
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        v = 0.0
    return f"{v:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_cnpj(raw: str) -> str:
    if not raw:
        return ""
    s = re.sub(r"\D", "", raw)
    if len(s) == 14:
        return f"{s[:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:]}"
    if len(s) == 11:
        return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"
    return raw


def _fmt_cep(raw: str) -> str:
    if not raw:
        return ""
    s = re.sub(r"\D", "", raw)
    if len(s) == 8:
        return f"{s[:5]}-{s[5:]}"
    return raw


def _fmt_fone(raw: str) -> str:
    if not raw:
        return ""
    s = re.sub(r"\D", "", raw)
    if len(s) == 11:
        return f"({s[:2]}){s[2:7]}-{s[7:]}"
    if len(s) == 10:
        return f"({s[:2]}){s[2:6]}-{s[6:]}"
    return raw


def _fmt_chave(chave: str) -> str:
    if not chave:
        return ""
    s = re.sub(r"\D", "", chave)
    return " ".join(s[i:i + 4] for i in range(0, len(s), 4))


def _fmt_date_br(iso: str) -> str:
    if not iso:
        return ""
    try:
        if "T" in iso:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y")
        # Pode ser YYYY-MM-DD
        dt = datetime.strptime(iso[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return iso


def _fmt_time_br(iso: str) -> str:
    if not iso or "T" not in iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return ""


def _text(el: Optional[ET.Element], path: str, default: str = "") -> str:
    if el is None:
        return default
    # tenta com namespace e sem
    for xpath in (f".//nfe:{p}" for p in path.split("/")):
        pass
    # caminho simples
    parts = path.split("/")
    ns_path = "/".join([f"nfe:{p}" for p in parts])
    try:
        node = el.find(f".//{ns_path}", NFE_NS)
        if node is None:
            node = el.find(f".//{path}")
        if node is not None and node.text:
            return node.text.strip()
    except Exception:
        pass
    return default


def _barcode_png_b64(chave: str) -> Optional[str]:
    """Gera um code128 barcode da chave como PNG base64."""
    if not chave:
        return None
    try:
        import barcode
        from barcode.writer import ImageWriter

        buf = io.BytesIO()
        code = barcode.get("code128", re.sub(r"\D", "", chave), writer=ImageWriter())
        code.write(buf, options={"write_text": False, "quiet_zone": 2, "module_height": 10.0})
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None


def _parse_xml(xml_str: str) -> Dict[str, Any]:
    """Extrai todos os dados relevantes do XML da NF-e para o template."""
    data: Dict[str, Any] = {
        "emit": {},
        "dest": {},
        "transp": {},
        "totais": {},
        "itens": [],
        "duplicatas": [],
        "nfe": {},
    }
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return data

    # proc -> NFe -> infNFe (ou direto)
    inf = root.find(".//nfe:infNFe", NFE_NS) or root.find(".//infNFe")
    prot = root.find(".//nfe:protNFe", NFE_NS) or root.find(".//protNFe")
    inf_prot = None
    if prot is not None:
        inf_prot = prot.find(".//nfe:infProt", NFE_NS) or prot.find(".//infProt")

    # Chave
    chave = ""
    if inf is not None:
        chave = (inf.get("Id") or "").replace("NFe", "")
    data["nfe"]["chave"] = chave

    if inf is None:
        return data

    ide = inf.find("nfe:ide", NFE_NS) or inf.find("ide")
    emit = inf.find("nfe:emit", NFE_NS) or inf.find("emit")
    dest = inf.find("nfe:dest", NFE_NS) or inf.find("dest")
    total = inf.find("nfe:total", NFE_NS) or inf.find("total")
    transp = inf.find("nfe:transp", NFE_NS) or inf.find("transp")
    cobr = inf.find("nfe:cobr", NFE_NS) or inf.find("cobr")
    inf_adic = inf.find("nfe:infAdic", NFE_NS) or inf.find("infAdic")

    # ====== IDE ======
    if ide is not None:
        data["nfe"]["numero_nf"] = _text(ide, "nNF")
        data["nfe"]["serie"] = _text(ide, "serie")
        data["nfe"]["tipo"] = _text(ide, "tpNF", "1")  # 0=entrada, 1=saída
        data["nfe"]["natureza_operacao"] = _text(ide, "natOp")
        data["nfe"]["data_emissao"] = _text(ide, "dhEmi") or _text(ide, "dEmi")
        data["nfe"]["data_saida"] = _text(ide, "dhSaiEnt") or _text(ide, "dSaiEnt")

    # ====== Emitente ======
    if emit is not None:
        ender = emit.find("nfe:enderEmit", NFE_NS) or emit.find("enderEmit")
        data["emit"] = {
            "cnpj": _text(emit, "CNPJ") or _text(emit, "CPF"),
            "razao_social": _text(emit, "xNome"),
            "fantasia": _text(emit, "xFant"),
            "ie": _text(emit, "IE"),
            "iest": _text(emit, "IEST"),
            "im": _text(emit, "IM"),
            "endereco": (
                f"{_text(ender, 'xLgr')}, {_text(ender, 'nro')}"
                + (f" - {_text(ender, 'xCpl')}" if _text(ender, "xCpl") else "")
            ),
            "bairro": _text(ender, "xBairro"),
            "municipio": _text(ender, "xMun"),
            "uf": _text(ender, "UF"),
            "cep": _fmt_cep(_text(ender, "CEP")),
            "fone": _fmt_fone(_text(ender, "fone")),
        }

    # ====== Destinatário ======
    if dest is not None:
        ender = dest.find("nfe:enderDest", NFE_NS) or dest.find("enderDest")
        data["dest"] = {
            "cnpj": _text(dest, "CNPJ") or _text(dest, "CPF"),
            "razao_social": _text(dest, "xNome"),
            "ie": _text(dest, "IE"),
            "endereco": (
                f"{_text(ender, 'xLgr')}, {_text(ender, 'nro')}"
                + (f" - {_text(ender, 'xCpl')}" if _text(ender, "xCpl") else "")
            ) if ender is not None else "",
            "bairro": _text(ender, "xBairro"),
            "municipio": _text(ender, "xMun"),
            "uf": _text(ender, "UF"),
            "cep": _fmt_cep(_text(ender, "CEP")),
            "fone": _fmt_fone(_text(ender, "fone")),
        }

    # ====== Transportador ======
    if transp is not None:
        mod_frete = _text(transp, "modFrete", "9")
        transporta = transp.find("nfe:transporta", NFE_NS) or transp.find("transporta")
        veic = transp.find("nfe:veicTransp", NFE_NS) or transp.find("veicTransp")
        vol = transp.find("nfe:vol", NFE_NS) or transp.find("vol")
        data["transp"] = {
            "mod_frete": mod_frete,
            "mod_frete_desc": MOD_FRETE.get(mod_frete, mod_frete),
            "razao_social": _text(transporta, "xNome") if transporta is not None else "",
            "cnpj": (_text(transporta, "CNPJ") or _text(transporta, "CPF")) if transporta is not None else "",
            "ie": _text(transporta, "IE") if transporta is not None else "",
            "endereco": _text(transporta, "xEnder") if transporta is not None else "",
            "municipio": _text(transporta, "xMun") if transporta is not None else "",
            "uf": _text(transporta, "UF") if transporta is not None else "",
            "placa": _text(veic, "placa") if veic is not None else "",
            "uf_veic": _text(veic, "UF") if veic is not None else "",
            "rntc": _text(veic, "RNTC") if veic is not None else "",
            "q_vol": _text(vol, "qVol") if vol is not None else "",
            "esp": _text(vol, "esp") if vol is not None else "",
            "marca": _text(vol, "marca") if vol is not None else "",
            "n_vol": _text(vol, "nVol") if vol is not None else "",
            "peso_b": _text(vol, "pesoB") if vol is not None else "",
            "peso_l": _text(vol, "pesoL") if vol is not None else "",
        }

    # ====== Totais ======
    icms_tot = None
    if total is not None:
        icms_tot = total.find("nfe:ICMSTot", NFE_NS) or total.find("ICMSTot")
    if icms_tot is not None:
        data["totais"] = {
            "v_bc": _text(icms_tot, "vBC"),
            "v_icms": _text(icms_tot, "vICMS"),
            "v_bc_st": _text(icms_tot, "vBCST"),
            "v_icms_st": _text(icms_tot, "vST"),
            "v_prod": _text(icms_tot, "vProd"),
            "v_frete": _text(icms_tot, "vFrete"),
            "v_seg": _text(icms_tot, "vSeg"),
            "v_desc": _text(icms_tot, "vDesc"),
            "v_outro": _text(icms_tot, "vOutro"),
            "v_ipi": _text(icms_tot, "vIPI"),
            "v_nf": _text(icms_tot, "vNF"),
            "v_trib": _text(icms_tot, "vTotTrib"),
        }

    # ====== Itens (det) ======
    for det in inf.findall("nfe:det", NFE_NS) or inf.findall("det"):
        prod = det.find("nfe:prod", NFE_NS) or det.find("prod")
        imposto = det.find("nfe:imposto", NFE_NS) or det.find("imposto")
        if prod is None:
            continue

        # ICMS (pode estar em várias subtags)
        cst = ""
        v_bc = v_icms = p_icms = "0"
        if imposto is not None:
            icms_block = imposto.find("nfe:ICMS", NFE_NS) or imposto.find("ICMS")
            if icms_block is not None:
                for child in list(icms_block):
                    # primeiro filho define o tipo (ICMS00, ICMS10, etc.)
                    cst = _text(child, "CST") or _text(child, "CSOSN") or ""
                    v_bc = _text(child, "vBC", "0")
                    v_icms = _text(child, "vICMS", "0")
                    p_icms = _text(child, "pICMS", "0")
                    break

            ipi_block = imposto.find("nfe:IPI", NFE_NS) or imposto.find("IPI")
            v_ipi = "0"
            p_ipi = "0"
            if ipi_block is not None:
                for child in list(ipi_block):
                    v_ipi = _text(child, "vIPI", "0")
                    p_ipi = _text(child, "pIPI", "0")
        else:
            v_ipi = "0"
            p_ipi = "0"

        data["itens"].append({
            "codigo": _text(prod, "cProd"),
            "descricao": _text(prod, "xProd"),
            "ncm": _text(prod, "NCM"),
            "cst": cst,
            "cfop": _text(prod, "CFOP"),
            "unidade": _text(prod, "uCom"),
            "quantidade": _fmt_qty(_text(prod, "qCom", "0")),
            "valor_unitario": _fmt_brl(_text(prod, "vUnCom", "0")),
            "valor_total": _fmt_brl(_text(prod, "vProd", "0")),
            "v_bc": _fmt_brl(v_bc),
            "v_icms": _fmt_brl(v_icms),
            "v_ipi": _fmt_brl(v_ipi),
            "p_icms": _fmt_brl(p_icms),
            "p_ipi": _fmt_brl(p_ipi),
        })

    # ====== Duplicatas ======
    if cobr is not None:
        for dup in cobr.findall("nfe:dup", NFE_NS) or cobr.findall("dup"):
            data["duplicatas"].append({
                "numero": _text(dup, "nDup"),
                "vencimento": _fmt_date_br(_text(dup, "dVenc")),
                "valor": _fmt_brl(_text(dup, "vDup", "0")),
            })

    # ====== Informações Adicionais ======
    if inf_adic is not None:
        data["nfe"]["inf_cpl"] = _text(inf_adic, "infCpl")
        data["nfe"]["inf_ad_fisco"] = _text(inf_adic, "infAdFisco")

    # ====== Protocolo ======
    if inf_prot is not None:
        data["nfe"]["protocolo"] = _text(inf_prot, "nProt")
        data["nfe"]["data_autorizacao"] = _fmt_date_br(_text(inf_prot, "dhRecbto"))

    return data


def _merge_db_fallback(parsed: Dict[str, Any], nfe_db: Dict[str, Any]) -> Dict[str, Any]:
    """Completa dados ausentes do XML com os dados salvos no MongoDB."""
    parsed.setdefault("nfe", {})
    parsed.setdefault("emit", {})
    parsed.setdefault("dest", {})
    parsed.setdefault("transp", {})
    parsed.setdefault("totais", {})
    parsed.setdefault("itens", [])
    parsed.setdefault("duplicatas", [])

    if not parsed["nfe"].get("numero_nf"):
        parsed["nfe"]["numero_nf"] = str(nfe_db.get("numero_nf", ""))
    if not parsed["nfe"].get("serie"):
        parsed["nfe"]["serie"] = str(nfe_db.get("serie", "1"))
    if not parsed["nfe"].get("chave"):
        parsed["nfe"]["chave"] = nfe_db.get("chave_acesso", "")
    if not parsed["nfe"].get("data_emissao"):
        parsed["nfe"]["data_emissao"] = nfe_db.get("data_emissao", "")

    if not parsed["emit"].get("razao_social"):
        parsed["emit"]["razao_social"] = nfe_db.get("razao_social_emitente", "")
    if not parsed["emit"].get("cnpj"):
        parsed["emit"]["cnpj"] = nfe_db.get("cnpj_emitente", "")

    if not parsed["dest"].get("cnpj"):
        parsed["dest"]["cnpj"] = nfe_db.get("cnpj_destinatario", "")

    # Fallback itens
    if not parsed["itens"] and nfe_db.get("itens"):
        for it in nfe_db["itens"]:
            parsed["itens"].append({
                "codigo": it.get("codigo", ""),
                "descricao": it.get("descricao", ""),
                "ncm": it.get("ncm", ""),
                "cst": "",
                "cfop": it.get("cfop", ""),
                "unidade": it.get("unidade", ""),
                "quantidade": _fmt_qty(it.get("quantidade", 0)),
                "valor_unitario": _fmt_brl(it.get("valor_unitario", 0)),
                "valor_total": _fmt_brl(it.get("valor_total", 0)),
                "v_bc": _fmt_brl(0),
                "v_icms": _fmt_brl(0),
                "v_ipi": _fmt_brl(0),
                "p_icms": _fmt_brl(0),
                "p_ipi": _fmt_brl(0),
            })

    # Fallback totais
    if not parsed["totais"].get("v_nf"):
        parsed["totais"]["v_nf"] = nfe_db.get("valor_total", 0)
    return parsed


def _apply_formatting(data: Dict[str, Any]) -> Dict[str, Any]:
    """Aplica formatações finais antes de renderizar (datas, valores, números)."""
    nfe = data.setdefault("nfe", {})
    nfe["numero_nf_fmt"] = str(nfe.get("numero_nf", "")).zfill(9)
    try:
        numero_int = int(re.sub(r"\D", "", str(nfe.get("numero_nf", "")) or "0"))
        nfe["numero_nf_fmt"] = f"{numero_int:09d}"
        nfe["numero_nf_fmt"] = f"{nfe['numero_nf_fmt'][:3]}.{nfe['numero_nf_fmt'][3:6]}.{nfe['numero_nf_fmt'][6:]}"
    except Exception:
        pass

    try:
        serie_int = int(re.sub(r"\D", "", str(nfe.get("serie", "")) or "0"))
        nfe["serie_fmt"] = f"{serie_int:03d}"
    except Exception:
        nfe["serie_fmt"] = str(nfe.get("serie", "1"))

    nfe["chave_formatada"] = _fmt_chave(nfe.get("chave", ""))
    nfe["data_emissao_fmt"] = _fmt_date_br(nfe.get("data_emissao", ""))
    nfe["data_saida_fmt"] = _fmt_date_br(nfe.get("data_saida", ""))
    nfe["hora_saida"] = _fmt_time_br(nfe.get("data_saida", "")) or _fmt_time_br(nfe.get("data_emissao", ""))

    # Formata cnpj
    data["emit"]["cnpj_fmt"] = _fmt_cnpj(data["emit"].get("cnpj", ""))
    data["dest"]["cnpj_fmt"] = _fmt_cnpj(data["dest"].get("cnpj", ""))
    data["transp"]["cnpj_fmt"] = _fmt_cnpj(data["transp"].get("cnpj", ""))

    # Totais: garantir todas as chaves formatadas
    tot_keys = ["v_bc", "v_icms", "v_bc_st", "v_icms_st", "v_prod", "v_frete",
                "v_seg", "v_desc", "v_outro", "v_ipi", "v_nf", "v_trib"]
    for k in tot_keys:
        data["totais"][k] = _fmt_brl(data["totais"].get(k, 0))

    return data


def render_danfe_pdf(nfe_db: Dict[str, Any]) -> bytes:
    """
    Gera o PDF do DANFE no layout oficial a partir de um documento da coleção
    nfe_importadas. Tenta extrair dados detalhados do XML (se presente) e
    completa com dados do MongoDB.
    """
    xml_str = ""
    xml_b64 = nfe_db.get("xml_base64")
    if xml_b64:
        try:
            xml_bytes = base64.b64decode(xml_b64)
            xml_str = xml_bytes.decode("utf-8", errors="ignore")
        except Exception:
            xml_str = ""

    data = _parse_xml(xml_str) if xml_str else {
        "emit": {}, "dest": {}, "transp": {}, "totais": {},
        "itens": [], "duplicatas": [], "nfe": {},
    }
    data = _merge_db_fallback(data, nfe_db)
    data = _apply_formatting(data)

    context = {
        "emit": data["emit"],
        "dest": data["dest"],
        "transp": data["transp"],
        "totais": data["totais"],
        "itens": data["itens"],
        "duplicatas": data["duplicatas"],
        "nfe": data["nfe"],
        "barcode_b64": _barcode_png_b64(data["nfe"].get("chave", "")),
        "folha": 1,
        "total_folhas": 1,
        "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    template = _env.get_template("danfe.html")
    html_str = template.render(**context)

    # Importação local para evitar custo em import-time do módulo
    from weasyprint import HTML

    buf = io.BytesIO()
    HTML(string=html_str, base_url=str(TEMPLATES_DIR)).write_pdf(buf)
    return buf.getvalue()
