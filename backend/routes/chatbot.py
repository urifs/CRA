"""
Chatbot Routes - AI Assistant for the platform
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from datetime import datetime
import os
import io
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
    return decode_token(credentials.credentials)

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
    """Coleta TODAS as informações de TODAS as coleções do banco de dados"""
    context_parts = []
    
    context_parts.append("=" * 60)
    context_parts.append("BANCO DE DADOS COMPLETO - CRA CONSTRUTORA")
    context_parts.append("=" * 60)
    
    # USUÁRIOS
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nUSUÁRIOS DO SISTEMA ({len(users)} registros)\n{'='*40}")
    for u in users:
        context_parts.append(f"- Nome: {u.get('name')} | Email: {u.get('email')} | Tipo: {u.get('role', 'gerenciamento')}")
    
    # CATEGORIAS DE MÁQUINAS
    categories = await db.categories.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCATEGORIAS DE MÁQUINAS ({len(categories)} registros)\n{'='*40}")
    for c in categories:
        context_parts.append(f"- Nome: {c.get('name')} | Descrição: {c.get('description', '-')}")
    
    # MÁQUINAS
    machines = await db.machines.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nMÁQUINAS CADASTRADAS ({len(machines)} registros)\n{'='*40}")
    for m in machines:
        context_parts.append(f"- Nome: {m.get('name')} | Placa: {m.get('plate')} | Marca: {m.get('brand', '-')} | Status: {m.get('status', '-')}")
    
    # MANUTENÇÕES
    maintenances = await db.maintenances.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nMANUTENÇÕES ({len(maintenances)} registros)\n{'='*40}")
    total_valor = sum(m.get('part_value', 0) for m in maintenances)
    context_parts.append(f"RESUMO: Total gasto: R$ {total_valor:.2f}")
    for m in maintenances[:20]:
        context_parts.append(f"- Peça: {m.get('part_name')} | Valor: R$ {m.get('part_value', 0):.2f} | Data: {m.get('replacement_date', '-')}")
    
    # ESTOQUE
    stock_items = await db.stock_items.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nITENS DE ESTOQUE ({len(stock_items)} registros)\n{'='*40}")
    low_stock = [i for i in stock_items if i.get("quantity", 0) <= i.get("min_quantity", 0)]
    context_parts.append(f"ALERTA: {len(low_stock)} itens com estoque baixo!")
    for i in stock_items:
        context_parts.append(f"- Nome: {i.get('name')} | Qtd: {i.get('quantity', 0)} | Mínimo: {i.get('min_quantity', 0)}")
    
    # OBRAS
    obras = await db.obras.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nOBRAS/PROJETOS ({len(obras)} registros)\n{'='*40}")
    for o in obras:
        context_parts.append(f"- Nome: {o.get('name')} | Local: {o.get('location', '-')} | Status: {o.get('status', '-')}")
    
    # CADASTROS
    cadastros = await db.cadastros.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCADASTROS ({len(cadastros)} registros)\n{'='*40}")
    for c in cadastros:
        context_parts.append(f"- Tipo: {c.get('tipo_cadastro', '-')} | Nome: {c.get('nome_razao', '-')}")
    
    # CONTAS A PAGAR
    contas_pagar = await db.contas_pagar.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCONTAS A PAGAR ({len(contas_pagar)} registros)\n{'='*40}")
    total_pagar = sum(c.get('valor', 0) for c in contas_pagar if c.get('status') == 'em_aberto')
    context_parts.append(f"TOTAL EM ABERTO: R$ {total_pagar:.2f}")
    
    # CONTAS A RECEBER
    contas_receber = await db.contas_receber.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nCONTAS A RECEBER ({len(contas_receber)} registros)\n{'='*40}")
    total_receber = sum(c.get('valor', 0) for c in contas_receber if c.get('status') == 'em_aberto')
    context_parts.append(f"TOTAL EM ABERTO: R$ {total_receber:.2f}")
    
    # FUNCIONÁRIOS RH
    funcionarios = await db.funcionarios.find({}, {"_id": 0}).to_list(500)
    context_parts.append(f"\n\n{'='*40}\nFUNCIONÁRIOS RH ({len(funcionarios)} registros)\n{'='*40}")
    for f in funcionarios:
        context_parts.append(f"- Nome: {f.get('nome')} | Cargo: {f.get('cargo', '-')} | Salário: R$ {f.get('salario', 0):,.2f}")
    
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
        ).with_model("gemini", "gemini-2.0-flash")
        
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
        ).with_model("gemini", "gemini-2.0-flash")
        
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
