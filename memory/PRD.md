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

## Paleta de Cores (Atualizada 24/02/2026)
- **Vermelho**: #E31A1A (cor primária, botões de ação, links)
- **Amarelo**: #D4A000 (cor secundária escurecida, módulo administrativo) ← ATUALIZADO
- **Preto**: #000000 (sidebars, fundos de login/seleção)
- **Branco**: #FFFFFF (fundos de conteúdo principal)

## Arquitetura Atual

### Backend (FastAPI + MongoDB)
- **Auth**: JWT com bcrypt
- **Collections**: users, categories, machines, maintenances, stock_items, stock_movements, stock_categories, usage_logs, obras, audit_logs, contas_pagar, contas_receber, cadastros, produtos_admin, ordens_servico, plano_contas, centros_custo, formas_pagamento, **alugueis**
- **Sistema Compartilhado**: Dados globais com auditoria
- **Painel Admin**: Endpoints para gestão de usuários e auditoria

### Frontend (React + Shadcn UI)
- **Três Módulos**:
  1. **Gerenciamento Geral** (vermelho #E31A1A): Máquinas, Manutenções, Estoque, Obras
  2. **Administrativo** (amarelo #FFC232): Financeiro, Fornecedores, Produtos, OS, NF-e, Aluguéis, Notificações
  3. **Painel Administrativo** (vermelho #E31A1A): Gestão de Usuários, Auditoria, Criação de Contas
- **PWA**: Instalável em dispositivos móveis (Service Worker desativado para debug)
- **Design Responsivo**: Navegação inferior no mobile

## O Que Foi Implementado

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

### P1 (Importante) - Próximos Passos
- [ ] **Integração estoque ↔ manutenção** (baixa automática de peças)
- [ ] **Integração NF-e com SEFAZ** (requer certificado digital A1)
- [ ] Exportação de relatórios (PDF/Excel)
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
