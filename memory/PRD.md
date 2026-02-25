# CRA Construtora - Sistema de Gestão Empresarial

## Problema Original
Sistema de gerenciamento de máquinas (tratores e caminhões) para registro de manutenções, expandido para incluir:
- Cadastro de máquinas com placa
- Fichas de manutenção (peça, data de troca, valor, tipo preventiva/corretiva)
- Anexar fotos nas fichas
- Histórico completo por máquina
- Controle de estoque de peças
- Sistema de troca de óleo com notificações
- Plano de Obras
- Sistema Compartilhado com Auditoria
- **Módulo Administrativo** (financeiro, fornecedores, produtos, OS, NF-e, aluguéis, notificações)
- **Painel Administrativo** (gestão de usuários e auditoria)
- **Sistema de Medições de Máquinas** (horímetro, km, combustível, produção)
- **Sistema de Armazenamento** (estilo Google Drive)

## Paleta de Cores (Atualizada 24/02/2026)
- **Vermelho**: #E31A1A (cor primária, botões de ação, links)
- **Amarelo**: #D4A000 (cor secundária escurecida, módulo administrativo) ← ATUALIZADO
- **Preto**: #000000 (sidebars, fundos de login/seleção)
- **Branco**: #FFFFFF (fundos de conteúdo principal)

## Arquitetura Atual

### Backend (FastAPI + MongoDB)
- **Auth**: JWT com bcrypt
- **Collections**: users, categories, machines, maintenances, stock_items, stock_movements, stock_categories, usage_logs, obras, audit_logs, contas_pagar, contas_receber, cadastros, produtos_admin, ordens_servico, plano_contas, centros_custo, formas_pagamento, **alugueis**, **medicoes**, **storage_trash**
- **Sistema Compartilhado**: Dados globais com auditoria
- **Painel Admin**: Endpoints para gestão de usuários e auditoria

### Frontend (React + Shadcn UI)
- **Quatro Módulos**:
  1. **Gerenciamento** (vermelho #E31A1A): Máquinas, Manutenções, Estoque, Obras, Medições
  2. **Administrativo** (amarelo #FFC232): Financeiro, Fornecedores, Produtos, OS, NF-e, Aluguéis, Notificações
  3. **Painel Administrativo** (vermelho #E31A1A): Gestão de Usuários, Auditoria, Criação de Contas
  4. **Armazenamento** (fundo escuro): Gerenciador de arquivos estilo Google Drive
- **PWA**: Instalável em dispositivos móveis (Service Worker desativado para debug)
- **Design Responsivo**: Navegação inferior no mobile

## O Que Foi Implementado

### Sistema de Medições de Máquinas ✅ (25/02/2026)
- [x] Página dedicada `/obras/:obraId/medicoes`
- [x] Registro de medições: Horímetro, Km, Combustível, Produção, Outro
- [x] Valor anterior preenchido automaticamente
- [x] Cálculo automático de diferença
- [x] Filtros por máquina, tipo, data
- [x] Resumo consolidado por máquina
- [x] Cards de estatísticas (horas totais, km totais)
- [x] Botão de acesso na página de detalhes da obra

### Filtros no Dashboard Financeiro ✅ (25/02/2026)
- [x] Pesquisa por descrição
- [x] Filtro por Centro de Custo
- [x] Filtro por Plano de Contas
- [x] Filtro por Status (Pendente, Vencido, Pago)
- [x] Lista de contas com indicador visual de vencimento

### Textos em Português no Painel Admin ✅ (25/02/2026)
- [x] Corrigido abreviações em inglês (Users→Usuários, Audit→Auditoria, DB→Banco)

### Visualização de Arquivos no Armazenamento ✅ (25/02/2026)
- [x] Clique simples em imagens/PDFs abre preview
- [x] Indicador "Clique para visualizar" em arquivos suportados
- [x] Modal de preview com opção de download

### Anexos em Transações Financeiras ✅ (24/02/2026)
- [x] Componente reutilizável AttachmentsSection
- [x] Upload de imagens (PNG, JPG, GIF, WebP) e PDFs
- [x] Limite de 10MB por arquivo
- [x] Visualização de imagens inline, download de PDFs
- [x] Exclusão de anexos com confirmação
- [x] Integrado em: Contas a Pagar, Contas a Receber
- [x] Auditoria de uploads e exclusões

### Melhorias na Tela de Seleção de Sistema ✅ (24/02/2026)
- [x] Botão "Sair da conta" para fazer logout
- [x] Painel Administrativo visível para todos os usuários
- [x] Acesso ao Painel Admin bloqueado para não-administradores (com mensagem de erro)

### Exportação de Relatórios PDF ✅ (24/02/2026)
- [x] Página de exportação redesenhada com categorias expansíveis
- [x] **Gerenciamento (21 opções)**:
  - Máquinas: Lista completa, Operacionais, Em Manutenção, Categorias
  - Manutenções: Todas, Preventivas, Corretivas, Trocas de Óleo
  - Estoque: Itens, Estoque Baixo, Categorias, Movimentações (entrada/saída)
  - Obras: Todas, Em Andamento, Concluídas, Pausadas
  - Registros de Uso, Usuários, Auditoria
- [x] **Administrativo (27 opções)**:
  - Contas a Pagar: Todas, Pendentes, Quitadas, Vencidas
  - Contas a Receber: Todas, Pendentes, Recebidas, Vencidas
  - Cadastros: Todos, Clientes, Fornecedores
  - Ordens de Serviço: Todas, Abertas, Em Andamento, Concluídas
  - Aluguéis: Todos, Ativos, Finalizados
  - Contabilidade: Plano de Contas (receitas/despesas), Centros de Custo, Formas de Pagamento
  - Produtos, Usuários, Auditoria
- [x] Interface com checkbox para categoria completa ou subcategorias individuais
- [x] PDFs com logo CRA, tabelas formatadas, letras pretas
- [x] Exportação individual ou em lote

### Chatbot IA com Gemini ✅ (24/02/2026)
- [x] **Chatbot flutuante** em ambas as plataformas (Gerenciamento e Administrativo)
- [x] Integrado com **Gemini 2.0 Flash** via Emergent LLM Key
- [x] **Acesso COMPLETO a TODAS as coleções do banco de dados**:
  - Usuários, Máquinas, Categorias, Manutenções
  - Estoque (itens, categorias, movimentações)
  - Obras/Projetos
  - Cadastros (Clientes/Fornecedores)
  - Contas a Pagar e a Receber
  - Produtos, Ordens de Serviço
  - Plano de Contas, Centros de Custo, Formas de Pagamento
  - Aluguéis de Máquinas
  - Logs de Auditoria
- [x] Calcula totais, médias, identifica alertas (estoque baixo)
- [x] Resumo financeiro completo automatizado
- [x] Contexto atualizado em tempo real a cada pergunta

### Painel Administrativo ✅ (24/02/2026)
- [x] Listagem de todos os usuários da plataforma
- [x] Criar novos usuários (apenas via painel admin)
- [x] Excluir usuários
- [x] Visualizar atividades por usuário (clicável)
- [x] Aba de Auditoria com todos os logs do sistema
- [x] Estatísticas (total usuários, atividades do dia, registros totais)
- [x] Busca e filtros
- [x] Removido link "Cadastre-se" da tela de login
- [x] Registro de último login dos usuários
- [x] **Gerenciador de Banco de Dados** (novo - 24/02/2026):
  - [x] Visualização de todas as coleções do MongoDB
  - [x] Busca de documentos por nome, email, título, etc
  - [x] Paginação de resultados
  - [x] Visualização de documentos em JSON formatado
  - [x] Edição de documentos diretamente
  - [x] Criação de novos documentos
  - [x] Exclusão de documentos
  - [x] Proteção: apenas usuários com role "admin" podem acessar

### Módulo Gerenciamento Geral ✅
- [x] Autenticação (login/registro)
- [x] Dashboard com estatísticas
- [x] CRUD de categorias, máquinas, manutenções
- [x] Upload de fotos
- [x] Controle de estoque com alertas
- [x] Sistema de troca de óleo
- [x] Plano de Obras
- [x] Sistema de Auditoria
- [x] PWA Mobile

### Módulo Administrativo ✅ (Fevereiro 2026)
- [x] **Dashboard Financeiro** com 4 abas (Resumo, A Pagar, A Receber, Quitados)
- [x] **Badges de totais** (MÊS, ANO, GERAL) nas abas A Pagar e A Receber
- [x] **Valores de OS** refletidos no dashboard (A Pagar e A Receber)
- [x] **Saldo Líquido** na aba Quitados (Recebido - Pago)
- [x] Contas a Pagar (CRUD + marcar como pago + filtros)
- [x] Contas a Receber (CRUD + marcar como recebido + filtros)
- [x] **Plano de Contas** hierárquico (2 níveis: pai + subcontas)
- [x] **Exportação PDF** do Plano de Contas
- [x] **Centro de Custo** (CRUD completo)
- [x] **Formas de Pagamento** (CRUD completo, integrado aos formulários)
- [x] **Ordens de Serviço** com tipo financeiro (a_pagar, a_receber, nenhum)
- [x] Cadastros (clientes/fornecedores)
- [x] Produtos com **link de busca no Google**
- [x] NF-e (placeholder)
- [x] Navegação mobile

### **NOVO - Aluguéis de Máquinas** ✅ (Fevereiro 2026)
- [x] CRUD completo de aluguéis
- [x] **Seleção de máquinas** do sistema de Gerenciamento Geral
- [x] **Tipos de período**: hora, diária, semanal, quinzenal, mensal, semestral, anual, outro (especificar)
- [x] Campos: cliente (nome, telefone, documento), datas de entrega/vencimento, valores, local, observações
- [x] **Geração automática de conta a receber**
- [x] **Finalizar aluguel** marca conta como quitada
- [x] Filtros: todos, ativos, finalizados, cancelados
- [x] Indicador visual de aluguéis vencidos

### **NOVO - Central de Notificações** ✅ (Fevereiro 2026)
- [x] **Página dedicada** com visão consolidada de vencimentos
- [x] **Ícone de sino** no header com badge de contagem
- [x] **Prazo configurável** pelo usuário (padrão 7 dias)
- [x] Mostra: contas a pagar, contas a receber, ordens de serviço, aluguéis
- [x] **Classificação por urgência**: Urgente (vencida), Atenção (≤3 dias), Em breve (>3 dias)
- [x] Filtros por tipo e urgência
- [x] Resumo com totais por categoria
- [x] Navegação direta para o item clicado

### Endpoints da API Admin
- GET/POST/PUT/PATCH/DELETE `/api/admin/contas-pagar`
- GET/POST/PUT/PATCH/DELETE `/api/admin/contas-receber`
- GET/POST/PUT/DELETE `/api/admin/cadastros`
- GET/POST/PUT/DELETE `/api/admin/produtos`
- GET/POST/PUT/PATCH/DELETE `/api/admin/ordens-servico`
- GET/POST/PUT/DELETE `/api/admin/plano-contas`
- GET/POST/PUT/DELETE `/api/admin/centros-custo`
- GET/POST/PUT/DELETE `/api/admin/formas-pagamento`
- **GET/POST/PUT/PATCH/DELETE `/api/admin/alugueis`** (novo)
- **GET `/api/admin/maquinas-disponiveis`** (novo - busca máquinas do outro sistema)
- **GET `/api/admin/notificacoes?prazo_dias=7`** (novo)
- **GET `/api/admin/notificacoes/contagem`** (novo - para badge)
- GET `/api/admin/dashboard`

### Endpoints de Tarefas (NOVO - 24/02/2026)
- **POST `/api/admin-panel/tasks`** - Criar nova tarefa
- **POST `/api/admin-panel/tasks/{task_id}/attachments`** - Adicionar anexo à tarefa (100MB max)
- **GET `/api/admin-panel/tasks`** - Listar todas as tarefas (admin)
- **DELETE `/api/admin-panel/tasks/{task_id}`** - Excluir tarefa (admin)
- **GET `/api/tasks?system=gerenciamento|administrativo`** - Listar tarefas por sistema
- **GET `/api/tasks/unread-count?system=...`** - Contagem de tarefas não lidas
- **PATCH `/api/tasks/{task_id}/read`** - Marcar tarefa como lida
- **GET `/api/tasks/{task_id}/attachments/{filename}`** - Download de anexo

### Endpoints do Painel Administrativo (Database Manager)
- **GET `/api/admin-panel/database/{collection_name}`** - Lista documentos com paginação e busca
- **POST `/api/admin-panel/database/{collection_name}`** - Cria novo documento
- **PUT `/api/admin-panel/database/{collection_name}/{doc_id}`** - Atualiza documento
- **DELETE `/api/admin-panel/database/{collection_name}/{doc_id}`** - Exclui documento

## Backlog Priorizado

### P0 (Crítico) - ✅ CONCLUÍDO
- Autenticação
- CRUD de máquinas e manutenções
- Controle de estoque
- Sistema de troca de óleo
- Plano de Obras
- Sistema de Auditoria
- PWA Mobile
- Módulo Administrativo completo
- Dashboard com abas e badges
- Centro de Custo CRUD
- Formas de Pagamento CRUD
- OS com tipo financeiro
- **Aluguéis de Máquinas**
- **Central de Notificações**
- **Sistema de Armazenamento** (estilo Google Drive) ← NOVO 24/02/2026
- **Campo de Contrato em Aluguéis** (número + anexo) ← NOVO 24/02/2026

### NOVO - Sistema de Armazenamento ✅ (24/02/2026)
- [x] **Página dedicada** (`/armazenamento`) no estilo Google Drive
- [x] **Criar pastas** com nomes customizados
- [x] **Upload de arquivos** (múltiplos, qualquer formato)
- [x] **Visualização em grid ou lista**
- [x] **Navegação por breadcrumbs**
- [x] **Preview** de imagens e PDFs
- [x] **Download** de arquivos
- [x] **Renomear** arquivos e pastas
- [x] **Excluir** itens
- [x] **Pesquisa** por nome
- [x] Tema visual alinhado com a paleta CRA (vermelho e amarelo)

### NOVO - Contrato em Aluguéis ✅ (24/02/2026)
- [x] Campo **Nº do Contrato** no formulário de aluguel
- [x] **Anexo de arquivo de contrato** (PDF, DOC, DOCX, imagens)
- [x] **Visualização** do contrato diretamente na listagem
- [x] **Download** do arquivo de contrato

### Endpoints do Sistema de Armazenamento (24/02/2026)
- **GET `/api/storage/list?path=/`** - Lista arquivos e pastas
- **POST `/api/storage/folder`** - Cria nova pasta
- **POST `/api/storage/upload`** - Upload de arquivo
- **GET `/api/storage/download?path=/file.pdf`** - Download de arquivo
- **DELETE `/api/storage/delete?path=/item`** - Exclui arquivo ou pasta
- **PATCH `/api/storage/rename`** - Renomeia item

### Endpoints de Contrato de Aluguel (24/02/2026)
- **POST `/api/admin/alugueis/{id}/contrato`** - Upload de contrato
- **GET `/api/admin/alugueis/{id}/contrato/download`** - Download de contrato

### P1 (Importante) - Próximos Passos
- [x] **Exportação Excel/OFX** (além do PDF existente) ✅ CONCLUÍDO (24/02/2026)
- [x] **Visualização de Anexos em Modal** (Contas a Pagar/Receber) ✅ CONCLUÍDO (25/02/2026)
- [x] **Consulta de CNPJ** (preenchimento automático via BrasilAPI) ✅ CONCLUÍDO (25/02/2026)
- [x] **Consulta de CEP** (preenchimento automático via ViaCEP) ✅ CONCLUÍDO (25/02/2026)
- [x] **Anexos em Produtos** (upload de arquivos no cadastro) ✅ CONCLUÍDO (24/02/2026)
- [ ] **Integração estoque ↔ manutenção** (baixa automática de peças)
- [ ] **Integração NF-e com SEFAZ** (requer certificado digital A1)
- [ ] Gráficos de custos por categoria

### P2 (Desejável)
- [ ] Notificações por email/WhatsApp
- [ ] Integração com GPS/telemetria
- [ ] Níveis de permissão (admin vs operador)
- [ ] Modo offline completo
- [ ] Reativar PWA (Service Worker)

## Credenciais de Teste
- **Email**: test@test.com
- **Senha**: password

## Últimos Testes (Fevereiro 2026)
- Backend: 100% (16/16 testes - aluguéis e notificações)
- Frontend: 100% (todos os fluxos)
- Funcionalidades testadas: Aluguéis CRUD, seleção de máquinas, geração de conta a receber, finalização, notificações com prazo configurável, filtros, badge no header

### Bug Fix - Dropdowns (24/02/2026)
- **Problema**: Dropdown "Plano de Contas" não abria nos formulários de Contas a Pagar/Receber
- **Causa**: Componente Select do Shadcn/UI precisa de value válido correspondente a SelectItem
- **Solução**: Adicionada opção "Nenhum" (value='none') e tratamento de valor vazio
- **Arquivos**: `ContasPagarPage.jsx`, `ContasReceberPage.jsx`
- **Testes**: 100% aprovados (iteration_9.json)

## Refatoração do Backend (24/02/2026)

### O que foi feito:
- **Índice navegável**: Adicionado índice completo no início do `server.py` com número de linhas para cada seção
- **Estrutura modular criada**: Pasta `/routes`, `/models`, `/utils` com arquivos de exemplo
- **Documentação**: README.md explicando a estrutura proposta e como migrar
- **Backup**: Arquivo `server_backup.py` preservando o original

### Estrutura de Arquivos Criada:
```
/app/backend/
├── server.py           # ~5400 linhas com índice navegável
├── server_backup.py    # Backup original
├── README.md           # Documentação da refatoração
├── routes/
│   ├── auth.py         # Rotas de autenticação (exemplo)
│   └── categories.py   # Rotas de categorias (exemplo)
├── models/
│   ├── core.py         # Modelos principais
│   └── admin.py        # Modelos administrativos
└── utils/
    ├── database.py     # Conexão MongoDB
    ├── auth.py         # JWT e autenticação
    └── audit.py        # Log de auditoria
```

### Sistema de Tarefas/Mensagens ✅ (24/02/2026)
- [x] **Lançar Tarefa no Painel Admin**: Nova aba para criar tarefas/mensagens
- [x] **Seletor de Sistema Destino**: Gerenciamento Geral ou Administrativo
- [x] **Seletor de Prioridade**: Baixa, Média ou Alta (com ícones e cores)
- [x] **Campos**: Título, Mensagem e Anexos
- [x] **Upload de Anexos**: Até 100MB por arquivo, múltiplos anexos permitidos
- [x] **Download de Anexos**: Usuários podem baixar arquivos da tarefa
- [x] **Caixa de Tarefas**: Componente flutuante nos sistemas de destino
- [x] **Badge de Notificação**: Contador de tarefas não lidas no header
- [x] **Marcar como Lida**: Tarefas são marcadas automaticamente ao visualizar
- [x] **Histórico de Tarefas**: Admin pode ver todas as tarefas enviadas
- [x] **Excluir Tarefas**: Admin pode remover tarefas do sistema

### Bug Fix - Chatbot e Logout Mobile (24/02/2026)
- **Problema 1**: Chatbot estava sobrepondo a barra de navegação inferior no mobile
- **Solução**: Ajustada posição do chatbot para `calc(90px + env(safe-area-inset-bottom))` no mobile
- **Problema 2**: Chatbot e FAB (botão +) estavam sobrepostos no mobile
- **Solução**: Quando há FAB presente, o chatbot é posicionado à esquerda (`calc(16px + 56px + 16px)`)
- **Arquivos**: `ChatbotWidget.jsx`, `Layout.jsx`
- **Problema 3**: Logout não funcionava no mobile na tela de seleção de sistemas
- **Solução**: Adicionado `e.preventDefault()` e `e.stopPropagation()` no handler do botão
- **Arquivos**: `SystemSelectPage.jsx`

### Auditoria Detalhada (24/02/2026)
- **Problema**: Ações de auditoria estavam genéricas (apenas "criar", "excluir", etc)
- **Solução**: 
  - Adicionado campo `module` para identificar a plataforma (Gerenciamento Geral, Administrativo, Painel Admin)
  - Ações agora mostram descrição completa (ex: "Criou Item de Estoque" ao invés de "create")
  - Detalhes incluem nome do item e informações adicionais
  - Badges coloridos por módulo (vermelho=Gerenciamento, amarelo=Administrativo, roxo=Painel Admin)
- **Arquivos**: `server.py` (função create_audit_log), `PainelAdminPage.jsx`
- **Contraste**: Corrigido texto dos badges de usuário para branco

### Rebranding e Paleta de Cores (24/02/2026)
- **Nome da Empresa**: CRA Construtora (mantido)
- **Ícone**: HardHat (capacete de construção) do lucide-react
- **Nova Paleta**: Vermelho (#E31A1A), Amarelo (#FFC232), Preto (#000000), Branco (#FFFFFF)
- **Arquivos Modificados**: 
  - index.css (variáveis CSS globais)
  - App.css (sidebar, botões, estilos)
  - Layout.jsx, AdminLayout.jsx (sidebars)
  - LoginPage.jsx, RegisterPage.jsx (telas de login)
  - SystemSelectPage.jsx (seleção de módulos)
  - Todas as páginas em /pages e /pages/admin (substituição global de cores)

## Estrutura de Arquivos
```
/app/
├── backend/
│   └── server.py      # Monólito FastAPI (~3700 linhas)
└── frontend/
    └── src/
        ├── App.js
        ├── components/
        │   ├── AdminLayout.jsx    # Com ícone de sino e badge
        │   └── Layout.jsx
        └── pages/
            └── admin/
                ├── AdminDashboardPage.jsx
                ├── AlugueisPage.jsx        # NOVO
                ├── NotificacoesPage.jsx    # NOVO
                ├── CentroCustoPage.jsx
                ├── FormasPagamentoPage.jsx
                ├── OrdensServicoPage.jsx
                └── ...
```

### Consulta de CNPJ e CEP ✅ (25/02/2026)
- [x] **Consulta de CNPJ**: Preenchimento automático de dados via BrasilAPI (Receita Federal)
  - Endpoint: `GET /api/consulta/cnpj/{cnpj}`
  - Dados retornados: Razão Social, Nome Fantasia, Telefone, Email, Endereço completo, Situação, Atividade Principal
  - Botão de busca (lupa) ao lado do campo CNPJ no formulário de Pessoa Jurídica
  - Bug corrigido: Substituída implementação via Gemini (dados incorretos) por BrasilAPI (dados oficiais)
- [x] **Consulta de CEP**: Preenchimento automático de endereço via ViaCEP
  - Endpoint: `GET /api/consulta/cep/{cep}`
  - Dados retornados: Logradouro, Complemento, Bairro, Cidade, UF
  - Botão de busca (lupa) ao lado do campo CEP

## Últimos Testes (25/02/2026)
- **Backend CNPJ**: 100% (consulta via BrasilAPI funcionando)
- **Frontend CNPJ**: 100% (preenchimento automático validado)
- **Teste com CNPJ**: 00000000000191 (Banco do Brasil) - Retornou corretamente
- **Arquivo de teste**: `/app/test_reports/iteration_11.json`

### Visualização de Anexos em Modal ✅ (25/02/2026)
- [x] **Preview de Imagens**: Modal exibe imagens (PNG, JPG, GIF, WebP) em tamanho ampliado
- [x] **Preview de PDFs**: Modal exibe PDFs em iframe para visualização inline
- [x] **Botão de visualização (Eye)**: Adicionado para imagens E PDFs na lista de anexos
- [x] **Botão de Download no Modal**: Permite baixar o arquivo diretamente do modal de preview
- [x] **Botão X para fechar**: Modal pode ser fechado facilmente
- [x] **Bug corrigido**: Ordem das rotas no backend (`/attachments/download/{id}` antes de `/attachments/{type}/{id}`)
- [x] **Bug corrigido**: Botões de ação com `type="button"` para evitar submit do formulário
- **Arquivos modificados**: 
  - `frontend/src/components/AttachmentsSection.jsx`
  - `backend/server.py` (ordem das rotas)

### Correções e Melhorias - 25/02/2026

#### Preview de Arquivos no Armazenamento ✅
- [x] **Bug corrigido**: Preview de PDF retornava "Not authenticated" porque o endpoint exigia autenticação via header
- [x] **Solução**: Criado `optional_security` com `auto_error=False` para aceitar token via query string
- [x] **Suporte a vídeos**: Adicionado preview para arquivos MP4, WebM e OGG usando tag `<video>`
- **Arquivos modificados**: `backend/server.py`

#### Linhas Clicáveis nas Listas ✅
- [x] **Contas a Pagar**: Clique na linha abre modal de edição
- [x] **Contas a Receber**: Clique na linha abre modal de edição
- [x] **Cadastros**: Clique na linha abre modal de edição
- [x] **Produtos**: Clique na linha abre modal de edição
- [x] **Centro de Custo**: Clique na linha abre modal de edição
- [x] **Aluguéis**: Clique no card abre modal de edição
- [x] **Ordens de Serviço**: Clique no card abre modal de edição
- **Implementação**: Adicionado `cursor-pointer`, `onClick` na `<tr>` ou `<Card>`, e `e.stopPropagation()` nas colunas de ações

### Atualização de Branding e UI - 25/02/2026

#### Renomeação "CRA Construtora" → "Gerenciamento" ✅
- [x] Página de Login
- [x] Página de Seleção de Sistema
- [x] Layout (Sidebar)
- [x] Rodapé
- [x] Página de Registro
- [x] Página de Exportação
- [x] Chatbot Widget
- [x] Página "Mais"

#### Botão "Buscar" em todas as barras de pesquisa ✅
Adicionado em todas as páginas:
- [x] Dashboard Financeiro (todas as 4 abas)
- [x] Contas a Pagar
- [x] Contas a Receber
- [x] Cadastros
- [x] Produtos
- [x] Centro de Custo
- [x] Aluguéis
- [x] Ordens de Serviço
- [x] Formas de Pagamento
- [x] Máquinas
- [x] Manutenções
- [x] Estoque
- [x] Obras
- [x] Categorias
- [x] Armazenamento
- [x] Notificações
- [x] Uso de Máquinas (Usage)
- [x] Auditoria
- [x] Notificações Admin
- [x] Fornecedores
- [x] Painel Admin
- [x] Medições

#### Estrutura de Backend (Parcialmente refatorada)
A refatoração parcial foi preparada com arquivos em:
- `/app/backend/routes/auth.py` - Rotas de autenticação
- `/app/backend/routes/categories.py` - Rotas de categorias
- `/app/backend/utils/` - Funções utilitárias (database, auth, audit)
- `/app/backend/models/` - Modelos Pydantic

**Próximos passos da refatoração**:
1. Migrar rotas de máquinas para `/routes/machines.py`
2. Migrar rotas de manutenções para `/routes/maintenances.py`
3. Migrar rotas de estoque para `/routes/stock.py`
4. Migrar rotas administrativas para `/routes/admin.py`
5. Integrar routers modulares no `server.py` principal
