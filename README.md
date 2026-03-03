# 🏗️ CRA Construtora - Sistema de Gestão Empresarial (ERP)

Sistema completo de gestão empresarial desenvolvido para construtoras e empresas de locação de máquinas. Integra gestão de máquinas, manutenções, recursos humanos, financeiro, estoque e muito mais em uma única plataforma.

![React](https://img.shields.io/badge/React-18.x-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-47A248?logo=mongodb)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-38B2AC?logo=tailwindcss)

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Módulos do Sistema](#-módulos-do-sistema)
  - [Sistema de Gerenciamento](#1-sistema-de-gerenciamento)
  - [Sistema Administrativo/Financeiro](#2-sistema-administrativofinanceiro)
  - [Sistema de RH](#3-sistema-de-rh)
  - [Painel do Administrador](#4-painel-do-administrador)
- [Funcionalidades Avançadas](#-funcionalidades-avançadas)
- [Integrações](#-integrações)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Estrutura de Arquivos](#-estrutura-de-arquivos)
- [API Endpoints](#-api-endpoints)
- [Credenciais de Teste](#-credenciais-de-teste)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)

---

## 🎯 Visão Geral

O CRA Construtora ERP é uma solução completa para gestão empresarial que oferece:

- **Gestão de Frota e Máquinas**: Controle total sobre máquinas, manutenções preventivas e corretivas
- **Sistema Financeiro Completo**: Contas a pagar/receber, contas bancárias, plano de contas
- **Recursos Humanos**: Funcionários, ponto eletrônico, folha de pagamento, férias, EPIs
- **Controle de Estoque**: Peças, movimentações, alertas de estoque baixo
- **Gestão de Obras**: Projetos, cronogramas, custos
- **Importação de NF-e**: Integração direta com SEFAZ para importar notas fiscais
- **Chatbot com IA**: Assistente inteligente integrado ao sistema
- **Exportação Avançada**: PDF, Excel, OFX, recibos e duplicatas
- **Armazenamento de Arquivos**: Sistema completo com pastas, senhas e compartilhamento

---

## 🏛️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Gerenc. │ │ Admin.  │ │   RH    │ │  Painel │           │
│  │         │ │Financ.  │ │         │ │  Admin  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │           │           │           │                 │
│       └───────────┴───────────┴───────────┘                 │
│                          │                                   │
│              TailwindCSS + Shadcn/UI                        │
└──────────────────────────┼──────────────────────────────────┘
                           │ HTTP/REST
┌──────────────────────────┼──────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    API Router                         │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │   │
│  │  │  auth  │ │machines│ │  admin │ │   rh   │  ...   │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘        │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│               JWT Auth + Motor (Async MongoDB)              │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                     MongoDB Database                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │machines │ │  users  │ │contas_* │ │funciona.│  ...      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Módulos do Sistema

### 1. Sistema de Gerenciamento

O módulo de gerenciamento controla toda a operação de máquinas e equipamentos.

#### 🚜 Máquinas
- Cadastro completo com nome, marca, modelo, placa, ano
- **Categorias com cores**: Organize máquinas por tipo com indicadores visuais
- **Status de operação**: Pátio (amarelo), Operacional (verde), Manutenção (vermelho)
- **Chassi/Número de Série**: Identificação única do equipamento
- Histórico de manutenções, horímetro e combustível
- Vinculação de operador quando em operação

#### 🔧 Manutenções
- **Preventivas e Corretivas**: Classificação e acompanhamento
- **Integração com Estoque**: Selecione peças diretamente do estoque
- **Baixa automática**: Peças utilizadas são descontadas automaticamente
- **Cálculo de custos**: Peças + mão de obra = valor total automático
- Anexo de fotos e documentos
- Histórico completo por máquina

#### ⏱️ Horímetro
- Registro de horas de operação
- **Tipo de medição**: Horas (horímetro) ou Km (odômetro)
- Hora/Km inicial e final com cálculo automático
- Vinculação de operador (funcionários RH + cadastros financeiro)
- Atualização automática do horímetro da máquina

#### ⛽ Combustível
- **Veículos Tanque (Abastecedores)**: Cadastro de máquinas como tanque
- Barras de progresso visuais para Diesel, Óleo e Graxa
- **Registro de abastecimento**:
  - Tipo "Abastecedor" (entrada no tanque)
  - Tipo "Abastecido" (saída do tanque)
- **Desconto automático** do tanque em abastecimentos internos
- Alertas de combustível baixo (crítico <10%, baixo <25%)

#### 📦 Estoque
- Cadastro de itens com código, descrição, quantidade, preço
- **Quantidade mínima**: Alertas automáticos de estoque baixo
- **Vinculação a máquinas**: Associe peças a máquinas específicas
- Movimentações de entrada e saída com histórico
- Visualização expansível com máquinas associadas
- 4 badges por linha com modelo da máquina

#### 🚚 Frotas
- Agrupamento lógico de máquinas
- Vinculação de máquinas a frotas
- Filtros e relatórios por frota

#### 🏗️ Obras/Projetos
- Cadastro de obras com endereço e responsável
- Vinculação de máquinas à obra
- Acompanhamento de status (em andamento, concluída, pausada)
- Custos e cronograma

#### 🔔 Notificações
- **Manutenções preventivas** próximas ou vencidas
- **Troca de óleo**: Alertas por horas ou dias
- **Combustível baixo**: Crítico e baixo
- **Estoque baixo**: Itens abaixo do mínimo
- Badge com contador no menu

---

### 2. Sistema Administrativo/Financeiro

Controle financeiro completo da empresa.

#### 💰 Contas a Pagar
- CRUD completo com descrição, valor, vencimento
- **Máscaras monetárias**: Formatação automática R$ X.XXX,XX
- **Cálculo automático**: Valor Final = Valor - Desconto + Juros + Multa
- Vinculação a fornecedor, centro de custo, plano de contas
- **Quitação com conta bancária**: Atualiza saldo automaticamente
- Status: Pendente, Pago, Vencido
- Anexo de comprovantes

#### 💵 Contas a Receber
- Mesma estrutura de Contas a Pagar
- Vinculação a clientes
- **Quitação aumenta saldo** da conta bancária

#### 🏛️ Contas Bancárias
- Cadastro com banco, agência, conta, titular
- **Lista de bancos brasileiros** pré-cadastrada
- Tipos: Corrente, Poupança, Salário, Investimento
- Chave PIX e cor personalizada
- **Extrato bancário**: Movimentações de entrada e saída
- Exportação de extrato em PDF

#### 📊 Plano de Contas
- Estrutura hierárquica (Receitas/Despesas)
- Contas sintéticas e analíticas
- Vinculação de lançamentos

#### 🏢 Centros de Custo
- Departamentos e projetos
- Alocação de despesas
- Relatórios por centro

#### 👥 Cadastros
- **Tipos**: Cliente, Fornecedor, Cliente/Fornecedor, Transportador
- **Pessoa**: Física ou Jurídica
- **Consulta automática CNPJ**: Integração BrasilAPI
- **Consulta automática CEP**: Integração ViaCEP
- **Máscaras automáticas**: CPF, CNPJ, CEP, Telefone
- Limite de crédito e observações

#### 🚜 Aluguéis de Máquinas
- Locação de máquinas com período
- Valor do aluguel + caução
- **Integração com status**: Ao criar aluguel, máquina fica "Operacional"
- Finalização reverte status para "Pátio"
- Vinculação de operador no início

#### 🏠 Imóveis para Locação
- Cadastro completo do imóvel (tipo, área, quartos, vagas)
- Dados do inquilino e contrato
- Valores: Aluguel, condomínio, IPTU, caução
- **Geração automática** de conta a receber mensal
- Anexo de contrato

#### 💳 Formas de Pagamento
- Cadastro de formas (Dinheiro, PIX, Cartão, Boleto, etc.)
- Vinculação em lançamentos

#### 📥 Importação de NF-e
- **Integração direta com SEFAZ** via certificado A1
- Cadastro de múltiplos CNPJs
- Configuração: UF, Ambiente (Produção/Homologação)
- **Limite de 3 consultas por dia** por empresa
- **Cronômetro de bloqueio** (1 hora) quando SEFAZ retorna erro 656
- Visualização completa da NF-e (emitente, itens, valores)
- **Criação automática de Conta a Pagar** a partir da NF-e
- Status: Nova, Processada, Ignorada

#### 📤 Exportação
- **Formatos**: PDF, Excel, OFX
- **Individual**: Exportar item específico
- **Múltipla**: Selecionar vários itens
- **Combinada**: Categorias em um único PDF
- **Recibos e Duplicatas**: Documentos formais
- **Extrato Bancário**: Por conta

---

### 3. Sistema de RH

Gestão completa de recursos humanos.

#### 👤 Funcionários
- Cadastro completo: dados pessoais, documentos, endereço
- **Auto-preenchimento por CEP** (ViaCEP)
- Dados profissionais: cargo, função, departamento, salário
- **Regimes**: CLT, PJ, Contrato, Estágio, Prestador
- **Status**: Ativo, Férias, Afastado, Desligado
- **Anexos**: Contrato, fotos, documentos com visualização inline

#### ⏰ Ponto Eletrônico
- Registro: entrada, saída almoço, retorno, saída
- **Jornada configurada**:
  - Seg-Sex: 08:00-11:30 / 13:30-18:00
  - Sábado: 08:00-12:00
- Cálculo automático de horas trabalhadas
- Identificação de atrasos e saídas antecipadas
- **Registro rápido**: Um clique para entrada/saída
- **Relatório mensal**: Banco de horas, valor de horas extras
- Resumo do dia: Presentes, Ausentes, Atrasados

#### 💵 Folha de Pagamento
- **Tabelas atualizadas 2025**: INSS e IRPF
- **INSS progressivo**: 7.5% a 14%
- **IRPF com deduções**: 0% a 27.5%
- **FGTS**: 8% automático
- **Proventos**: Salário base, horas extras, adicional noturno, comissões
- **Descontos**: VT, VA, plano de saúde
- **Holerite PDF**: Geração automática com layout profissional
- **Geração de contas a pagar**: Salários, INSS, FGTS

#### 🏖️ Férias
- **Calendário anual**: Visualização de 12 meses
- Férias destacadas em azul
- **Abono pecuniário**: Venda de até 10 dias
- **Alertas**: Período aquisitivo vencendo
- **Status**: Agendado, Em Férias, Concluído
- Navegação por ano

#### 🦺 Gestão de EPI/EPC
- Cadastro de cargos
- **Consulta de EPIs por CBO**: Integração com IA Gemini
- **Mapa de risco**: Alta (vermelho), Média (amarelo), Baixa (verde)
- Ficha de EPI digital com controle de validade
- **Exportação PDF**: Ficha de EPI e Termo de Responsabilidade
- Alertas de EPIs vencendo (30 dias)

#### 📊 Gestão de Custos
- **Custo real por funcionário**:
  - Salário + FGTS (8%) + INSS Patronal (20%)
  - Benefícios + EPIs
- **Custo/hora**: Dividido por 220h CLT
- **Simulação de dissídio**: Impacto mensal e anual
- **Provisão de rescisão**:
  - Saldo salário, aviso prévio
  - Férias proporcionais, 13º proporcional
  - FGTS + multa 40%

#### 🔔 Notificações RH
- Aniversariantes do mês
- Alertas de férias (período aquisitivo)
- EPIs próximos do vencimento
- Inconsistências de ponto (atrasos)
- Badge com contador

---

### 4. Painel do Administrador

Controle total do sistema.

#### 👥 Gestão de Usuários
- Criar, editar, excluir usuários
- Atribuição de cargos/permissões
- **Roles disponíveis**:
  - `gerenciamento` - Acesso ao sistema de gerenciamento
  - `administrativo` - Acesso ao sistema financeiro
  - `rh` - Acesso ao sistema de RH
  - `ambos` - Gerenciamento + Administrativo
  - `ambos_rh` - Gerenciamento + Administrativo + RH
  - `gerenciamento_rh`, `administrativo_rh`
  - `admin` - Acesso total
  - `programador` - Acesso total (badge azul)

#### 📊 Auditoria
- Log de todas as ações do sistema
- Usuário, ação, entidade, data/hora
- Filtros por módulo e período

#### 🗄️ Banco de Dados
- Visualização de estatísticas
- Contagem de documentos por coleção
- Monitoramento de uso

---

## ⭐ Funcionalidades Avançadas

### 🤖 Chatbot com IA (Gemini)
- Assistente inteligente integrado
- Consultas sobre máquinas, manutenções, financeiro
- **Anexo de arquivos**: PDFs, Word, Excel, imagens
- **Extração automática** de conteúdo para análise
- Sugestão de EPIs por CBO

### 📁 Sistema de Armazenamento
- Gerenciador de arquivos completo
- Criação de pastas com/sem senha
- Upload de arquivos com drag-and-drop
- **Seleção múltipla**: Mover, copiar, excluir
- Preview de Word, Excel, PDF, imagens
- Lixeira com restauração

### 📊 Dashboard com Expansão
- Badge de Total de Máquinas clicável
- **Expande para mostrar** máquinas por categoria
- Sub-badges coloridos por categoria
- Clique redireciona para página filtrada

### 🎨 Formatação Automática
- **Máscaras monetárias**: R$ X.XXX,XX
- **CPF**: 000.000.000-00
- **CNPJ**: 00.000.000/0000-00
- **CEP**: 00000-000
- **Telefone**: (00) 00000-0000

---

## 🔗 Integrações

| Serviço | Uso |
|---------|-----|
| **Gemini AI** | Chatbot, sugestão de EPIs por CBO |
| **BrasilAPI** | Consulta automática de CNPJ |
| **ViaCEP** | Auto-preenchimento de endereço por CEP |
| **SEFAZ** | Importação de NF-e via certificado A1 |
| **PyNFe** | Comunicação com webservice NFeDistribuicaoDFe |

---

## 🚀 Instalação e Configuração

### Pré-requisitos
- Node.js 18+
- Python 3.11+
- MongoDB 6.0+

### Backend
```bash
cd backend
pip install -r requirements.txt
# Configurar variáveis em .env
# MONGO_URL=mongodb://localhost:27017
# DB_NAME=cra_db
# SECRET_KEY=sua_chave_secreta
# EMERGENT_API_KEY=sua_chave_gemini
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend
```bash
cd frontend
yarn install
# Configurar variáveis em .env
# REACT_APP_BACKEND_URL=http://localhost:8001
yarn start
```

---

## 📁 Estrutura de Arquivos

```
/app
├── backend/
│   ├── server.py           # Servidor principal FastAPI
│   ├── requirements.txt    # Dependências Python
│   ├── routes/             # Módulos de rotas
│   │   ├── auth.py         # Autenticação
│   │   ├── machines.py     # Máquinas e manutenções
│   │   ├── admin.py        # Financeiro
│   │   ├── rh.py           # Recursos Humanos
│   │   ├── stock.py        # Estoque
│   │   ├── storage.py      # Armazenamento
│   │   ├── exports.py      # Exportação PDF/Excel
│   │   ├── chatbot.py      # IA Gemini
│   │   ├── obras.py        # Obras/Projetos
│   │   └── categories.py   # Categorias
│   ├── core/
│   │   ├── database.py     # Configuração MongoDB
│   │   └── security.py     # JWT e bcrypt
│   └── tests/              # Testes automatizados
│
├── frontend/
│   ├── src/
│   │   ├── App.js          # Rotas principais
│   │   ├── pages/          # Páginas
│   │   │   ├── admin/      # Sistema Financeiro
│   │   │   ├── rh/         # Sistema RH
│   │   │   └── *.jsx       # Gerenciamento
│   │   ├── components/     # Componentes reutilizáveis
│   │   │   ├── ui/         # Shadcn/UI
│   │   │   └── *.jsx
│   │   └── utils/
│   │       └── masks.js    # Funções de formatação
│   └── package.json
│
└── memory/
    └── PRD.md              # Documentação do projeto
```

---

## 🔌 API Endpoints

### Autenticação
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/auth/register` | Registrar usuário |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Dados do usuário logado |

### Máquinas
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/machines` | Listar máquinas |
| POST | `/api/machines` | Criar máquina |
| GET | `/api/machines/{id}` | Detalhes da máquina |
| PUT | `/api/machines/{id}` | Atualizar máquina |
| DELETE | `/api/machines/{id}` | Excluir máquina |
| PATCH | `/api/machines/{id}/status` | Alterar status |

### Manutenções
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/maintenances` | Listar manutenções |
| POST | `/api/maintenances` | Criar manutenção |
| GET | `/api/maintenances/{id}` | Detalhes |
| PUT | `/api/maintenances/{id}` | Atualizar |
| DELETE | `/api/maintenances/{id}` | Excluir |

### Financeiro
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/admin/contas-pagar` | Contas a pagar |
| GET | `/api/admin/contas-receber` | Contas a receber |
| GET | `/api/admin/cadastros` | Cadastros |
| GET | `/api/admin/contas-bancarias` | Contas bancárias |
| GET | `/api/admin/plano-contas` | Plano de contas |
| GET | `/api/admin/centros-custo` | Centros de custo |
| GET | `/api/admin/alugueis` | Aluguéis |
| GET | `/api/admin/imoveis` | Imóveis |

### RH
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/rh/funcionarios` | Funcionários |
| GET | `/api/rh/ponto` | Registros de ponto |
| GET | `/api/rh/folha` | Folhas de pagamento |
| GET | `/api/rh/ferias` | Férias |
| GET | `/api/rh/cargos` | Cargos |
| GET | `/api/rh/epi-fichas` | Fichas de EPI |

### NF-e
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/nfe/certificados` | Listar certificados |
| POST | `/api/nfe/certificados` | Cadastrar certificado |
| POST | `/api/nfe/importar/{id}` | Importar NF-e da SEFAZ |
| GET | `/api/nfe/importadas` | NF-e importadas |
| POST | `/api/nfe/importadas/{id}/criar-conta-pagar` | Criar conta a pagar |

### Exportação
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/export/pdf/{category}` | Exportar PDF |
| GET | `/api/export/excel/{category}` | Exportar Excel |
| GET | `/api/export/recibo/{cat}/{id}` | Gerar recibo |
| GET | `/api/export/duplicata/{cat}/{id}` | Gerar duplicata |
| GET | `/api/export/extrato-bancario/{id}` | Extrato bancário |

---

## 🔑 Credenciais de Teste

```
Email: test@test.com
Senha: password
Role: admin
```

---

## 🛠️ Tecnologias Utilizadas

### Frontend
- **React 18** - Framework UI
- **TailwindCSS 3** - Estilização
- **Shadcn/UI** - Componentes
- **React Router 6** - Roteamento
- **Axios** - HTTP Client
- **Sonner** - Notificações toast
- **Lucide React** - Ícones

### Backend
- **FastAPI** - Framework Python
- **Motor** - MongoDB async driver
- **Pydantic** - Validação de dados
- **PyJWT** - Autenticação JWT
- **bcrypt** - Hash de senhas
- **PyNFe** - Comunicação SEFAZ
- **ReportLab** - Geração de PDFs
- **OpenPyXL** - Geração de Excel
- **python-docx** - Leitura de Word
- **PyPDF2** - Leitura de PDFs

### Banco de Dados
- **MongoDB 6.0+** - NoSQL Document Store

### Integrações
- **Google Gemini AI** - Chatbot e sugestões
- **BrasilAPI** - Consulta CNPJ
- **ViaCEP** - Consulta CEP
- **SEFAZ** - NF-e

---

## 📄 Licença

Este projeto é proprietário da CRA Construtora.

---

## 👥 Contato

Para suporte ou dúvidas, entre em contato com a equipe de desenvolvimento.

---

**Desenvolvido com ❤️ para CRA Construtora**
