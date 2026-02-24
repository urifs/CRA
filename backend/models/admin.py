from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# ============ ADMIN/FINANCIAL MODELS ============

class CadastroCreate(BaseModel):
    tipo: str  # "cliente", "fornecedor", "funcionario"
    nome: str
    documento: Optional[str] = ""
    telefone: Optional[str] = ""
    email: Optional[str] = ""
    endereco: Optional[str] = ""
    observacoes: Optional[str] = ""

class CadastroResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tipo: str
    nome: str
    documento: str
    telefone: str
    email: str
    endereco: str
    observacoes: str
    ativo: bool
    created_at: str

class ProdutoCreate(BaseModel):
    nome: str
    codigo: Optional[str] = ""
    unidade: Optional[str] = "UN"
    preco_custo: Optional[float] = 0
    preco_venda: Optional[float] = 0
    estoque_minimo: Optional[int] = 0
    categoria: Optional[str] = ""
    observacoes: Optional[str] = ""

class ProdutoResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nome: str
    codigo: str
    unidade: str
    preco_custo: float
    preco_venda: float
    estoque_minimo: int
    categoria: str
    observacoes: str
    ativo: bool
    created_at: str

class ContaPagarCreate(BaseModel):
    descricao: str
    valor: float
    data_vencimento: str
    fornecedor_id: Optional[str] = None
    categoria: Optional[str] = ""
    centro_custo: Optional[str] = ""
    forma_pagamento: Optional[str] = ""
    observacoes: Optional[str] = ""
    parcela_atual: Optional[int] = 1
    total_parcelas: Optional[int] = 1

class ContaPagarResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    descricao: str
    valor: float
    data_vencimento: str
    fornecedor_id: Optional[str] = None
    fornecedor_nome: Optional[str] = ""
    categoria: str
    centro_custo: str
    forma_pagamento: str
    observacoes: str
    status: str
    data_pagamento: Optional[str] = None
    parcela_atual: int
    total_parcelas: int
    attachments: List[str] = []
    created_at: str

class ContaReceberCreate(BaseModel):
    descricao: str
    valor: float
    data_vencimento: str
    cliente_id: Optional[str] = None
    categoria: Optional[str] = ""
    centro_custo: Optional[str] = ""
    forma_pagamento: Optional[str] = ""
    observacoes: Optional[str] = ""
    parcela_atual: Optional[int] = 1
    total_parcelas: Optional[int] = 1

class ContaReceberResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    descricao: str
    valor: float
    data_vencimento: str
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = ""
    categoria: str
    centro_custo: str
    forma_pagamento: str
    observacoes: str
    status: str
    data_recebimento: Optional[str] = None
    parcela_atual: int
    total_parcelas: int
    attachments: List[str] = []
    created_at: str

class OrdemServicoCreate(BaseModel):
    numero: Optional[str] = ""
    cliente_id: Optional[str] = None
    descricao: str
    valor_total: Optional[float] = 0
    data_abertura: Optional[str] = None
    data_previsao: Optional[str] = None
    observacoes: Optional[str] = ""
    itens: Optional[List[dict]] = []

class OrdemServicoResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    numero: str
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = ""
    descricao: str
    valor_total: float
    data_abertura: str
    data_previsao: Optional[str] = None
    data_conclusao: Optional[str] = None
    status: str
    observacoes: str
    itens: List[dict]
    created_at: str

class PlanoContasCreate(BaseModel):
    codigo: str
    nome: str
    tipo: str  # "receita", "despesa"
    pai_id: Optional[str] = None

class PlanoContasResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    codigo: str
    nome: str
    tipo: str
    pai_id: Optional[str] = None
    ativo: bool
    created_at: str

class CentroCustoCreate(BaseModel):
    codigo: str
    nome: str
    responsavel: Optional[str] = ""

class CentroCustoResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    codigo: str
    nome: str
    responsavel: str
    ativo: bool
    created_at: str

class FormaPagamentoCreate(BaseModel):
    nome: str
    taxa: Optional[float] = 0
    prazo_dias: Optional[int] = 0

class FormaPagamentoResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nome: str
    taxa: float
    prazo_dias: int
    ativo: bool
    created_at: str

class AluguelCreate(BaseModel):
    maquina_id: str
    cliente_id: Optional[str] = None
    cliente_nome: Optional[str] = ""
    valor_diaria: float
    data_inicio: str
    data_fim_prevista: Optional[str] = None
    observacoes: Optional[str] = ""

class AluguelResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    maquina_id: str
    maquina_nome: Optional[str] = ""
    maquina_placa: Optional[str] = ""
    cliente_id: Optional[str] = None
    cliente_nome: str
    valor_diaria: float
    data_inicio: str
    data_fim_prevista: Optional[str] = None
    data_fim_real: Optional[str] = None
    status: str
    valor_total: Optional[float] = None
    observacoes: str
    created_at: str
