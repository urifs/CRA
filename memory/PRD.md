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
- **Módulo Administrativo** (financeiro, fornecedores, produtos, OS, NF-e)

## Arquitetura Atual

### Backend (FastAPI + MongoDB)
- **Auth**: JWT com bcrypt
- **Collections**: users, categories, machines, maintenances, stock_items, stock_movements, stock_categories, usage_logs, obras, audit_logs, contas_pagar, contas_receber, cadastros, produtos_admin, ordens_servico, plano_contas, centros_custo, formas_pagamento
- **Sistema Compartilhado**: Dados globais com auditoria

### Frontend (React + Shadcn UI)
- **Dois Módulos**:
  1. **Gerenciamento Geral** (laranja): Máquinas, Manutenções, Estoque, Obras
  2. **Administrativo** (azul): Financeiro, Fornecedores, Produtos, OS, NF-e
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

### Endpoints da API Admin
- GET/POST/PUT/PATCH/DELETE `/api/admin/contas-pagar`
- GET/POST/PUT/PATCH/DELETE `/api/admin/contas-receber`
- GET/POST/PUT/DELETE `/api/admin/cadastros`
- GET/POST/PUT/DELETE `/api/admin/produtos`
- GET/POST/PUT/PATCH/DELETE `/api/admin/ordens-servico`
- GET/POST/PUT/DELETE `/api/admin/plano-contas`
- GET/POST/PUT/DELETE `/api/admin/centros-custo`
- GET/POST/PUT/DELETE `/api/admin/formas-pagamento`
- GET `/api/admin/dashboard` (retorna stats, aPagar, aReceber, quitados, contasProximas)

## Backlog Priorizado

### P0 (Crítico) - ✅ CONCLUÍDO
- Autenticação
- CRUD de máquinas e manutenções
- Controle de estoque
- Sistema de troca de óleo
- Plano de Obras
- Sistema de Auditoria
- PWA Mobile
- **Módulo Administrativo completo**
- **Dashboard com abas e badges**
- **Centro de Custo CRUD**
- **Formas de Pagamento CRUD**
- **OS com tipo financeiro**

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
- Backend: 100% (27/27 testes)
- Frontend: 100% (todos os fluxos)
- Bug de scroll do sidebar: ✅ Corrigido
- Bug de login loop: ✅ Corrigido (Service Worker desativado)
- Módulo Administrativo: ✅ Funcionando

## Notas Técnicas

### Service Worker
O Service Worker foi desativado em `index.html` para resolver um bug de loop na tela de login. Isso significa que a funcionalidade PWA offline não está ativa. Para reativar no futuro, será necessário:
1. Reativar o registro do SW em `index.html`
2. Garantir que o cache seja invalidado corretamente em novas versões

### Estrutura de Arquivos
```
/app/
├── backend/
│   └── server.py      # Monólito FastAPI (~3400 linhas)
└── frontend/
    └── src/
        ├── App.js           # Rotas e autenticação
        ├── components/
        │   ├── AdminLayout.jsx
        │   └── Layout.jsx
        └── pages/
            └── admin/
                ├── AdminDashboardPage.jsx  # Dashboard com tabs
                ├── CentroCustoPage.jsx     # NOVO
                ├── FormasPagamentoPage.jsx # NOVO
                ├── OrdensServicoPage.jsx   # Atualizado com tipo_financeiro
                └── ProdutosPage.jsx        # Atualizado com busca Google
```
