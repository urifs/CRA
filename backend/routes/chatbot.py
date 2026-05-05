"""
Chatbot Routes - AI Assistant for the platform
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from datetime import datetime, timedelta
import os
import io
import base64
import logging
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
import jwt
JWT_SECRET = os.environ.get('JWT_SECRET', 'fleet-maintenance-secret-key-2024')

security = HTTPBearer()

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = decode_token(credentials.credentials)
    # Normaliza: token usa "user_id"; alguns trechos esperam "id"
    if "id" not in payload and "user_id" in payload:
        payload["id"] = payload["user_id"]
    return payload

# Create router
chatbot_router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


# Models
class ChatMessage(BaseModel):
    message: str
    module: str = "gerenciamento"


class ChatResponse(BaseModel):
    response: str
    context_used: List[str] = []


async def get_full_platform_context() -> str:
    """Coleta TODAS as informações de TODAS as coleções do banco de dados.
    Inclui agregações úteis para Ponto (faltas/atrasos), Folha, NF-e, OS, etc."""
    from collections import defaultdict
    context_parts = []
    hoje = datetime.now()
    inicio_30 = (hoje - timedelta(days=30)).strftime("%Y-%m-%d")
    inicio_60 = (hoje - timedelta(days=60)).strftime("%Y-%m-%d")
    mes_passado_dt = hoje.replace(day=1) - timedelta(days=1)
    mes_passado_inicio = mes_passado_dt.replace(day=1).strftime("%Y-%m-%d")
    mes_passado_fim = mes_passado_dt.strftime("%Y-%m-%d")

    context_parts.append("=" * 60)
    context_parts.append(f"BANCO DE DADOS COMPLETO - CRA CONSTRUTORA  |  Hoje: {hoje.strftime('%d/%m/%Y')}")
    context_parts.append("=" * 60)

    # ============ USUÁRIOS ============
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nUSUÁRIOS ({len(users)})\n{'='*40}")
    for u in users:
        context_parts.append(f"- {u.get('name')} | {u.get('email')} | role={u.get('role','gerenciamento')}")

    # ============ MÁQUINAS / FROTA ============
    categories = await db.categories.find({}, {"_id": 0}).to_list(200)
    machines = await db.machines.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nFROTA ({len(machines)} máquinas, {len(categories)} categorias)\n{'='*40}")
    for m in machines:
        context_parts.append(
            f"- {m.get('name')} | placa={m.get('plate','-')} | marca={m.get('brand','-')} | status={m.get('status','-')}"
        )

    # ============ MANUTENÇÕES ============
    maintenances = await db.maintenances.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    total_valor_manut = sum(m.get('part_value', 0) for m in maintenances)
    context_parts.append(f"\n\n{'='*40}\nMANUTENÇÕES ({len(maintenances)})\n{'='*40}")
    context_parts.append(f"TOTAL GASTO: R$ {total_valor_manut:,.2f}")
    for m in maintenances[:30]:
        context_parts.append(
            f"- {m.get('part_name','-')} | R$ {m.get('part_value',0):,.2f} | data={m.get('replacement_date','-')} | máquina={m.get('machine_id','-')}"
        )

    # ============ ESTOQUE ============
    stock_items = await db.stock_items.find({}, {"_id": 0}).to_list(500)
    low_stock = [i for i in stock_items if i.get("quantity", 0) <= i.get("min_quantity", 0)]
    context_parts.append(f"\n\n{'='*40}\nESTOQUE ({len(stock_items)} itens, {len(low_stock)} em alerta)\n{'='*40}")
    for i in stock_items:
        context_parts.append(f"- {i.get('name')} | qtd={i.get('quantity',0)} | min={i.get('min_quantity',0)}")

    # ============ OBRAS ============
    obras = await db.obras.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nOBRAS ({len(obras)})\n{'='*40}")
    for o in obras:
        context_parts.append(f"- {o.get('name','-')} | {o.get('location','-')} | status={o.get('status','-')}")

    # ============ CADASTROS (clientes/fornecedores) ============
    cadastros = await db.cadastros.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCADASTROS ({len(cadastros)})\n{'='*40}")
    for c in cadastros[:80]:
        context_parts.append(f"- {c.get('tipo_cadastro','-')}: {c.get('nome_razao','-')} | CNPJ/CPF={c.get('cnpj_cpf','-')}")

    # ============ FINANCEIRO ============
    contas_pagar = await db.contas_pagar.find({}, {"_id": 0}).to_list(2000)
    contas_receber = await db.contas_receber.find({}, {"_id": 0}).to_list(2000)
    pagar_aberto = [c for c in contas_pagar if c.get("status") in ("em_aberto", "pendente", "parcial")]
    receber_aberto = [c for c in contas_receber if c.get("status") in ("em_aberto", "pendente", "parcial")]
    pagar_vencidas = [c for c in pagar_aberto if (c.get("data_vencimento") or "9999") < hoje.strftime("%Y-%m-%d")]
    receber_vencidas = [c for c in receber_aberto if (c.get("data_vencimento") or "9999") < hoje.strftime("%Y-%m-%d")]
    context_parts.append(f"\n\n{'='*40}\nCONTAS A PAGAR ({len(contas_pagar)})\n{'='*40}")
    context_parts.append(f"EM ABERTO: {len(pagar_aberto)} | VENCIDAS: {len(pagar_vencidas)}")
    context_parts.append(f"TOTAL EM ABERTO: R$ {sum(c.get('valor',0) for c in pagar_aberto):,.2f}")
    for c in pagar_aberto[:40]:
        context_parts.append(
            f"- {c.get('descricao','-')[:50]} | R$ {c.get('valor',0):,.2f} | venc={c.get('data_vencimento','-')} | forma={c.get('forma_pagamento','-')} | fornecedor={c.get('cadastro_nome','-')}"
        )
    context_parts.append(f"\n\n{'='*40}\nCONTAS A RECEBER ({len(contas_receber)})\n{'='*40}")
    context_parts.append(f"EM ABERTO: {len(receber_aberto)} | VENCIDAS: {len(receber_vencidas)}")
    context_parts.append(f"TOTAL EM ABERTO: R$ {sum(c.get('valor',0) for c in receber_aberto):,.2f}")
    for c in receber_aberto[:40]:
        context_parts.append(
            f"- {c.get('descricao','-')[:50]} | R$ {c.get('valor',0):,.2f} | venc={c.get('data_vencimento','-')} | cliente={c.get('cadastro_nome','-')}"
        )

    # ============ ORDENS DE SERVIÇO ============
    ordens_servico = await db.ordens_servico.find({}, {"_id": 0}).sort("data_emissao", -1).to_list(200)
    context_parts.append(f"\n\n{'='*40}\nORDENS DE SERVIÇO ({len(ordens_servico)})\n{'='*40}")
    for os_ in ordens_servico[:30]:
        context_parts.append(
            f"- OS #{os_.get('numero','?')} | {os_.get('cliente_nome','-')} | R$ {os_.get('valor_total',0):,.2f} | status={os_.get('status','-')} | emissão={os_.get('data_emissao','-')}"
        )

    # ============ ALUGUEIS ============
    alugueis = await db.alugueis.find({}, {"_id": 0}).to_list(200)
    context_parts.append(f"\n\n{'='*40}\nALUGUEIS ({len(alugueis)})\n{'='*40}")
    for a in alugueis[:30]:
        context_parts.append(
            f"- {a.get('descricao','-')[:50]} | R$ {a.get('valor_mensal',0):,.2f}/mês | início={a.get('data_inicio','-')} | status={a.get('status','-')}"
        )

    # ============ NF-e e NFS-e IMPORTADAS ============
    nfes = await db.nfes_importadas.find({}, {"_id": 0}).sort("data_emissao", -1).to_list(50)
    nfses = await db.nfse_importadas.find({}, {"_id": 0}).sort("data_emissao", -1).to_list(50)
    context_parts.append(f"\n\n{'='*40}\nNF-e ({len(nfes)} amostra) / NFS-e ({len(nfses)} amostra)\n{'='*40}")
    for nf in nfes[:15]:
        context_parts.append(
            f"- NF-e #{nf.get('numero_nota','?')} | {nf.get('razao_social_emitente','-')} | R$ {nf.get('valor_total',0):,.2f} | {nf.get('data_emissao','-')}"
        )
    for nf in nfses[:15]:
        context_parts.append(
            f"- NFS-e #{nf.get('numero_nota','?')} | {nf.get('razao_social_emitente','-')} | R$ {nf.get('valor_total',0):,.2f} | {nf.get('data_emissao','-')}"
        )

    # ============ FUNCIONÁRIOS RH ============
    funcionarios = await db.funcionarios.find({}, {"_id": 0}).to_list(500)
    func_id_to_nome = {f.get("id"): f.get("nome") for f in funcionarios}
    ativos = [f for f in funcionarios if (f.get("status") or "").lower() == "ativo"]
    context_parts.append(f"\n\n{'='*40}\nFUNCIONÁRIOS RH ({len(funcionarios)} total, {len(ativos)} ativos)\n{'='*40}")
    for f in funcionarios:
        context_parts.append(
            f"- ID:{f.get('id','-')} | {f.get('nome','-')} | {f.get('cargo','-')} | R$ {f.get('salario',0):,.2f} | status={f.get('status','-')}"
        )

    # ============ PONTO ELETRÔNICO — agregações por funcionário ============
    ponto_30 = await db.ponto_registros.find(
        {"data": {"$gte": inicio_30, "$lte": hoje.strftime("%Y-%m-%d")}}, {"_id": 0}
    ).to_list(5000)
    ponto_mes_passado = await db.ponto_registros.find(
        {"data": {"$gte": mes_passado_inicio, "$lte": mes_passado_fim}}, {"_id": 0}
    ).to_list(5000)
    ponto_60 = await db.ponto_registros.find(
        {"data": {"$gte": inicio_60, "$lte": hoje.strftime("%Y-%m-%d")}}, {"_id": 0}
    ).to_list(8000)
    context_parts.append(
        f"\n\n{'='*40}\nPONTO ELETRÔNICO (últ. 30 dias: {len(ponto_30)} regs / 60 dias: {len(ponto_60)})\n{'='*40}"
    )
    context_parts.append(
        f"Período mês passado considerado: {mes_passado_inicio} a {mes_passado_fim}"
    )

    def _agregar(registros, label):
        faltas = defaultdict(int)
        atrasos = defaultdict(int)
        abonados = defaultdict(int)
        trabalhados = defaultdict(int)
        for r in registros:
            fid = r.get("funcionario_id")
            if not fid:
                continue
            status_dia = (r.get("status_dia") or "").lower()
            if r.get("abono") or status_dia == "abonado":
                abonados[fid] += 1
            elif status_dia in ("sem_registro", "faltou", "ausente"):
                faltas[fid] += 1
            elif status_dia in ("atrasado", "atraso"):
                atrasos[fid] += 1
                trabalhados[fid] += 1
            elif r.get("batidas"):
                trabalhados[fid] += 1
        if faltas or atrasos or abonados:
            context_parts.append(f"\n>>> RESUMO {label}:")
            top_faltas = sorted(faltas.items(), key=lambda x: -x[1])[:10]
            for fid, qtd in top_faltas:
                context_parts.append(
                    f"- {func_id_to_nome.get(fid,'?')} → {qtd} falta(s) | {atrasos.get(fid,0)} atraso(s) | {abonados.get(fid,0)} abono(s) | {trabalhados.get(fid,0)} dia(s) trabalhado(s)"
                )
            if not top_faltas:
                # Se ninguém tem faltas, ainda mostre quem mais trabalhou
                top_t = sorted(trabalhados.items(), key=lambda x: -x[1])[:5]
                for fid, qtd in top_t:
                    context_parts.append(f"- {func_id_to_nome.get(fid,'?')} → {qtd} dia(s) trabalhado(s) | {atrasos.get(fid,0)} atraso(s)")
        else:
            context_parts.append(f"(nenhuma falta/atraso/abono registrado em {label})")

    _agregar(ponto_mes_passado, "MÊS PASSADO")
    _agregar(ponto_30, "ÚLTIMOS 30 DIAS")

    # ============ FOLHA DE PAGAMENTO ============
    folhas = await db.folha_pagamento.find({}, {"_id": 0}).sort("competencia", -1).to_list(200)
    context_parts.append(f"\n\n{'='*40}\nFOLHA DE PAGAMENTO ({len(folhas)})\n{'='*40}")
    by_comp = defaultdict(list)
    for fp in folhas:
        by_comp[fp.get("competencia", "?")].append(fp)
    for comp in list(sorted(by_comp.keys(), reverse=True))[:6]:
        items = by_comp[comp]
        total_liq = sum(i.get("liquido", 0) for i in items)
        context_parts.append(
            f"- Competência {comp}: {len(items)} funcionário(s) | total líquido R$ {total_liq:,.2f}"
        )

    # ============ FÉRIAS ============
    ferias = await db.ferias.find({}, {"_id": 0}).to_list(200)
    context_parts.append(f"\n\n{'='*40}\nFÉRIAS ({len(ferias)})\n{'='*40}")
    for fe in ferias[:20]:
        context_parts.append(
            f"- {func_id_to_nome.get(fe.get('funcionario_id'), '?')} | {fe.get('data_inicio','-')} → {fe.get('data_fim','-')} | status={fe.get('status','-')}"
        )

    # ============ EPI ============
    epi = await db.epi_fichas.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nEPI ({len(epi)} fichas)\n{'='*40}")
    for e in epi[:20]:
        context_parts.append(
            f"- {func_id_to_nome.get(e.get('funcionario_id'), '?')} | EPI={e.get('item','-')} | entrega={e.get('data_entrega','-')}"
        )

    # ============ JORNADAS ============
    jornadas = await db.jornadas.find({}, {"_id": 0}).to_list(50)
    context_parts.append(f"\n\n{'='*40}\nJORNADAS DE TRABALHO ({len(jornadas)})\n{'='*40}")
    for j in jornadas:
        context_parts.append(f"- {j.get('nome','-')} | padrão={j.get('is_padrao',False)}")

    # ============ NOTIFICAÇÕES RH ============
    notifs = await db.rh_notificacoes.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    context_parts.append(f"\n\n{'='*40}\nNOTIFICAÇÕES RH ({len(notifs)})\n{'='*40}")
    for n in notifs[:20]:
        context_parts.append(
            f"- [{n.get('tipo','info')}] {n.get('titulo','-')} → {n.get('funcionario_nome','-')} | lida={n.get('lida',False)}"
        )

    # ============ CONTAS BANCÁRIAS / FORMAS / PLANO ============
    contas_bancarias = await db.contas_bancarias.find({}, {"_id": 0}).to_list(50)
    formas_pag = await db.formas_pagamento.find({}, {"_id": 0}).to_list(50)
    plano_contas = await db.plano_contas.find({}, {"_id": 0}).to_list(200)
    centros = await db.centros_custo.find({}, {"_id": 0}).to_list(50)
    context_parts.append(f"\n\n{'='*40}\nCONTAS BANCÁRIAS ({len(contas_bancarias)})\n{'='*40}")
    for cb in contas_bancarias:
        context_parts.append(f"- {cb.get('nome','-')} | banco={cb.get('banco','-')} | saldo R$ {cb.get('saldo_atual',0):,.2f}")
    context_parts.append(f"\nFORMAS DE PAGAMENTO: {', '.join(f.get('nome','-') for f in formas_pag) or '(nenhuma)'}")
    context_parts.append(f"\nCENTROS DE CUSTO ({len(centros)}): {', '.join(c.get('nome','-') for c in centros) or '(nenhum)'}")
    context_parts.append(f"\nPLANO DE CONTAS: {len(plano_contas)} contas cadastradas")

    return "\n".join(context_parts)


@chatbot_router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(chat_message: ChatMessage, current_user: dict = Depends(get_current_user)):
    """Chat com o assistente de IA"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        platform_context = await get_full_platform_context()
        
        system_message = f"""Você é o assistente virtual inteligente da CRA Construtora.
Você tem ACESSO COMPLETO a TODAS as informações do banco de dados.

DADOS DO SISTEMA:
{platform_context}

INSTRUÇÕES:
1. SEMPRE responda em português brasileiro
2. Use quebras de linha para separar parágrafos
3. Use listas com "•" para enumerar itens
4. Formate valores monetários como R$ 1.234,56
5. NÃO use markdown com asteriscos
6. Seja útil e forneça dados específicos quando perguntado
"""
        
        llm_key = os.environ.get("EMERGENT_LLM_KEY")
        
        llm_chat = LlmChat(
            api_key=llm_key,
            session_id=f"chatbot-{current_user['id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message=system_message
        ).with_model("gemini", "gemini-2.5-flash")
        
        user_message = UserMessage(text=chat_message.message)
        response = await llm_chat.send_message(user_message)
        
        return ChatResponse(
            response=response,
            context_used=[chat_message.module, "database"]
        )
        
    except Exception as e:
        logging.error(f"Erro no chatbot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no assistente: {str(e)}")


@chatbot_router.post("/chat-with-files", response_model=ChatResponse)
async def chat_with_files(
    message: str = Form(default=""),
    files: List[UploadFile] = File(default=[]),
    current_user: dict = Depends(get_current_user)
):
    """Chat com arquivos anexados"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        files_info = []
        file_contents = []
        
        for file in files:
            content = await file.read()
            file_size = len(content)
            filename = file.filename or "arquivo"
            content_type = file.content_type
            
            files_info.append({
                "nome": filename,
                "tipo": content_type,
                "tamanho": f"{file_size / 1024:.1f} KB"
            })
            
            extracted_content = ""
            
            # Arquivos de texto
            if content_type and content_type.startswith('text/'):
                try:
                    text = content.decode('utf-8', errors='ignore')
                    extracted_content = f"📄 CONTEÚDO DE {filename}:\n{text[:10000]}"
                except:
                    extracted_content = f"📄 Arquivo {filename}: não foi possível extrair texto"
            
            # PDFs
            elif content_type == 'application/pdf' or filename.lower().endswith('.pdf'):
                try:
                    from PyPDF2 import PdfReader
                    pdf_reader = PdfReader(io.BytesIO(content))
                    pdf_text = ""
                    for page in pdf_reader.pages[:10]:
                        pdf_text += page.extract_text() + "\n"
                    if pdf_text.strip():
                        extracted_content = f"📑 CONTEÚDO DO PDF {filename}:{pdf_text[:8000]}"
                    else:
                        extracted_content = f"📑 PDF {filename}: {len(pdf_reader.pages)} páginas"
                except Exception as pdf_err:
                    extracted_content = f"⚠️ PDF {filename}: erro ao extrair ({str(pdf_err)[:100]})"
            
            # Excel
            elif filename.lower().endswith(('.xlsx', '.xls')):
                try:
                    import pandas as pd
                    df = pd.read_excel(io.BytesIO(content))
                    preview = df.head(20).to_string()
                    extracted_content = f"📊 PLANILHA {filename}:\nColunas: {list(df.columns)}\nLinhas: {len(df)}\n\nPrimeiras linhas:\n{preview}"
                except Exception as xl_err:
                    extracted_content = f"⚠️ Planilha {filename}: erro ({str(xl_err)[:100]})"
            
            # Imagens
            elif content_type and content_type.startswith('image/'):
                try:
                    from PIL import Image
                    img = Image.open(io.BytesIO(content))
                    extracted_content = f"🖼️ IMAGEM {filename}: {img.format}, {img.width}x{img.height} pixels"
                except:
                    extracted_content = f"🖼️ Imagem {filename}: {file_size / 1024:.1f} KB"
            
            else:
                extracted_content = f"📁 Arquivo {filename}: {content_type or 'desconhecido'} ({file_size / 1024:.1f} KB)"
            
            if extracted_content:
                file_contents.append(extracted_content)
            
            await file.seek(0)
        
        files_context = ""
        if files_info:
            files_context = "\n\nARQUIVOS ANEXADOS:\n"
            for info in files_info:
                files_context += f"• {info['nome']} ({info['tipo']}, {info['tamanho']})\n"
            if file_contents:
                files_context += "\n" + "\n\n".join(file_contents)
        
        platform_context = await get_full_platform_context()
        
        system_message = f"""Você é o assistente virtual da CRA Construtora.

DADOS DO SISTEMA:
{platform_context}

{files_context}

INSTRUÇÕES:
1. SEMPRE responda em português brasileiro
2. Analise os arquivos anexados e faça comentários úteis
3. Relacione os dados dos arquivos com os dados da plataforma
4. NÃO use markdown com asteriscos
"""
        
        llm_key = os.environ.get("EMERGENT_LLM_KEY")
        
        llm_chat = LlmChat(
            api_key=llm_key,
            session_id=f"chatbot-files-{current_user['id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message=system_message
        ).with_model("gemini", "gemini-2.5-flash")
        
        user_text = message if message else "Analise os arquivos que anexei"
        if files_info:
            user_text += f"\n\n[Arquivos: {', '.join([f['nome'] for f in files_info])}]"
        
        user_message = UserMessage(text=user_text)
        response = await llm_chat.send_message(user_message)
        
        return ChatResponse(
            response=response,
            context_used=["arquivos", "todos_os_modulos"]
        )
        
    except Exception as e:
        logging.error(f"Erro no chatbot com arquivos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivos: {str(e)}")



# ============================================================
# Conversas persistentes (estilo ChatGPT) — usadas pela tela principal do RH
# ============================================================
import uuid
from datetime import timezone


class ConversationCreate(BaseModel):
    title: Optional[str] = "Nova conversa"
    module: str = "rh"


class ConversationOut(BaseModel):
    id: str
    title: str
    module: str
    created_at: str
    updated_at: str
    last_message_preview: Optional[str] = None


class MessageIn(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: str
    role: str  # "user" | "assistant"
    content: str
    created_at: str
    artifact: Optional[dict] = None  # {download_url, label, type} quando IA gera arquivo


@chatbot_router.get("/conversations", response_model=List[ConversationOut])
async def list_conversations(
    module: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Lista conversas do usuário autenticado, ordenadas por última atualização (mais recentes primeiro)."""
    query = {"user_id": current_user["id"]}
    if module:
        query["module"] = module
    convs = await db.chat_conversations.find(query, {"_id": 0}).sort("updated_at", -1).to_list(200)
    return [ConversationOut(**c) for c in convs]


@chatbot_router.post("/conversations", response_model=ConversationOut)
async def create_conversation(
    payload: ConversationCreate,
    current_user: dict = Depends(get_current_user),
):
    now_iso = datetime.now(timezone.utc).isoformat()
    conv = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "title": payload.title or "Nova conversa",
        "module": payload.module,
        "created_at": now_iso,
        "updated_at": now_iso,
        "last_message_preview": None,
    }
    await db.chat_conversations.insert_one(dict(conv))
    return ConversationOut(**{k: v for k, v in conv.items() if k != "user_id"})


@chatbot_router.get("/conversations/{conv_id}/messages", response_model=List[MessageOut])
async def list_messages(conv_id: str, current_user: dict = Depends(get_current_user)):
    conv = await db.chat_conversations.find_one(
        {"id": conv_id, "user_id": current_user["id"]}, {"_id": 0}
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    msgs = await db.chat_messages.find(
        {"conversation_id": conv_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(2000)
    return [MessageOut(**m) for m in msgs]


@chatbot_router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, current_user: dict = Depends(get_current_user)):
    conv = await db.chat_conversations.find_one({"id": conv_id, "user_id": current_user["id"]})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    await db.chat_messages.delete_many({"conversation_id": conv_id})
    await db.chat_conversations.delete_one({"id": conv_id})
    return {"deleted": True}


# ============ Execução de ferramentas (tool calling) ============

async def _execute_chat_tool(action: str, params: dict, current_user: dict):
    """Executa a ação solicitada pela IA. Retorna (artifact_dict|None, result_text)."""

    if action == "criar_notificacao":
        funcionario_id = params.get("funcionario_id")
        titulo = (params.get("titulo") or "").strip()
        mensagem = (params.get("mensagem") or "").strip()
        tipo = (params.get("tipo") or "info").strip()
        if not funcionario_id or not titulo or not mensagem:
            raise ValueError("Parâmetros obrigatórios: funcionario_id, titulo, mensagem")
        func = await db.funcionarios.find_one({"id": funcionario_id}, {"_id": 0})
        if not func:
            raise ValueError(f"Funcionário {funcionario_id} não encontrado")
        notif_id = str(uuid.uuid4())
        notif_doc = {
            "id": notif_id,
            "tipo": tipo if tipo in ("info", "alerta", "urgente") else "info",
            "titulo": titulo,
            "mensagem": mensagem,
            "categoria": "rh",
            "funcionario_id": funcionario_id,
            "funcionario_nome": func.get("nome"),
            "lida": False,
            "criada_por_ia": True,
            "criada_por_user_id": current_user.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.rh_notificacoes.insert_one(dict(notif_doc))
        result_text = (
            f"✅ Notificação criada com sucesso para {func.get('nome')}.\n"
            f"• Título: {titulo}\n"
            f"• Tipo: {tipo}\n"
            f"• ID: {notif_id}"
        )
        return None, result_text

    if action == "gerar_pdf_funcionario":
        funcionario_id = params.get("funcionario_id")
        if not funcionario_id:
            raise ValueError("funcionario_id é obrigatório")
        func = await db.funcionarios.find_one({"id": funcionario_id}, {"_id": 0})
        if not func:
            raise ValueError(f"Funcionário {funcionario_id} não encontrado")
        pdf_bytes = _gerar_pdf_funcionario(func)
        # Persistir o PDF como artefato baixável (rota dedicada abaixo)
        artifact_id = str(uuid.uuid4())
        await db.chat_artifacts.insert_one({
            "id": artifact_id,
            "user_id": current_user.get("id"),
            "filename": f"funcionario_{(func.get('nome') or 'desconhecido').replace(' ', '_')}.pdf",
            "content_type": "application/pdf",
            "content_b64": base64.b64encode(pdf_bytes).decode("ascii"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        artifact = {
            "type": "pdf",
            "label": f"Baixar PDF de {func.get('nome')}",
            "download_url": f"/api/chatbot/artifacts/{artifact_id}",
        }
        return artifact, f"📄 PDF gerado para {func.get('nome')}. Clique em 'Baixar' abaixo."

    if action == "gerar_pdf_lista_funcionarios":
        funcionarios = await db.funcionarios.find({}, {"_id": 0}).to_list(500)
        pdf_bytes = _gerar_pdf_lista_funcionarios(funcionarios)
        artifact_id = str(uuid.uuid4())
        await db.chat_artifacts.insert_one({
            "id": artifact_id,
            "user_id": current_user.get("id"),
            "filename": "lista_funcionarios.pdf",
            "content_type": "application/pdf",
            "content_b64": base64.b64encode(pdf_bytes).decode("ascii"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        artifact = {
            "type": "pdf",
            "label": f"Baixar lista ({len(funcionarios)} funcionários)",
            "download_url": f"/api/chatbot/artifacts/{artifact_id}",
        }
        return artifact, f"📄 Lista de funcionários gerada ({len(funcionarios)} registros)."

    raise ValueError(f"Ação desconhecida: {action}")


def _gerar_pdf_funcionario(func: dict) -> bytes:
    """Gera PDF simples com dados do funcionário usando reportlab."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, "Ficha do Funcionário")
    y -= 1 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Gerado pelo Assistente IA · {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 1 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, f"Nome: {func.get('nome', '-')}")
    y -= 0.7 * cm
    c.setFont("Helvetica", 11)
    campos = [
        ("CPF", func.get("cpf")),
        ("Cargo", func.get("cargo")),
        ("Departamento", func.get("departamento")),
        ("Data de Admissão", func.get("data_admissao")),
        ("Salário", f"R$ {(func.get('salario') or 0):,.2f}"),
        ("Tipo Contrato", func.get("tipo_contrato")),
        ("Telefone", func.get("telefone")),
        ("Email", func.get("email")),
        ("Status", func.get("status")),
    ]
    for k, v in campos:
        if v in (None, ""):
            continue
        c.drawString(2 * cm, y, f"{k}: {v}")
        y -= 0.6 * cm
        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm
    c.showPage()
    c.save()
    return buf.getvalue()


def _gerar_pdf_lista_funcionarios(funcionarios: list) -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, f"Lista de Funcionários ({len(funcionarios)})")
    y -= 0.8 * cm
    c.setFont("Helvetica", 9)
    c.drawString(2 * cm, y, f"Gerado pelo Assistente IA · {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 1 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Nome")
    c.drawString(9 * cm, y, "Cargo")
    c.drawString(14 * cm, y, "Salário")
    y -= 0.4 * cm
    c.line(2 * cm, y, width - 2 * cm, y)
    y -= 0.5 * cm
    c.setFont("Helvetica", 9)
    for f in funcionarios:
        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm
        c.drawString(2 * cm, y, (f.get("nome") or "")[:42])
        c.drawString(9 * cm, y, (f.get("cargo") or "")[:28])
        c.drawString(14 * cm, y, f"R$ {(f.get('salario') or 0):,.2f}")
        y -= 0.5 * cm
    c.showPage()
    c.save()
    return buf.getvalue()


@chatbot_router.get("/artifacts/{artifact_id}")
async def download_chat_artifact(artifact_id: str, current_user: dict = Depends(get_current_user)):
    """Download de um artefato gerado pela IA (PDF, etc.)."""
    from fastapi.responses import StreamingResponse as _SR
    art = await db.chat_artifacts.find_one(
        {"id": artifact_id, "user_id": current_user.get("id")}, {"_id": 0}
    )
    if not art:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    content = base64.b64decode(art["content_b64"])
    return _SR(
        io.BytesIO(content),
        media_type=art.get("content_type", "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="{art.get("filename", "arquivo.pdf")}"',
        },
    )


@chatbot_router.post("/conversations/{conv_id}/messages", response_model=MessageOut)
async def send_message_in_conversation(
    conv_id: str,
    payload: MessageIn,
    current_user: dict = Depends(get_current_user),
):
    """Envia mensagem do usuário, gera resposta com Gemini 2.5 Flash + contexto da plataforma e persiste tudo."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    conv = await db.chat_conversations.find_one(
        {"id": conv_id, "user_id": current_user["id"]}, {"_id": 0}
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    now_iso = datetime.now(timezone.utc).isoformat()

    # Persistir mensagem do usuário
    user_msg = {
        "id": str(uuid.uuid4()),
        "conversation_id": conv_id,
        "role": "user",
        "content": payload.content,
        "created_at": now_iso,
    }
    await db.chat_messages.insert_one(dict(user_msg))

    # Construir histórico recente para contexto (últimas 30 mensagens) — emergentintegrations
    # mantém histórico por session_id; aqui re-injetamos o histórico textual no system prompt.
    msgs_anteriores = await db.chat_messages.find(
        {"conversation_id": conv_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(60)
    historico_txt = "\n".join(
        f"[{m['role'].upper()}]: {m['content']}" for m in msgs_anteriores[:-1]  # exclui a recém-inserida (vai no UserMessage)
    )

    # Contexto completo da plataforma
    platform_context = await get_full_platform_context()

    # Module-aware system prompt (RH em destaque)
    foco_modulo = ""
    if conv.get("module") == "rh":
        foco_modulo = (
            "Você é o assistente principal do MÓDULO DE RECURSOS HUMANOS desta plataforma. "
            "Tem acesso a TODOS os dados da plataforma (financeiro, frota, obras etc.) mas seu "
            "foco principal é responder com profundidade sobre Funcionários, Ponto Eletrônico, "
            "Folha de Pagamento, Férias, EPI, Custos de RH e Jornadas. Use os dados reais do "
            "banco para todas as respostas — nunca invente. Quando perguntarem sobre dados de "
            "outros módulos, responda com igual precisão.\n\n"
        )

    system_message = f"""{foco_modulo}Você é o assistente virtual inteligente da CRA Construtora.
Você tem ACESSO COMPLETO a TODAS as informações do banco de dados.

DADOS DO SISTEMA:
{platform_context}

HISTÓRICO RECENTE DESTA CONVERSA:
{historico_txt or "(início da conversa)"}

INSTRUÇÕES:
1. SEMPRE responda em português brasileiro.
2. Use quebras de linha para separar parágrafos e listas com "•".
3. Formate valores monetários como R$ 1.234,56.
4. NÃO use markdown com asteriscos.
5. Seja útil, direto e específico — cite números e nomes reais quando possível.
6. Se a pergunta for ambígua, pergunte qual recorte o usuário quer.

FERRAMENTAS DISPONÍVEIS (você PODE executar ações reais na plataforma):

Quando o usuário pedir para criar uma notificação, gerar um PDF, ou executar uma ação,
emita uma chamada de ferramenta ANTES da sua mensagem em texto, no formato:

<<TOOL>>{{"action":"NOME_DA_ACAO","params":{{...}}}}<<END>>

Ações suportadas:
• action="criar_notificacao" — params: {{"funcionario_id":"<id>","titulo":"...","mensagem":"...","tipo":"info|alerta|urgente"}}
  Use quando o usuário pedir para gerar/criar uma notificação para um funcionário.
• action="gerar_pdf_funcionario" — params: {{"funcionario_id":"<id>"}}
  Gera um PDF com dados completos de um funcionário (folha, ponto, férias, etc.).
• action="gerar_pdf_lista_funcionarios" — params: {{}}
  Gera um PDF com a lista geral de funcionários ativos.

Após o bloco <<TOOL>>...<<END>>, escreva uma mensagem natural em português confirmando
o que está sendo feito. NÃO emita uma ação se não tiver os parâmetros necessários —
nesse caso, pergunte ao usuário primeiro (ex.: "Para qual funcionário?").

Os IDs de funcionários estão na seção FUNCIONÁRIOS RH do contexto. Use o ID correto.
Se o usuário pedir uma ação genérica e houver ambiguidade (ex.: "gere notificação"),
peça os detalhes faltantes em vez de chutar.
"""

    llm_key = os.environ.get("EMERGENT_LLM_KEY")
    llm_chat = LlmChat(
        api_key=llm_key,
        session_id=f"conv-{conv_id}",
        system_message=system_message,
    ).with_model("gemini", "gemini-2.5-flash")

    try:
        ai_response = await llm_chat.send_message(UserMessage(text=payload.content))
    except Exception as e:
        logging.error(f"Erro Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na IA: {str(e)[:200]}")

    # ============ Detecção e execução de ferramentas ============
    artifact: Optional[dict] = None
    import re as _re_tools
    import json as _json_tools

    tool_match = _re_tools.search(
        r"<<TOOL>>\s*(\{.*?\})\s*<<END>>", ai_response, _re_tools.DOTALL
    )
    if tool_match:
        try:
            tool_data = _json_tools.loads(tool_match.group(1))
            tool_action = (tool_data.get("action") or "").strip()
            tool_params = tool_data.get("params") or {}
            artifact, tool_result_text = await _execute_chat_tool(
                tool_action, tool_params, current_user
            )
            # Remove o bloco <<TOOL>>...<<END>> da resposta final e prefixa com resultado
            ai_response = _re_tools.sub(
                r"<<TOOL>>.*?<<END>>", "", ai_response, flags=_re_tools.DOTALL
            ).strip()
            if tool_result_text:
                ai_response = f"{tool_result_text}\n\n{ai_response}".strip()
        except Exception as et:
            logging.warning(f"Falha ao executar tool do chatbot: {et}")
            ai_response = _re_tools.sub(
                r"<<TOOL>>.*?<<END>>", "", ai_response, flags=_re_tools.DOTALL
            ).strip()
            ai_response = (
                f"⚠️ Falha ao executar a ação solicitada: {str(et)[:200]}\n\n{ai_response}"
            ).strip()

    # Persistir resposta do assistente
    assistant_msg = {
        "id": str(uuid.uuid4()),
        "conversation_id": conv_id,
        "role": "assistant",
        "content": ai_response,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact": artifact,
    }
    await db.chat_messages.insert_one(dict(assistant_msg))

    # Atualizar conversa: timestamp + preview + título auto se ainda for "Nova conversa"
    update_fields = {
        "updated_at": assistant_msg["created_at"],
        "last_message_preview": (ai_response or "")[:120],
    }
    if conv.get("title") in (None, "", "Nova conversa"):
        # Pega as primeiras palavras da pergunta como título
        title_auto = (payload.content or "").strip().split("\n")[0][:60]
        if title_auto:
            update_fields["title"] = title_auto
    await db.chat_conversations.update_one({"id": conv_id}, {"$set": update_fields})

    return MessageOut(**{k: v for k, v in assistant_msg.items() if k != "conversation_id"})
