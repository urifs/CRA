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
- **Collections**: users, categories, machines, maintenances, stock_items, stock_movements, stock_categories, usage_logs, obras, audit_logs, contas_pagar, contas_receber, fornecedores, produtos, ordens_servico, plano_contas
- **Sistema Compartilhado**: Dados globais com auditoria

### Frontend (React + Shadcn UI)
- **Dois Módulos**:
  1. **Gerenciamento Geral** (laranja): Máquinas, Manutenções, Estoque, Obras
  2. **Administrativo** (azul): Financeiro, Fornecedores, Produtos, OS, NF-e
- **PWA**: Instalável em dispositivos móveis
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
- [x] Dashboard Administrativo (totais, vencimentos)
- [x] Contas a Pagar (CRUD + marcar como pago)
- [x] Contas a Receber (CRUD + marcar como recebido)
- [x] Fornecedores (CRUD + busca)
- [x] Produtos (CRUD + busca)
- [x] Ordens de Serviço (CRUD + status)
- [x] Plano de Contas (receitas/despesas)
- [x] Página de NF-e (placeholder)
- [x] Navegação mobile do admin
- [x] Página de Seleção de Sistema

### Endpoints da API Admin
- GET/POST/PUT/PATCH/DELETE `/api/admin/contas-pagar`
- GET/POST/PUT/PATCH/DELETE `/api/admin/contas-receber`
- GET/POST/PUT/DELETE `/api/admin/fornecedores`
- GET/POST/PUT/DELETE `/api/admin/produtos`
- GET/POST/PUT/PATCH/DELETE `/api/admin/ordens-servico`
- GET/POST/PUT/DELETE `/api/admin/plano-contas`
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
- **Módulo Administrativo completo**

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

## Credenciais de Teste
- **Email**: test@test.com
- **Senha**: password

## Últimos Testes (Fevereiro 2026)
- Backend: 100% (31/31 testes)
- Frontend: 100% (todos os fluxos)
- Bug de scroll do sidebar: ✅ Corrigido
- Módulo Administrativo: ✅ Funcionando
