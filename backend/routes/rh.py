"""
RH Routes - Human Resources module endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body, Response
from fastapi.responses import FileResponse
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import os
import io
import json
import shutil
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Collections
funcionarios_collection = db["funcionarios"]
ponto_collection = db["ponto_registros"]
folha_pagamento_collection = db["folha_pagamento"]
ferias_collection = db["ferias"]
epi_fichas_collection = db["epi_fichas"]
epi_cargos_collection = db["epi_cargos"]

# Create router
rh_router = APIRouter(prefix="/rh", tags=["RH"])

# ===== Jornada de trabalho padrão =====
JORNADA_PADRAO = {
    "seg_sex": {
        "entrada": "08:00",
        "saida_almoco": "11:30",
        "retorno_almoco": "13:30",
        "saida": "18:00",
        "horas_diarias": 8.0
    },
    "sabado": {
        "entrada": "08:00",
        "saida": "12:00",
        "horas_diarias": 4.0
    }
}

# ===== Tabelas de alíquotas 2025 =====
TABELA_INSS_2025 = [
    {"ate": 1518.00, "aliquota": 7.5},
    {"ate": 2793.88, "aliquota": 9.0},
    {"ate": 4190.83, "aliquota": 12.0},
    {"ate": 8157.41, "aliquota": 14.0}
]
TETO_INSS = 951.01

TABELA_IRPF_2025 = [
    {"ate": 2259.20, "aliquota": 0, "deducao": 0},
    {"ate": 2826.65, "aliquota": 7.5, "deducao": 169.44},
    {"ate": 3751.05, "aliquota": 15.0, "deducao": 381.44},
    {"ate": 4664.68, "aliquota": 22.5, "deducao": 662.77},
    {"ate": 999999999.99, "aliquota": 27.5, "deducao": 896.00}
]

FGTS_ALIQUOTA = 8.0
INSS_PATRONAL_ALIQUOTA = 20.0


# ===== Helper Functions =====
def calcular_inss(salario_bruto: float) -> float:
    inss = 0.0
    salario_restante = salario_bruto
    faixa_anterior = 0.0
    
    for faixa in TABELA_INSS_2025:
        if salario_restante <= 0:
            break
        base = min(salario_restante, faixa["ate"] - faixa_anterior)
        inss += base * (faixa["aliquota"] / 100)
        salario_restante -= base
        faixa_anterior = faixa["ate"]
    
    return min(inss, TETO_INSS)


def calcular_irpf(base_calculo: float) -> float:
    for faixa in TABELA_IRPF_2025:
        if base_calculo <= faixa["ate"]:
            return max(0, (base_calculo * faixa["aliquota"] / 100) - faixa["deducao"])
    return 0.0


# ===== PYDANTIC MODELS =====
from pydantic import BaseModel

class FuncionarioCreate(BaseModel):
    nome: str
    cpf: Optional[str] = None
    rg: Optional[str] = None
    data_nascimento: Optional[str] = None
    telefone: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[str] = None
    cep: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cargo: str
    funcao: Optional[str] = None
    departamento: Optional[str] = None
    salario: float = 0
    data_admissao: str
    regime_contratacao: str = "CLT"
    status: str = "ativo"
    observacoes: Optional[str] = None


class PontoCreate(BaseModel):
    funcionario_id: str
    data: str
    entrada: str
    saida_almoco: Optional[str] = ""
    retorno_almoco: Optional[str] = ""
    saida: str
    observacoes: Optional[str] = ""


class FolhaCreate(BaseModel):
    funcionario_id: str
    mes: int
    ano: int
    salario_base: float
    horas_extras: float = 0
    valor_hora_extra: float = 0
    adicional_noturno: float = 0
    comissoes: float = 0
    vale_transporte: float = 0
    vale_alimentacao: float = 0
    plano_saude: float = 0
    outros_descontos: float = 0
    salario_bruto: float = 0
    inss: float = 0
    irpf: float = 0
    fgts: float = 0
    total_descontos: float = 0
    salario_liquido: float = 0


class FeriasCreate(BaseModel):
    funcionario_id: str
    data_inicio: str
    data_fim: str
    dias_vendidos: int = 0
    observacoes: Optional[str] = None


class EPIItem(BaseModel):
    nome: str
    ca: Optional[str] = None
    validade: Optional[str] = None
    data_entrega: Optional[str] = None


class FichaEPICreate(BaseModel):
    funcionario_id: str
    cargo: str
    codigo_cbo: Optional[str] = None
    epis: List[EPIItem] = []
    observacoes: Optional[str] = None


# ===== CBO DATABASE =====
CBO_DATABASE = {
    "7152-10": {"titulo": "Pedreiro", "familia": "Trabalhadores de estruturas de alvenaria", "sinonimos": ["Pedreiro de alvenaria", "Pedreiro de edificações"]},
    "7152-15": {"titulo": "Pedreiro de acabamento", "familia": "Trabalhadores de estruturas de alvenaria", "sinonimos": ["Pedreiro de revestimento"]},
    "7152-20": {"titulo": "Pedreiro de fachadas", "familia": "Trabalhadores de estruturas de alvenaria", "sinonimos": []},
    "7241-05": {"titulo": "Eletricista de instalações (prediais)", "familia": "Eletricistas de instalações", "sinonimos": ["Eletricista predial", "Eletricista de manutenção predial"]},
    "7241-10": {"titulo": "Eletricista de instalações (industriais)", "familia": "Eletricistas de instalações", "sinonimos": ["Eletricista industrial"]},
    "7244-10": {"titulo": "Eletricista de manutenção de linhas elétricas", "familia": "Trabalhadores de manutenção de linhas elétricas", "sinonimos": []},
    "7153-05": {"titulo": "Armador de estrutura de concreto", "familia": "Trabalhadores de estruturas de concreto armado", "sinonimos": ["Armador de ferragens", "Ferreiro armador"]},
    "7153-10": {"titulo": "Moldador de concreto armado", "familia": "Trabalhadores de estruturas de concreto armado", "sinonimos": ["Carpinteiro de formas"]},
    "7155-05": {"titulo": "Carpinteiro", "familia": "Carpinteiros", "sinonimos": ["Carpinteiro de obras", "Carpinteiro de construção"]},
    "7155-35": {"titulo": "Carpinteiro de telhados", "familia": "Carpinteiros", "sinonimos": ["Carpinteiro de estruturas de madeira"]},
    "7161-10": {"titulo": "Pintor de obras", "familia": "Pintores de obras e decoradores", "sinonimos": ["Pintor de construção civil", "Pintor de paredes"]},
    "7161-20": {"titulo": "Pintor de estruturas metálicas", "familia": "Pintores de obras e decoradores", "sinonimos": []},
    "7166-10": {"titulo": "Encanador", "familia": "Instaladores de tubulações", "sinonimos": ["Bombeiro hidráulico", "Encanador industrial"]},
    "7166-20": {"titulo": "Instalador de tubulações de gás", "familia": "Instaladores de tubulações", "sinonimos": []},
    "7170-20": {"titulo": "Servente de obras", "familia": "Ajudantes de obras civis", "sinonimos": ["Auxiliar de pedreiro", "Ajudante de construção"]},
    "7170-25": {"titulo": "Vibradorista", "familia": "Ajudantes de obras civis", "sinonimos": []},
    "7823-10": {"titulo": "Operador de escavadeira", "familia": "Operadores de máquinas de movimentação de cargas", "sinonimos": ["Operador de retroescavadeira"]},
    "7823-20": {"titulo": "Operador de pá carregadeira", "familia": "Operadores de máquinas de movimentação de cargas", "sinonimos": []},
    "7824-10": {"titulo": "Operador de guindaste (móvel)", "familia": "Operadores de guindastes", "sinonimos": ["Guindasteiro"]},
    "7825-10": {"titulo": "Operador de empilhadeira", "familia": "Operadores de empilhadeiras", "sinonimos": ["Empilhadeirista"]},
    "7821-25": {"titulo": "Motorista de caminhão", "familia": "Condutores de veículos sobre rodas", "sinonimos": ["Caminhoneiro"]},
    "7821-15": {"titulo": "Motorista de ônibus", "familia": "Condutores de veículos sobre rodas", "sinonimos": []},
    "7251-10": {"titulo": "Soldador", "familia": "Soldadores e oxicortadores", "sinonimos": ["Soldador elétrico", "Soldador a arco"]},
    "7251-25": {"titulo": "Soldador a oxigás", "familia": "Soldadores e oxicortadores", "sinonimos": []},
    "7252-05": {"titulo": "Serralheiro", "familia": "Trabalhadores de estruturas de metal", "sinonimos": ["Serralheiro de alumínio", "Serralheiro industrial"]},
    "7211-10": {"titulo": "Ferramenteiro", "familia": "Ferramenteiros e operadores de máquinas", "sinonimos": ["Ferramenteiro de moldes"]},
    "7211-20": {"titulo": "Torneiro mecânico", "familia": "Ferramenteiros e operadores de máquinas", "sinonimos": ["Torneiro CNC"]},
    "7211-25": {"titulo": "Fresador mecânico", "familia": "Ferramenteiros e operadores de máquinas", "sinonimos": []},
    "5143-20": {"titulo": "Vigia", "familia": "Trabalhadores de segurança e vigilância", "sinonimos": ["Vigilante", "Guarda"]},
    "4110-10": {"titulo": "Auxiliar de escritório", "familia": "Escriturários em geral", "sinonimos": ["Auxiliar administrativo"]},
}

# EPIs por tipo de função
EPI_POR_CARGO = {
    "construcao_civil": [
        {"nome": "Capacete", "ca": "A definir", "validade_meses": 36, "prioridade": "Alta"},
        {"nome": "Óculos de proteção", "ca": "A definir", "validade_meses": 24, "prioridade": "Alta"},
        {"nome": "Luvas de proteção", "ca": "A definir", "validade_meses": 6, "prioridade": "Alta"},
        {"nome": "Botina de segurança", "ca": "A definir", "validade_meses": 12, "prioridade": "Alta"},
        {"nome": "Protetor auricular", "ca": "A definir", "validade_meses": 6, "prioridade": "Média"},
        {"nome": "Cinto de segurança", "ca": "A definir", "validade_meses": 24, "prioridade": "Alta"},
    ],
    "eletricidade": [
        {"nome": "Capacete classe B", "ca": "A definir", "validade_meses": 36, "prioridade": "Alta"},
        {"nome": "Óculos de proteção", "ca": "A definir", "validade_meses": 24, "prioridade": "Alta"},
        {"nome": "Luvas isolantes", "ca": "A definir", "validade_meses": 6, "prioridade": "Alta"},
        {"nome": "Botina isolante", "ca": "A definir", "validade_meses": 12, "prioridade": "Alta"},
        {"nome": "Vestimenta antichama", "ca": "A definir", "validade_meses": 24, "prioridade": "Alta"},
        {"nome": "Detector de tensão", "ca": "A definir", "validade_meses": 12, "prioridade": "Alta"},
    ],
    "soldagem": [
        {"nome": "Máscara de solda", "ca": "A definir", "validade_meses": 24, "prioridade": "Alta"},
        {"nome": "Avental de raspa", "ca": "A definir", "validade_meses": 12, "prioridade": "Alta"},
        {"nome": "Luvas de raspa", "ca": "A definir", "validade_meses": 3, "prioridade": "Alta"},
        {"nome": "Mangote de raspa", "ca": "A definir", "validade_meses": 6, "prioridade": "Alta"},
        {"nome": "Perneira de raspa", "ca": "A definir", "validade_meses": 12, "prioridade": "Alta"},
        {"nome": "Botina de segurança", "ca": "A definir", "validade_meses": 12, "prioridade": "Alta"},
    ],
    "operador_maquinas": [
        {"nome": "Capacete", "ca": "A definir", "validade_meses": 36, "prioridade": "Alta"},
        {"nome": "Protetor auricular", "ca": "A definir", "validade_meses": 6, "prioridade": "Alta"},
        {"nome": "Óculos de proteção", "ca": "A definir", "validade_meses": 24, "prioridade": "Média"},
        {"nome": "Luvas de vaqueta", "ca": "A definir", "validade_meses": 6, "prioridade": "Média"},
        {"nome": "Botina de segurança", "ca": "A definir", "validade_meses": 12, "prioridade": "Alta"},
    ],
    "administrativo": [
        {"nome": "Não requer EPIs específicos", "ca": "-", "validade_meses": 0, "prioridade": "Baixa"},
    ]
}


def get_categoria_epi(codigo_cbo: str) -> str:
    """Determina a categoria de EPI baseado no código CBO"""
    if codigo_cbo.startswith("715"):  # Construção civil
        return "construcao_civil"
    elif codigo_cbo.startswith("724"):  # Eletricidade
        return "eletricidade"
    elif codigo_cbo.startswith("725"):  # Serralheria e Metalurgia
        return "soldagem"
    elif codigo_cbo.startswith("782") or codigo_cbo.startswith("783"):  # Operadores
        return "operador_maquinas"
    elif codigo_cbo.startswith("411") or codigo_cbo.startswith("514"):  # Administrativo
        return "administrativo"
    else:
        return "construcao_civil"  # Default


# ===== DASHBOARD =====
@rh_router.get("/dashboard")
async def get_rh_dashboard():
    """Dashboard do RH com estatísticas"""
    try:
        total_funcionarios = await funcionarios_collection.count_documents({})
        funcionarios_ativos = await funcionarios_collection.count_documents({"status": "ativo"})
        funcionarios_ferias = await funcionarios_collection.count_documents({"status": "ferias"})
        funcionarios_afastados = await funcionarios_collection.count_documents({"status": "afastado"})
        
        total_folha = 0
        async for func in funcionarios_collection.find({"status": "ativo"}):
            total_folha += func.get("salario", 0)
        
        hoje = datetime.now()
        mes_atual = hoje.month
        
        aniversariantes = []
        async for func in funcionarios_collection.find({"status": "ativo"}):
            if func.get("data_nascimento"):
                try:
                    data_nasc = datetime.strptime(func["data_nascimento"], "%Y-%m-%d")
                    if data_nasc.month == mes_atual:
                        aniversariantes.append({
                            "nome": func["nome"],
                            "data": data_nasc.strftime("%d/%m"),
                            "cargo": func.get("cargo", "-")
                        })
                except:
                    pass
        
        alertas_ferias = []
        async for func in funcionarios_collection.find({"status": "ativo"}):
            if func.get("data_admissao"):
                try:
                    data_adm = datetime.strptime(func["data_admissao"], "%Y-%m-%d")
                    meses_trabalhados = (hoje.year - data_adm.year) * 12 + (hoje.month - data_adm.month)
                    
                    if meses_trabalhados >= 11:
                        alertas_ferias.append({
                            "nome": func["nome"],
                            "meses": meses_trabalhados,
                            "mensagem": f"Completou {meses_trabalhados} meses"
                        })
                except:
                    pass
        
        alertas_epi = []
        async for ficha in epi_fichas_collection.find({}):
            func = await funcionarios_collection.find_one({"id": ficha.get("funcionario_id")})
            if func and ficha.get("epis"):
                for epi in ficha["epis"]:
                    if epi.get("validade"):
                        try:
                            validade = datetime.strptime(epi["validade"], "%Y-%m-%d")
                            dias_restantes = (validade - hoje).days
                            if 0 < dias_restantes <= 30:
                                alertas_epi.append({
                                    "funcionario": func["nome"],
                                    "epi": epi["nome"],
                                    "dias_restantes": dias_restantes
                                })
                        except:
                            pass
        
        # Calcular ponto de hoje
        hoje_str = hoje.strftime("%Y-%m-%d")
        presentes = 0
        atrasados = 0
        async for reg in ponto_collection.find({"data": hoje_str}):
            if reg.get("entrada"):
                presentes += 1
                try:
                    h, m = map(int, reg["entrada"].split(":"))
                    if h > 8 or (h == 8 and m > 15):
                        atrasados += 1
                except:
                    pass
        ausentes = funcionarios_ativos - presentes
        
        return {
            "total_funcionarios": total_funcionarios,
            "funcionarios_ativos": funcionarios_ativos,
            "funcionarios_ferias": funcionarios_ferias,
            "funcionarios_afastados": funcionarios_afastados,
            "total_folha": total_folha,
            "aniversariantes": aniversariantes[:5],
            "aniversariantes_mes": aniversariantes[:5],
            "alertas_ferias": alertas_ferias,
            "alertas_epi": alertas_epi[:10],
            "jornada": JORNADA_PADRAO,
            "tabela_inss": TABELA_INSS_2025,
            "tabela_irpf": TABELA_IRPF_2025,
            "ponto_hoje": {
                "presentes": presentes,
                "ausentes": max(0, ausentes),
                "atrasados": atrasados
            }
        }
    except Exception as e:
        return {
            "total_funcionarios": 0,
            "funcionarios_ativos": 0,
            "funcionarios_ferias": 0,
            "funcionarios_afastados": 0,
            "total_folha": 0,
            "aniversariantes": [],
            "aniversariantes_mes": [],
            "alertas_ferias": [],
            "alertas_epi": [],
            "jornada": JORNADA_PADRAO,
            "tabela_inss": TABELA_INSS_2025,
            "tabela_irpf": TABELA_IRPF_2025,
            "ponto_hoje": {
                "presentes": 0,
                "ausentes": 0,
                "atrasados": 0
            }
        }


# ===== FUNCIONARIOS =====
@rh_router.get("/funcionarios")
async def list_funcionarios():
    """Listar todos os funcionários"""
    funcionarios = []
    async for func in funcionarios_collection.find({}):
        func["_id"] = str(func["_id"])
        funcionarios.append(func)
    return funcionarios


@rh_router.get("/funcionarios/{funcionario_id}")
async def get_funcionario(funcionario_id: str):
    """Obter funcionário por ID"""
    func = await funcionarios_collection.find_one({"id": funcionario_id})
    if not func:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    func["_id"] = str(func["_id"])
    return func


@rh_router.post("/funcionarios")
async def create_funcionario(data: FuncionarioCreate):
    """Criar novo funcionário"""
    func_doc = data.dict()
    func_doc["id"] = str(uuid.uuid4())
    func_doc["created_at"] = datetime.now().isoformat()
    func_doc["anexos"] = []
    
    await funcionarios_collection.insert_one(func_doc)
    func_doc["_id"] = str(func_doc.get("_id", ""))
    return func_doc


@rh_router.put("/funcionarios/{funcionario_id}")
async def update_funcionario(funcionario_id: str, data: FuncionarioCreate):
    """Atualizar funcionário"""
    existing = await funcionarios_collection.find_one({"id": funcionario_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    update_data = data.dict()
    update_data["updated_at"] = datetime.now().isoformat()
    
    await funcionarios_collection.update_one(
        {"id": funcionario_id},
        {"$set": update_data}
    )
    
    return {"message": "Funcionário atualizado com sucesso"}


@rh_router.delete("/funcionarios/{funcionario_id}")
async def delete_funcionario(funcionario_id: str):
    """Excluir funcionário"""
    existing = await funcionarios_collection.find_one({"id": funcionario_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    if existing.get("anexos"):
        for anexo in existing["anexos"]:
            try:
                if os.path.exists(anexo.get("path", "")):
                    os.remove(anexo["path"])
            except:
                pass
    
    await funcionarios_collection.delete_one({"id": funcionario_id})
    return {"message": "Funcionário excluído com sucesso"}


# ===== PONTO =====
@rh_router.get("/ponto")
async def list_ponto(data: Optional[str] = None, funcionario_id: Optional[str] = None):
    """Listar registros de ponto"""
    query = {}
    if data:
        query["data"] = data
    if funcionario_id:
        query["funcionario_id"] = funcionario_id
    
    registros = []
    async for reg in ponto_collection.find(query).sort("data", -1):
        reg["_id"] = str(reg["_id"])
        func = await funcionarios_collection.find_one({"id": reg["funcionario_id"]})
        reg["funcionario_nome"] = func["nome"] if func else "-"
        registros.append(reg)
    
    return registros


@rh_router.post("/ponto")
async def create_ponto(data: PontoCreate):
    """Criar registro de ponto"""
    existing = await ponto_collection.find_one({
        "funcionario_id": data.funcionario_id,
        "data": data.data
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Já existe registro para este funcionário nesta data")
    
    ponto_doc = data.dict()
    ponto_doc["id"] = str(uuid.uuid4())
    ponto_doc["created_at"] = datetime.now().isoformat()
    
    await ponto_collection.insert_one(ponto_doc)
    ponto_doc["_id"] = str(ponto_doc.get("_id", ""))
    return ponto_doc


@rh_router.put("/ponto/{ponto_id}")
async def update_ponto(ponto_id: str, data: PontoCreate):
    """Atualizar registro de ponto"""
    existing = await ponto_collection.find_one({"id": ponto_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    
    update_data = data.dict()
    update_data["updated_at"] = datetime.now().isoformat()
    
    await ponto_collection.update_one({"id": ponto_id}, {"$set": update_data})
    return {"message": "Registro atualizado"}


@rh_router.delete("/ponto/{ponto_id}")
async def delete_ponto(ponto_id: str):
    """Excluir registro de ponto"""
    result = await ponto_collection.delete_one({"id": ponto_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return {"message": "Registro excluído com sucesso"}


# ===== IMPORTAÇÃO DE PLANILHA DE PONTO (.xls) =====
def _normalizar_nome(nome: str) -> str:
    """Normaliza nome para comparação: trim + lowercase + remover múltiplos espaços."""
    if not nome:
        return ""
    return " ".join(nome.strip().lower().split())


def _parse_batidas_celula(valor: str) -> list:
    """Recebe o valor da célula (ex: '08:01\\n11:50\\n13:55\\n17:48') e retorna lista ordenada de batidas HH:MM."""
    if not valor:
        return []
    raw = str(valor).replace("\r", "\n").split("\n")
    batidas = []
    for b in raw:
        b = b.strip()
        if not b:
            continue
        # Aceita formatos HH:MM ou HH:MM:SS
        partes = b.split(":")
        if len(partes) >= 2:
            try:
                h = int(partes[0])
                m = int(partes[1])
                if 0 <= h <= 23 and 0 <= m <= 59:
                    batidas.append(f"{h:02d}:{m:02d}")
            except (ValueError, TypeError):
                continue
    # Ordenar
    batidas.sort()
    return batidas


def _calcular_minutos_trabalhados(batidas: list, dia_semana: int) -> tuple:
    """Calcula minutos trabalhados a partir de uma lista de batidas ordenadas.
    Regras:
      - 0 batidas: dia sem registro (falta se for dia útil)
      - 1 batida: incompleto (entrada apenas) → 0 minutos
      - 2 batidas: entrada e saída sem almoço (jornada curta, ex: sábado)
      - 3 batidas: assume entrada/saída-almoço/retorno (sem saída final) ou inverso → aplica almoço padrão de 60min
      - 4+ batidas: pareia em entrada/saída-almoço/retorno-almoço/saída
    Retorna: (minutos_trabalhados, status_legivel)
    """
    if not batidas:
        return 0, "sem_registro"
    if len(batidas) == 1:
        return 0, "incompleto"
    
    def to_min(s):
        h, m = s.split(":")
        return int(h) * 60 + int(m)
    
    pts = [to_min(b) for b in batidas]
    
    if len(pts) == 2:
        return max(0, pts[1] - pts[0]), "ok_2_batidas"
    
    if len(pts) == 3:
        # Inferir: entrada=p1, saída=p3; descontar 60min de almoço
        bruto = pts[2] - pts[0]
        liquido = max(0, bruto - 60)
        return liquido, "inferido_3_batidas"
    
    # 4+ batidas: usa as primeiras 4 (entrada, saída-almoço, retorno-almoço, saída)
    e, sa, ra, s = pts[0], pts[1], pts[2], pts[3]
    parte1 = max(0, sa - e)
    parte2 = max(0, s - ra)
    return parte1 + parte2, "ok_4_batidas"


def _jornada_prevista_minutos(dia_semana: int) -> int:
    """0=Seg ... 5=Sáb, 6=Dom. Retorna minutos previstos."""
    if dia_semana <= 4:  # Seg-Sex
        return 8 * 60
    if dia_semana == 5:  # Sábado
        return 4 * 60
    return 0  # Domingo


@rh_router.post("/ponto/importar-planilha")
async def importar_planilha_ponto(file: UploadFile = File(...)):
    """Importa planilha .xls/.xlsx de registro de presença (formato Topdata/Hikvision/etc.).
    
    Estrutura esperada:
      Linha N+0: 'IDUsuário: <id>' ... 'Nome: <nome>' ... 'Dep.: <departamento>'
      Linha N+1: cabeçalho com dias do mês (1, 2, 3, ..., 31)
      Linha N+2: batidas separadas por \\n para cada dia
      Linha 2 contém 'Data de presença:DD/MM/AAAA~DD/MM/AAAA'
    
    Comportamento:
      - Match por nome exato (case-insensitive normalizado)
      - Funcionários não encontrados: registros são salvos com flag 'funcionario_nao_cadastrado'
      - Sobrescreve registros existentes do mesmo (funcionario_id, data)
    """
    import xlrd
    import re
    
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    
    # Detectar formato pelo magic byte
    if content[:8].hex().lower() == "d0cf11e0a1b11ae1":
        try:
            wb = xlrd.open_workbook(file_contents=content, formatting_info=False)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao abrir .xls: {e}")
    elif content[:4] == b"PK\x03\x04":
        try:
            from openpyxl import load_workbook
            from io import BytesIO
            wb_x = load_workbook(BytesIO(content), data_only=True)
            # Converter para um wb-like com sheet_by_index
            class _SheetWrap:
                def __init__(self, ws):
                    self.ws = ws
                    self.nrows = ws.max_row
                    self.ncols = ws.max_column
                def cell_value(self, r, c):
                    v = self.ws.cell(row=r+1, column=c+1).value
                    return v if v is not None else ""
            class _WBWrap:
                def __init__(self, wbx):
                    self.wbx = wbx
                def sheet_by_index(self, i):
                    return _SheetWrap(self.wbx.worksheets[i])
            wb = _WBWrap(wb_x)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao abrir .xlsx: {e}")
    else:
        raise HTTPException(status_code=400, detail="Formato não reconhecido. Envie um arquivo .xls ou .xlsx válido.")
    
    sh = wb.sheet_by_index(0)
    
    # Detectar período (procurar nas primeiras 10 linhas)
    periodo_match = None
    for r in range(min(10, sh.nrows)):
        for c in range(sh.ncols):
            v = str(sh.cell_value(r, c) or "")
            m = re.search(r"(\d{2}/\d{2}/\d{4})\s*[~\-–]\s*(\d{2}/\d{2}/\d{4})", v)
            if m:
                periodo_match = m
                break
        if periodo_match:
            break
    
    if not periodo_match:
        raise HTTPException(status_code=400, detail="Não foi possível identificar o período (procurando 'Data de presença:DD/MM/AAAA~DD/MM/AAAA')")
    
    inicio_str, fim_str = periodo_match.group(1), periodo_match.group(2)
    try:
        inicio_dt = datetime.strptime(inicio_str, "%d/%m/%Y")
        fim_dt = datetime.strptime(fim_str, "%d/%m/%Y")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Período inválido: {e}")
    
    if inicio_dt.year != fim_dt.year or inicio_dt.month != fim_dt.month:
        raise HTTPException(status_code=400, detail="A planilha deve cobrir UM ÚNICO mês (limitação atual).")
    
    ano = inicio_dt.year
    mes = inicio_dt.month
    
    # Carregar todos os funcionários para matching por nome
    funcs_db = {}
    async for f in funcionarios_collection.find({}):
        funcs_db[_normalizar_nome(f.get("nome", ""))] = f
    
    # Os registros existentes serão sobrescritos individualmente abaixo (por funcionario_id + data)
    
    # Iterar linhas em busca de blocos de funcionários
    funcionarios_processados = []
    funcionarios_nao_cadastrados = []
    total_registros_inseridos = 0
    
    r = 0
    while r < sh.nrows:
        linha_idu = [str(sh.cell_value(r, c) or "").strip() for c in range(sh.ncols)]
        linha_concat = " ".join(linha_idu).lower()
        
        # Buscar a linha que contém 'idusuário' ou 'idusuario'
        if "idusuário" in linha_concat or "idusuario" in linha_concat:
            # Extrair IDUsuário, Nome, Dep.
            id_usuario = ""
            nome = ""
            dep = ""
            for c in range(sh.ncols):
                v = str(sh.cell_value(r, c) or "").strip()
                v_low = v.lower()
                if v_low.startswith("idusuário") or v_low.startswith("idusuario"):
                    # ID está no próximo valor não vazio
                    for c2 in range(c + 1, sh.ncols):
                        nv = str(sh.cell_value(r, c2) or "").strip()
                        if nv:
                            id_usuario = nv
                            break
                elif v_low.startswith("nome"):
                    for c2 in range(c + 1, sh.ncols):
                        nv = str(sh.cell_value(r, c2) or "").strip()
                        if nv:
                            nome = nv
                            break
                elif v_low.startswith("dep"):
                    for c2 in range(c + 1, sh.ncols):
                        nv = str(sh.cell_value(r, c2) or "").strip()
                        if nv:
                            dep = nv
                            break
            
            # Próxima linha: cabeçalho de dias (1.0, 2.0, ..., 31.0)
            # Linha r+1 = dias, Linha r+2 = batidas
            if r + 2 < sh.nrows and nome:
                linha_dias = [sh.cell_value(r + 1, c) for c in range(sh.ncols)]
                linha_batidas = [sh.cell_value(r + 2, c) for c in range(sh.ncols)]
                
                # Match funcionário
                nome_norm = _normalizar_nome(nome)
                func = funcs_db.get(nome_norm)
                func_id = func["id"] if func else None
                cargo = func.get("cargo", "") if func else ""
                
                if not func:
                    funcionarios_nao_cadastrados.append({
                        "nome": nome,
                        "id_usuario_planilha": id_usuario,
                        "departamento_planilha": dep,
                    })
                
                # Iterar dias: cada coluna onde linha_dias é numérica = dia válido
                dias_processados = 0
                for c in range(sh.ncols):
                    dia_val = linha_dias[c]
                    try:
                        dia_num = int(float(dia_val)) if dia_val not in (None, "") else 0
                    except (ValueError, TypeError):
                        dia_num = 0
                    
                    if not (1 <= dia_num <= 31):
                        continue
                    
                    # Validar que o dia existe no mês
                    try:
                        data_str = f"{ano}-{mes:02d}-{dia_num:02d}"
                        data_dt = datetime.strptime(data_str, "%Y-%m-%d")
                    except ValueError:
                        continue
                    
                    batidas_raw = linha_batidas[c] if c < len(linha_batidas) else ""
                    batidas = _parse_batidas_celula(batidas_raw)
                    
                    dia_semana = data_dt.weekday()
                    minutos_trab, status_dia = _calcular_minutos_trabalhados(batidas, dia_semana)
                    minutos_prev = _jornada_prevista_minutos(dia_semana)
                    saldo = minutos_trab - minutos_prev
                    
                    # Montar registro: usa primeira batida como entrada, última como saída, etc.
                    entrada = batidas[0] if len(batidas) >= 1 else ""
                    saida = batidas[-1] if len(batidas) >= 2 else ""
                    saida_almoco = batidas[1] if len(batidas) >= 4 else (batidas[1] if len(batidas) == 3 else "")
                    retorno_almoco = batidas[2] if len(batidas) >= 4 else ""
                    
                    ponto_doc = {
                        "id": str(uuid.uuid4()),
                        "funcionario_id": func_id or f"NAO_CADASTRADO::{nome_norm}",
                        "funcionario_nome_planilha": nome,
                        "funcionario_nao_cadastrado": func is None,
                        "id_usuario_planilha": id_usuario,
                        "departamento_planilha": dep,
                        "data": data_str,
                        "batidas": batidas,
                        "entrada": entrada,
                        "saida_almoco": saida_almoco,
                        "retorno_almoco": retorno_almoco,
                        "saida": saida,
                        "minutos_trabalhados": minutos_trab,
                        "minutos_previstos": minutos_prev,
                        "saldo_minutos": saldo,
                        "status_dia": status_dia,
                        "dia_semana": dia_semana,
                        "origem": "planilha_xls",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    
                    # Sobrescrever existente
                    await ponto_collection.delete_many({
                        "funcionario_id": ponto_doc["funcionario_id"],
                        "data": data_str,
                    })
                    await ponto_collection.insert_one(ponto_doc)
                    total_registros_inseridos += 1
                    dias_processados += 1
                
                funcionarios_processados.append({
                    "nome": nome,
                    "id_usuario_planilha": id_usuario,
                    "departamento": dep or cargo,
                    "funcionario_id": func_id,
                    "cadastrado": func is not None,
                    "dias_com_registro": dias_processados,
                })
                r += 3
                continue
        r += 1
    
    return {
        "message": f"Importação concluída: {total_registros_inseridos} registros de ponto importados.",
        "periodo": {"inicio": inicio_str, "fim": fim_str, "mes": mes, "ano": ano},
        "total_funcionarios": len(funcionarios_processados),
        "total_registros": total_registros_inseridos,
        "funcionarios_processados": funcionarios_processados,
        "funcionarios_nao_cadastrados": funcionarios_nao_cadastrados,
        "aviso_nao_cadastrados": (
            f"{len(funcionarios_nao_cadastrados)} funcionário(s) da planilha não estão cadastrados na plataforma "
            f"(serão exibidos no quadro com aviso): {', '.join([f['nome'] for f in funcionarios_nao_cadastrados[:5]])}"
            if funcionarios_nao_cadastrados else None
        ),
    }


@rh_router.get("/ponto/dashboard-mensal")
async def get_ponto_dashboard_mensal(mes: int, ano: int):
    """Quadro consolidado por funcionário do mês: horas trabalhadas vs previstas, saldo, banco de horas acumulado.
    Inclui detalhamento dia a dia."""
    inicio_mes = f"{ano}-{mes:02d}-01"
    if mes == 12:
        fim_mes = f"{ano + 1}-01-01"
    else:
        fim_mes = f"{ano}-{mes + 1:02d}-01"
    
    pipeline = [
        {"$match": {"data": {"$gte": inicio_mes, "$lt": fim_mes}}},
        {"$sort": {"data": 1}},
    ]
    
    por_func = {}
    async for reg in ponto_collection.aggregate(pipeline):
        fid = reg["funcionario_id"]
        if fid not in por_func:
            por_func[fid] = []
        por_func[fid].append(reg)
    
    # Banco de horas acumulado (de TODOS os meses anteriores e atual): soma saldo_minutos de cada registro
    banco_acumulado_por_func = {}
    async for reg in ponto_collection.aggregate([
        {"$match": {"data": {"$lt": fim_mes}}},
        {"$group": {"_id": "$funcionario_id", "total": {"$sum": "$saldo_minutos"}}},
    ]):
        banco_acumulado_por_func[reg["_id"]] = int(reg.get("total", 0) or 0)
    
    funcionarios_dashboard = []
    for fid, registros in por_func.items():
        # Tentar achar funcionário
        nome = ""
        cargo = ""
        departamento = ""
        cadastrado = False
        if fid.startswith("NAO_CADASTRADO::"):
            nome = registros[0].get("funcionario_nome_planilha", "")
            departamento = registros[0].get("departamento_planilha", "")
            cargo = "(Não cadastrado)"
            cadastrado = False
        else:
            func = await funcionarios_collection.find_one({"id": fid})
            if func:
                nome = func.get("nome", "")
                cargo = func.get("cargo", "")
                departamento = func.get("departamento", "") or registros[0].get("departamento_planilha", "")
                cadastrado = True
            else:
                nome = registros[0].get("funcionario_nome_planilha", "?")
                cargo = "(Funcionário removido)"
                cadastrado = False
        
        total_trab = sum(int(r.get("minutos_trabalhados", 0) or 0) for r in registros)
        total_prev = sum(int(r.get("minutos_previstos", 0) or 0) for r in registros)
        saldo_mes = total_trab - total_prev
        
        dias_com_registro = sum(1 for r in registros if r.get("minutos_trabalhados", 0) > 0)
        dias_incompletos = sum(1 for r in registros if r.get("status_dia") == "incompleto")
        dias_falta = sum(1 for r in registros if r.get("status_dia") == "sem_registro" and r.get("dia_semana", 6) <= 5)
        
        # Detalhamento dia a dia
        detalhe = []
        for r in registros:
            detalhe.append({
                "data": r.get("data"),
                "dia_semana": r.get("dia_semana"),
                "batidas": r.get("batidas", []),
                "minutos_trabalhados": r.get("minutos_trabalhados", 0),
                "minutos_previstos": r.get("minutos_previstos", 0),
                "saldo_minutos": r.get("saldo_minutos", 0),
                "status_dia": r.get("status_dia"),
            })
        
        funcionarios_dashboard.append({
            "funcionario_id": fid,
            "nome": nome,
            "cargo": cargo,
            "departamento": departamento,
            "cadastrado": cadastrado,
            "minutos_trabalhados": total_trab,
            "minutos_previstos": total_prev,
            "saldo_mes_minutos": saldo_mes,
            "banco_horas_acumulado_minutos": banco_acumulado_por_func.get(fid, 0),
            "dias_com_registro": dias_com_registro,
            "dias_incompletos": dias_incompletos,
            "dias_falta": dias_falta,
            "detalhe_dias": detalhe,
        })
    
    # Ordenar: cadastrados primeiro, por nome
    funcionarios_dashboard.sort(key=lambda x: (not x["cadastrado"], x["nome"].lower()))
    
    # Totais gerais
    total_funcionarios = len(funcionarios_dashboard)
    total_extras = sum(max(0, f["saldo_mes_minutos"]) for f in funcionarios_dashboard)
    total_devidas = sum(abs(min(0, f["saldo_mes_minutos"])) for f in funcionarios_dashboard)
    
    return {
        "mes": mes,
        "ano": ano,
        "total_funcionarios": total_funcionarios,
        "total_extras_minutos": total_extras,
        "total_devidas_minutos": total_devidas,
        "funcionarios": funcionarios_dashboard,
    }




@rh_router.get("/ponto/relatorio-mensal")
async def get_relatorio_ponto_mensal(mes: int, ano: int, funcionario_id: Optional[str] = None):
    """Obter relatório mensal de ponto com cálculo de horas extras e banco de horas"""
    
    JORNADA_SEG_SEX = 8 * 60 + 30
    JORNADA_SABADO = 4 * 60
    
    inicio_mes = f"{ano}-{mes:02d}-01"
    if mes == 12:
        fim_mes = f"{ano + 1}-01-01"
    else:
        fim_mes = f"{ano}-{mes + 1:02d}-01"
    
    query = {"data": {"$gte": inicio_mes, "$lt": fim_mes}}
    if funcionario_id:
        query["funcionario_id"] = funcionario_id
    
    funcionarios_ponto = {}
    async for reg in ponto_collection.find(query):
        fid = reg["funcionario_id"]
        if fid not in funcionarios_ponto:
            funcionarios_ponto[fid] = []
        funcionarios_ponto[fid].append(reg)
    
    relatorio = []
    for fid, registros in funcionarios_ponto.items():
        func = await funcionarios_collection.find_one({"id": fid})
        if not func:
            continue
        
        total_horas_trabalhadas = 0
        total_horas_previstas = 0
        total_atrasos = 0
        dias_trabalhados = 0
        dias_falta = 0
        
        for reg in registros:
            if not reg.get("entrada") or not reg.get("saida"):
                dias_falta += 1
                continue
            
            dias_trabalhados += 1
            
            try:
                data_reg = datetime.strptime(reg["data"], "%Y-%m-%d")
                dia_semana = data_reg.weekday()
            except:
                dia_semana = 0
            
            if dia_semana == 5:
                jornada_prevista = JORNADA_SABADO
            elif dia_semana == 6:
                jornada_prevista = 0
            else:
                jornada_prevista = JORNADA_SEG_SEX
            
            total_horas_previstas += jornada_prevista
            
            try:
                h_ent, m_ent = map(int, reg["entrada"].split(":"))
                h_sai, m_sai = map(int, reg["saida"].split(":"))
                
                minutos_trabalhados = (h_sai * 60 + m_sai) - (h_ent * 60 + m_ent)
                
                if reg.get("saida_almoco") and reg.get("retorno_almoco"):
                    h_sal, m_sal = map(int, reg["saida_almoco"].split(":"))
                    h_ret, m_ret = map(int, reg["retorno_almoco"].split(":"))
                    intervalo = (h_ret * 60 + m_ret) - (h_sal * 60 + m_sal)
                    minutos_trabalhados -= intervalo
                
                total_horas_trabalhadas += minutos_trabalhados
                
                if h_ent > 8 or (h_ent == 8 and m_ent > 0):
                    total_atrasos += (h_ent * 60 + m_ent) - (8 * 60)
            except:
                pass
        
        banco_horas = total_horas_trabalhadas - total_horas_previstas
        horas_extras = max(0, banco_horas)
        horas_devidas = abs(min(0, banco_horas))
        
        salario = func.get("salario", 0)
        valor_hora = salario / 220 if salario > 0 else 0
        valor_hora_extra = valor_hora * 1.5
        valor_horas_extras = (horas_extras / 60) * valor_hora_extra
        
        relatorio.append({
            "funcionario_id": fid,
            "nome": func.get("nome", ""),
            "cargo": func.get("cargo", ""),
            "dias_trabalhados": dias_trabalhados,
            "dias_falta": dias_falta,
            "horas_previstas": f"{total_horas_previstas // 60}h {total_horas_previstas % 60}min",
            "horas_trabalhadas": f"{total_horas_trabalhadas // 60}h {total_horas_trabalhadas % 60}min",
            "horas_extras": f"{horas_extras // 60}h {horas_extras % 60}min",
            "horas_devidas": f"{horas_devidas // 60}h {horas_devidas % 60}min",
            "banco_horas_minutos": banco_horas,
            "total_atrasos_minutos": total_atrasos,
            "total_atrasos": f"{total_atrasos // 60}h {total_atrasos % 60}min",
            "valor_hora": valor_hora,
            "valor_hora_extra": valor_hora_extra,
            "valor_horas_extras": valor_horas_extras
        })
    
    return {
        "mes": mes,
        "ano": ano,
        "funcionarios": relatorio,
        "total_funcionarios": len(relatorio)
    }


# ===== FOLHA DE PAGAMENTO =====
@rh_router.get("/folha-pagamento")
async def list_folha_pagamento(mes: int, ano: int):
    """Listar folhas de pagamento do mês"""
    folhas = []
    async for folha in folha_pagamento_collection.find({"mes": mes, "ano": ano}):
        folha["_id"] = str(folha["_id"])
        func = await funcionarios_collection.find_one({"id": folha["funcionario_id"]})
        folha["funcionario_nome"] = func["nome"] if func else "-"
        folha["funcionario_cargo"] = func.get("cargo", "-") if func else "-"
        folhas.append(folha)
    return folhas


@rh_router.post("/folha-pagamento")
async def create_folha_pagamento(data: FolhaCreate):
    """Criar folha de pagamento"""
    folha_doc = data.dict()
    folha_doc["id"] = str(uuid.uuid4())
    folha_doc["created_at"] = datetime.now().isoformat()
    
    await folha_pagamento_collection.insert_one(folha_doc)
    folha_doc["_id"] = str(folha_doc.get("_id", ""))
    return folha_doc


@rh_router.delete("/folha-pagamento/{folha_id}")
async def delete_folha_pagamento(folha_id: str):
    """Excluir folha de pagamento"""
    result = await folha_pagamento_collection.delete_one({"id": folha_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Folha não encontrada")
    return {"message": "Folha excluída"}


@rh_router.get("/folha-pagamento/{folha_id}/holerite")
async def gerar_holerite(folha_id: str):
    """Gerar PDF do holerite"""
    folha = await folha_pagamento_collection.find_one({"id": folha_id})
    if not folha:
        raise HTTPException(status_code=404, detail="Folha não encontrada")
    
    func = await funcionarios_collection.find_one({"id": folha["funcionario_id"]})
    if not func:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 2*cm, "HOLERITE DE PAGAMENTO")
    
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, height - 3*cm, f"Funcionário: {func['nome']}")
    c.drawString(2*cm, height - 3.5*cm, f"CPF: {func.get('cpf', '-')}")
    c.drawString(2*cm, height - 4*cm, f"Cargo: {func.get('cargo', '-')}")
    
    meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    c.drawString(12*cm, height - 3*cm, f"Competência: {meses[folha['mes']]}/{folha['ano']}")
    
    y = height - 5.5*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "PROVENTOS")
    y -= 0.6*cm
    c.setFont("Helvetica", 10)
    
    proventos = [
        ("Salário Base", folha.get('salario_base', 0)),
        ("Horas Extras", folha.get('horas_extras', 0) * folha.get('valor_hora_extra', 0)),
        ("Adicional Noturno", folha.get('adicional_noturno', 0)),
        ("Comissões", folha.get('comissoes', 0)),
    ]
    
    for desc, valor in proventos:
        if valor > 0:
            c.drawString(2*cm, y, desc)
            c.drawString(14*cm, y, f"R$ {valor:,.2f}")
            y -= 0.5*cm
    
    c.drawString(14*cm, y, f"R$ {folha.get('salario_bruto', 0):,.2f}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Total Proventos:")
    
    y -= 1*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "DESCONTOS")
    y -= 0.6*cm
    c.setFont("Helvetica", 10)
    
    descontos = [
        ("INSS", folha.get('inss', 0)),
        ("IRPF", folha.get('irpf', 0)),
        ("Vale Transporte", folha.get('vale_transporte', 0)),
        ("Vale Alimentação", folha.get('vale_alimentacao', 0)),
        ("Plano de Saúde", folha.get('plano_saude', 0)),
        ("Outros Descontos", folha.get('outros_descontos', 0)),
    ]
    
    for desc, valor in descontos:
        if valor > 0:
            c.drawString(2*cm, y, desc)
            c.drawString(14*cm, y, f"R$ {valor:,.2f}")
            y -= 0.5*cm
    
    c.drawString(14*cm, y, f"R$ {folha.get('total_descontos', 0):,.2f}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Total Descontos:")
    
    y -= 1.5*cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, f"SALÁRIO LÍQUIDO: R$ {folha.get('salario_liquido', 0):,.2f}")
    
    y -= 1*cm
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y, f"FGTS depositado: R$ {folha.get('fgts', 0):,.2f}")
    
    c.save()
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=holerite_{func['nome']}_{folha['mes']}_{folha['ano']}.pdf"}
    )


@rh_router.post("/folha-pagamento/gerar-contas-pagar")
async def gerar_contas_pagar_folha(mes: int = Body(...), ano: int = Body(...)):
    """Gerar contas a pagar a partir da folha de pagamento"""
    folhas = []
    async for folha in folha_pagamento_collection.find({"mes": mes, "ano": ano}):
        folhas.append(folha)
    
    if not folhas:
        raise HTTPException(status_code=404, detail="Nenhuma folha encontrada para este período")
    
    contas_criadas = []
    
    total_salarios = sum(f.get("salario_liquido", 0) for f in folhas)
    if total_salarios > 0:
        conta_salarios = {
            "id": str(uuid.uuid4()),
            "descricao": f"Folha de Pagamento - {mes:02d}/{ano}",
            "valor": total_salarios,
            "data_vencimento": f"{ano}-{mes:02d}-05",
            "categoria": "Salários",
            "status": "pendente",
            "origem": "rh",
            "created_at": datetime.now().isoformat()
        }
        await db.contas_pagar.insert_one(conta_salarios)
        contas_criadas.append(conta_salarios)
    
    total_inss = sum(f.get("inss", 0) for f in folhas)
    if total_inss > 0:
        conta_inss = {
            "id": str(uuid.uuid4()),
            "descricao": f"INSS - {mes:02d}/{ano}",
            "valor": total_inss,
            "data_vencimento": f"{ano}-{mes:02d}-20",
            "categoria": "Impostos",
            "status": "pendente",
            "origem": "rh",
            "created_at": datetime.now().isoformat()
        }
        await db.contas_pagar.insert_one(conta_inss)
        contas_criadas.append(conta_inss)
    
    total_fgts = sum(f.get("fgts", 0) for f in folhas)
    if total_fgts > 0:
        conta_fgts = {
            "id": str(uuid.uuid4()),
            "descricao": f"FGTS - {mes:02d}/{ano}",
            "valor": total_fgts,
            "data_vencimento": f"{ano}-{mes:02d}-07",
            "categoria": "FGTS",
            "status": "pendente",
            "origem": "rh",
            "created_at": datetime.now().isoformat()
        }
        await db.contas_pagar.insert_one(conta_fgts)
        contas_criadas.append(conta_fgts)
    
    return {
        "message": f"{len(contas_criadas)} contas criadas",
        "contas": contas_criadas
    }


# ===== FÉRIAS =====
@rh_router.get("/ferias")
async def list_ferias(ano: int):
    """Listar férias do ano"""
    ferias_list = []
    async for f in ferias_collection.find({}):
        try:
            inicio = datetime.strptime(f["data_inicio"], "%Y-%m-%d")
            if inicio.year == ano:
                f["_id"] = str(f["_id"])
                ferias_list.append(f)
        except:
            pass
    return ferias_list


@rh_router.get("/ferias/alertas")
async def get_ferias_alertas():
    """Alertas de período aquisitivo"""
    alertas = []
    hoje = datetime.now()
    
    async for func in funcionarios_collection.find({"status": "ativo"}):
        if func.get("data_admissao"):
            try:
                data_adm = datetime.strptime(func["data_admissao"], "%Y-%m-%d")
                meses_trabalhados = (hoje.year - data_adm.year) * 12 + (hoje.month - data_adm.month)
                
                if meses_trabalhados >= 11:
                    ultima_ferias = await ferias_collection.find_one(
                        {"funcionario_id": func["id"]},
                        sort=[("data_inicio", -1)]
                    )
                    
                    if not ultima_ferias or (hoje - datetime.strptime(ultima_ferias["data_inicio"], "%Y-%m-%d")).days > 365:
                        alertas.append({
                            "funcionario_id": func["id"],
                            "funcionario_nome": func["nome"],
                            "mensagem": f"Completou {meses_trabalhados} meses - programar férias"
                        })
            except:
                pass
    
    return alertas


@rh_router.post("/ferias")
async def create_ferias(data: FeriasCreate):
    """Agendar férias"""
    ferias_doc = data.dict()
    ferias_doc["id"] = str(uuid.uuid4())
    ferias_doc["created_at"] = datetime.now().isoformat()
    
    await ferias_collection.insert_one(ferias_doc)
    ferias_doc["_id"] = str(ferias_doc.get("_id", ""))
    return ferias_doc


@rh_router.put("/ferias/{ferias_id}")
async def update_ferias(ferias_id: str, data: FeriasCreate):
    """Atualizar férias"""
    existing = await ferias_collection.find_one({"id": ferias_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Férias não encontradas")
    
    update_data = data.dict()
    update_data["updated_at"] = datetime.now().isoformat()
    
    await ferias_collection.update_one({"id": ferias_id}, {"$set": update_data})
    return {"message": "Férias atualizadas com sucesso"}


@rh_router.delete("/ferias/{ferias_id}")
async def delete_ferias(ferias_id: str):
    """Excluir férias"""
    result = await ferias_collection.delete_one({"id": ferias_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Férias não encontradas")
    return {"message": "Férias excluídas com sucesso"}


# ===== EPI =====
@rh_router.get("/epi/cbo/buscar")
async def buscar_cbo(q: str):
    """Buscar ocupação por código CBO ou nome"""
    resultados = []
    q_lower = q.lower().strip()
    q_normalized = q_lower.replace("-", "").replace(".", "")
    
    # Primeiro: busca exata por código CBO
    for codigo, info in CBO_DATABASE.items():
        codigo_normalized = codigo.lower().replace("-", "").replace(".", "")
        if q_normalized == codigo_normalized or q_lower == codigo.lower():
            resultados.append({
                "codigo": codigo,
                "ocupacao": info["titulo"],
                "familia": info["familia"],
                "descricao": f"Família: {info['familia']}",
                "match_type": "exact"
            })
    
    # Se encontrou correspondência exata, retorna apenas ela
    if resultados:
        return resultados
    
    # Segundo: busca por código parcial (começa com)
    for codigo, info in CBO_DATABASE.items():
        codigo_normalized = codigo.lower().replace("-", "").replace(".", "")
        if codigo_normalized.startswith(q_normalized) or codigo.lower().startswith(q_lower):
            resultados.append({
                "codigo": codigo,
                "ocupacao": info["titulo"],
                "familia": info["familia"],
                "descricao": f"Família: {info['familia']}",
                "match_type": "partial_code"
            })
    
    # Se encontrou por código parcial, retorna
    if resultados:
        return resultados[:10]
    
    # Terceiro: busca por nome da ocupação ou sinônimos
    for codigo, info in CBO_DATABASE.items():
        if (q_lower in info["titulo"].lower() or
            any(q_lower in s.lower() for s in info.get("sinonimos", []))):
            resultados.append({
                "codigo": codigo,
                "ocupacao": info["titulo"],
                "familia": info["familia"],
                "descricao": f"Família: {info['familia']}",
                "match_type": "name"
            })
    
    return resultados[:10]


@rh_router.post("/epi/consultar-epis-cbo")
async def consultar_epis_por_cbo(codigo_cbo: str = Body(...), ocupacao: str = Body(...)):
    """Consultar EPIs recomendados por código CBO - SEMPRE usa IA Gemini para precisão"""
    
    # Normalizar código CBO
    codigo_cbo = codigo_cbo.strip()
    
    # SEMPRE consultar a IA Gemini com o código CBO para garantir precisão
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        prompt = f"""Você é um especialista em segurança do trabalho no Brasil, com profundo conhecimento da Classificação Brasileira de Ocupações (CBO).

CÓDIGO CBO INFORMADO: {codigo_cbo}
OCUPAÇÃO: {ocupacao}

IMPORTANTE: Primeiro, verifique se o código CBO {codigo_cbo} corresponde EXATAMENTE à ocupação "{ocupacao}". 
Se houver divergência, informe a ocupação correta para este código CBO.

Com base no código CBO {codigo_cbo}, liste TODOS os Equipamentos de Proteção Individual (EPIs) obrigatórios e recomendados conforme as Normas Regulamentadoras (NRs) brasileiras.

Para cada EPI, forneça:
1. Nome do EPI
2. CA (Certificado de Aprovação) - coloque "A definir" se não souber o número específico
3. Validade média em meses
4. Prioridade: "Alta" (obrigatório por NR), "Média" (recomendado), "Baixa" (opcional)

Também forneça um mapa de risco com os principais riscos da ocupação segundo a NR correspondente.

Responda APENAS em formato JSON válido:
{{
  "codigo_cbo": "{codigo_cbo}",
  "ocupacao_oficial": "Nome oficial da ocupação segundo CBO",
  "epis": [
    {{"nome": "Nome do EPI", "ca": "A definir", "validade_meses": 36, "prioridade": "Alta"}}
  ],
  "mapa_risco": [
    {{"risco": "Descrição do risco", "prioridade": "Alta", "epi_recomendado": "Nome do EPI"}}
  ]
}}"""
        
        llm = LlmChat(
            api_key=os.environ.get("EMERGENT_LLM_KEY"),
            session_id=f"epi_cbo_{codigo_cbo}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            system_message="Você é especialista em segurança do trabalho, CBO e EPIs no Brasil. Sempre responda com precisão baseado no código CBO informado."
        ).with_model("gemini", "gemini-2.5-flash")
        
        response_text = await llm.send_message(UserMessage(text=prompt))
        
        if hasattr(response_text, 'content'):
            response_text = response_text.content
        
        response_text = str(response_text).strip()
        
        # Limpar resposta para extrair JSON
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```json"):
                    in_json = True
                    continue
                elif line.startswith("```"):
                    in_json = False
                    continue
                elif in_json:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)
        
        result = json.loads(response_text)
        result["fonte"] = "IA_GEMINI"
        result["codigo_consultado"] = codigo_cbo
        return result
        
    except Exception as e:
        # Fallback: usar base local se IA falhar
        categoria = get_categoria_epi(codigo_cbo)
        epis_base = EPI_POR_CARGO.get(categoria, EPI_POR_CARGO["construcao_civil"])
        
        EPI_RISK_MAP = {
            "Capacete": {"risco": "Queda de objetos/impactos na cabeça", "prioridade": "Alta"},
            "Óculos de proteção": {"risco": "Projeção de partículas", "prioridade": "Alta"},
            "Luvas de proteção": {"risco": "Cortes e abrasões", "prioridade": "Alta"},
            "Botina de segurança": {"risco": "Queda de objetos nos pés", "prioridade": "Alta"},
            "Protetor auricular": {"risco": "Ruído excessivo", "prioridade": "Média"},
            "Cinto de segurança": {"risco": "Queda de altura", "prioridade": "Alta"},
            "Capacete classe B": {"risco": "Choque elétrico e impactos", "prioridade": "Alta"},
            "Luvas isolantes": {"risco": "Choque elétrico", "prioridade": "Alta"},
            "Botina isolante": {"risco": "Choque elétrico pelos pés", "prioridade": "Alta"},
            "Vestimenta antichama": {"risco": "Arco elétrico/chamas", "prioridade": "Alta"},
            "Detector de tensão": {"risco": "Trabalho com energia viva", "prioridade": "Alta"},
            "Máscara de solda": {"risco": "Radiação e respingos", "prioridade": "Alta"},
            "Avental de raspa": {"risco": "Respingos de solda", "prioridade": "Alta"},
            "Luvas de raspa": {"risco": "Queimaduras nas mãos", "prioridade": "Alta"},
        }
        
        epis = []
        mapa_risco = []
        
        for epi in epis_base:
            epis.append({
                "nome": epi["nome"],
                "ca": epi.get("ca", "A definir"),
                "validade_meses": epi.get("validade_meses", 12),
                "prioridade": epi.get("prioridade", "Alta")
            })
            
            if epi["nome"] in EPI_RISK_MAP:
                risk_info = EPI_RISK_MAP[epi["nome"]]
                mapa_risco.append({
                    "risco": risk_info["risco"],
                    "prioridade": risk_info["prioridade"],
                    "epi_recomendado": epi["nome"]
                })
        
        return {
            "codigo_cbo": codigo_cbo,
            "ocupacao_oficial": ocupacao,
            "epis": epis,
            "mapa_risco": mapa_risco,
            "fonte": "FALLBACK_LOCAL",
            "erro": str(e)
        }


@rh_router.get("/epi/fichas")
async def list_fichas_epi(funcionario_id: Optional[str] = None):
    """Listar fichas de EPI"""
    query = {}
    if funcionario_id:
        query["funcionario_id"] = funcionario_id
    
    fichas = []
    async for ficha in epi_fichas_collection.find(query):
        ficha["_id"] = str(ficha["_id"])
        func = await funcionarios_collection.find_one({"id": ficha["funcionario_id"]})
        ficha["funcionario_nome"] = func["nome"] if func else "-"
        fichas.append(ficha)
    
    return fichas


@rh_router.post("/epi/fichas")
async def create_ficha_epi(data: FichaEPICreate):
    """Criar ficha de EPI"""
    ficha_doc = data.dict()
    ficha_doc["id"] = str(uuid.uuid4())
    ficha_doc["created_at"] = datetime.now().isoformat()
    
    await epi_fichas_collection.insert_one(ficha_doc)
    ficha_doc["_id"] = str(ficha_doc.get("_id", ""))
    return ficha_doc


# ===== NOTIFICAÇÕES =====
@rh_router.get("/notificacoes")
async def get_rh_notificacoes():
    """Obter todas as notificações do RH"""
    hoje = datetime.now()
    mes_atual = hoje.month
    
    aniversariantes = []
    async for func in funcionarios_collection.find({"status": "ativo"}):
        if func.get("data_nascimento"):
            try:
                data_nasc = datetime.strptime(func["data_nascimento"], "%Y-%m-%d")
                if data_nasc.month == mes_atual:
                    idade = hoje.year - data_nasc.year
                    aniversariantes.append({
                        "nome": func["nome"],
                        "cargo": func.get("cargo", "-"),
                        "data_formatada": data_nasc.strftime("%d/%m"),
                        "idade": idade
                    })
            except:
                pass
    
    alertas_ferias = []
    funcionarios_sem_ferias = []
    async for func in funcionarios_collection.find({"status": "ativo"}):
        if func.get("data_admissao"):
            try:
                data_adm = datetime.strptime(func["data_admissao"], "%Y-%m-%d")
                meses_trabalhados = (hoje.year - data_adm.year) * 12 + (hoje.month - data_adm.month)
                
                ultima_ferias = await ferias_collection.find_one(
                    {"funcionario_id": func["id"]},
                    sort=[("data_inicio", -1)]
                )
                
                if meses_trabalhados >= 11 and meses_trabalhados <= 14:
                    alertas_ferias.append({
                        "nome": func["nome"],
                        "mensagem": f"Período aquisitivo completando"
                    })
                
                if meses_trabalhados >= 12:
                    if not ultima_ferias:
                        funcionarios_sem_ferias.append({
                            "nome": func["nome"],
                            "ultima_ferias": "Nunca tirou férias"
                        })
                    else:
                        ultima = datetime.strptime(ultima_ferias["data_inicio"], "%Y-%m-%d")
                        if (hoje - ultima).days > 365:
                            funcionarios_sem_ferias.append({
                                "nome": func["nome"],
                                "ultima_ferias": ultima.strftime("%d/%m/%Y")
                            })
            except:
                pass
    
    alertas_epi = []
    async for ficha in epi_fichas_collection.find({}):
        func = await funcionarios_collection.find_one({"id": ficha.get("funcionario_id")})
        if func and ficha.get("epis"):
            for epi in ficha["epis"]:
                if epi.get("validade"):
                    try:
                        validade = datetime.strptime(epi["validade"], "%Y-%m-%d")
                        dias_restantes = (validade - hoje).days
                        if 0 < dias_restantes <= 30:
                            alertas_epi.append({
                                "funcionario": func["nome"],
                                "epi": epi["nome"],
                                "dias_restantes": dias_restantes
                            })
                    except:
                        pass
    
    inconsistencias_ponto = []
    hoje_str = hoje.strftime("%Y-%m-%d")
    dia_semana = hoje.weekday()
    
    if dia_semana < 6:
        async for reg in ponto_collection.find({"data": hoje_str}):
            func = await funcionarios_collection.find_one({"id": reg.get("funcionario_id")})
            if func and reg.get("entrada"):
                try:
                    h, m = map(int, reg["entrada"].split(":"))
                    hora_limite = 8
                    minuto_limite = 15
                    
                    if h > hora_limite or (h == hora_limite and m > minuto_limite):
                        atraso = (h - 8) * 60 + m
                        inconsistencias_ponto.append({
                            "funcionario": func["nome"],
                            "tipo": "Atraso",
                            "detalhe": f"Entrada às {reg['entrada']} ({atraso} min de atraso)"
                        })
                except:
                    pass
    
    return {
        "aniversariantes": aniversariantes,
        "alertas_ferias": alertas_ferias,
        "funcionarios_sem_ferias": funcionarios_sem_ferias,
        "alertas_epi": alertas_epi,
        "alertas_atestados": [],
        "inconsistencias_ponto": inconsistencias_ponto
    }


@rh_router.get("/notificacoes/contagem")
async def get_rh_notificacoes_contagem():
    """Contagem de notificações para badge"""
    notifs = await get_rh_notificacoes()
    
    total = (
        len(notifs["alertas_ferias"]) +
        len(notifs["funcionarios_sem_ferias"]) +
        len(notifs["alertas_epi"]) +
        len(notifs["inconsistencias_ponto"])
    )
    
    urgentes = len(notifs["funcionarios_sem_ferias"]) + len([e for e in notifs["alertas_epi"] if e.get("dias_restantes", 30) <= 7])
    
    return {"total": total, "urgentes": urgentes}


# ===== CUSTOS =====
@rh_router.get("/custos")
async def get_custos_rh():
    """Obter custos detalhados de RH"""
    custos_funcionarios = []
    total_salarios = 0
    total_encargos = 0
    total_beneficios = 0
    total_epis = 0
    
    async for func in funcionarios_collection.find({"status": "ativo"}):
        salario = func.get("salario", 0)
        fgts = salario * (FGTS_ALIQUOTA / 100)
        inss_patronal = salario * (INSS_PATRONAL_ALIQUOTA / 100)
        
        beneficios = 150
        epis_custo = 50
        
        custo_total = salario + fgts + inss_patronal + beneficios + epis_custo
        custo_hora = custo_total / 220 if custo_total > 0 else 0
        
        total_salarios += salario
        total_encargos += fgts + inss_patronal
        total_beneficios += beneficios
        total_epis += epis_custo
        
        custos_funcionarios.append({
            "funcionario_id": func["id"],
            "nome": func["nome"],
            "cargo": func.get("cargo", "-"),
            "salario": salario,
            "fgts": fgts,
            "inss_patronal": inss_patronal,
            "beneficios": beneficios,
            "epis": epis_custo,
            "custo_total": custo_total,
            "custo_hora": custo_hora
        })
    
    return {
        "funcionarios": custos_funcionarios,
        "resumo": {
            "total_salarios": total_salarios,
            "total_encargos": total_encargos,
            "total_beneficios": total_beneficios,
            "total_epis": total_epis,
            "custo_total": total_salarios + total_encargos + total_beneficios + total_epis
        }
    }


@rh_router.post("/custos/simular-dissidio")
async def simular_dissidio(percentual: float = Body(..., embed=True)):
    """Simular impacto de dissídio na folha"""
    folha_atual = 0
    async for func in funcionarios_collection.find({"status": "ativo"}):
        salario = func.get("salario", 0)
        fgts = salario * (FGTS_ALIQUOTA / 100)
        inss_patronal = salario * (INSS_PATRONAL_ALIQUOTA / 100)
        folha_atual += salario + fgts + inss_patronal
    
    folha_nova = folha_atual * (1 + percentual / 100)
    impacto_mensal = folha_nova - folha_atual
    
    return {
        "percentual": percentual,
        "folha_atual": folha_atual,
        "folha_nova": folha_nova,
        "impacto_mensal": impacto_mensal,
        "impacto_anual": impacto_mensal * 12
    }


@rh_router.post("/custos/simular-rescisao")
async def simular_rescisao(funcionario_id: str = Body(..., embed=True)):
    """Simular provisão de rescisão"""
    func = await funcionarios_collection.find_one({"id": funcionario_id})
    if not func:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    salario = func.get("salario", 0)
    data_admissao = func.get("data_admissao", "")
    
    try:
        data_adm = datetime.strptime(data_admissao, "%Y-%m-%d")
        meses_trabalhados = (datetime.now().year - data_adm.year) * 12 + (datetime.now().month - data_adm.month)
    except:
        meses_trabalhados = 12
    
    saldo_salario = salario
    aviso_previo = salario + (salario / 30 * 3 * (meses_trabalhados // 12))
    ferias_proporcionais = (salario / 12) * (meses_trabalhados % 12) + (salario / 12 * (meses_trabalhados % 12) / 3)
    decimo_terceiro = (salario / 12) * (datetime.now().month)
    fgts_saldo = salario * (FGTS_ALIQUOTA / 100) * meses_trabalhados
    multa_fgts = fgts_saldo * 0.4
    
    total = saldo_salario + aviso_previo + ferias_proporcionais + decimo_terceiro + multa_fgts
    
    return {
        "funcionario": func["nome"],
        "meses_trabalhados": meses_trabalhados,
        "saldo_salario": saldo_salario,
        "aviso_previo": aviso_previo,
        "ferias_proporcionais": ferias_proporcionais,
        "decimo_terceiro": decimo_terceiro,
        "fgts_saldo": fgts_saldo,
        "multa_fgts": multa_fgts,
        "total": total
    }
