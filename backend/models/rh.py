"""
RH Models - Pydantic models for Human Resources module
"""
from pydantic import BaseModel
from typing import Optional, List


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
