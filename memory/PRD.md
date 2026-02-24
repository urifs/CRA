# RA Locadora - Sistema de Gestão Empresarial

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

## Paleta de Cores (Atualizada 24/02/2026)
- **Vermelho**: #E31A1A (cor primária, botões de ação, links)
- **Amarelo**: #FFC232 (cor secundária, módulo administrativo)
- **Preto**: #000000 (sidebars, fundos de login/seleção)
- **Branco**: #FFFFFF (fundos de conteúdo principal)

## Arquitetura Atual

### Backend (FastAPI + MongoDB)
- **Auth**: JWT com bcrypt
- **Collections**: users, categories, machines, maintenances, stock_items, stock_movements, stock_categories, usage_logs, obras, audit_logs, contas_pagar, contas_receber, cadastros, produtos_admin, ordens_servico, plano_contas, centros_custo, formas_pagamento, **alugueis**
- **Sistema Compartilhado**: Dados globais com auditoria

### Frontend (React + Shadcn UI)
- **Dois Módulos**:
  1. **Gerenciamento Geral** (vermelho #E31A1A): Máquinas, Manutenções, Estoque, Obras
  2. **Administrativo** (amarelo #FFC232): Financeiro, Fornecedores, Produtos, OS, NF-e, Aluguéis, Notificações
- **PWA**: Instalável em dispositivos móveis (Service Worker desativado para debug)
- **Design Responsivo**: Navegação inferior no mobile

## O Que Foi Implementado

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
