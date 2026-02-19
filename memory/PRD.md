# CRA Construtora - Sistema de Gerenciamento de Manutenção de Máquinas

## Problema Original
Sistema de gerenciamento de máquinas (tratores e caminhões) para registro de manutenções com:
- Cadastro de máquinas com placa
- Fichas de manutenção (peça, data de troca, valor, tipo preventiva/corretiva)
- Anexar fotos nas fichas
- Histórico completo por máquina

## Escolhas do Usuário
1. ✅ Autenticação JWT (email/senha)
2. ✅ Visualização no sistema (sem exportação PDF/Excel)
3. ✅ Categorias personalizadas de máquinas
4. ✅ Histórico completo de manutenções por máquina
5. ✅ Registro manual (sem notificações automáticas)
6. ✅ Controle de estoque de peças (completo com alertas)
7. ✅ Sistema de troca de óleo com controle de tempo de uso

## Arquitetura

### Backend (FastAPI + MongoDB)
- **Auth**: JWT com bcrypt para hash de senhas
- **Collections**: users, categories, machines, maintenances, stock_items, stock_movements, stock_categories, usage_logs
- **Upload**: Fotos armazenadas em base64 no MongoDB

### Frontend (React + Shadcn UI)
- **Design**: "Tactical Industrial" - Slate 900 + Safety Orange
- **Fonts**: Chivo (headings), Manrope (body), JetBrains Mono (data)
- **Components**: Shadcn UI customizado

## O Que Foi Implementado (Janeiro 2026)

### Funcionalidades Completas
- [x] Sistema de autenticação (login/registro)
- [x] Dashboard com estatísticas (total máquinas, manutenções, gastos)
- [x] CRUD completo de categorias
- [x] CRUD completo de máquinas
- [x] CRUD completo de manutenções
- [x] Upload de fotos nas manutenções
- [x] Filtros e busca
- [x] Histórico por máquina
- [x] Design responsivo
- [x] **Controle de Estoque**
  - Cadastro de peças com quantidade, estoque mínimo, preço
  - Entrada/saída de itens com histórico
  - Alertas de reposição no dashboard
  - Filtro de itens com estoque baixo
  - Gerenciamento de categorias de estoque
- [x] **Sistema de Troca de Óleo** (Novo!)
  - Campo "Troca de Óleo" na ficha de manutenção
  - Página "Tempo de Uso" para registrar horas de uso das máquinas
  - Status visual com barras de progresso (horas e dias)
  - Alertas automáticos:
    - Faltam 50h para 500h de uso
    - Faltam 2 meses para 1 ano
    - Limite atingido (urgente)
  - Página de Notificações centralizada

### Endpoints da API
- POST /api/auth/register, /api/auth/login, GET /api/auth/me
- GET/POST/DELETE /api/categories
- GET/POST/PUT/DELETE /api/machines
- GET/POST/DELETE /api/maintenances (com is_oil_change)
- POST/DELETE /api/maintenances/{id}/photos
- GET/POST/PUT/DELETE /api/stock/items
- GET/POST/DELETE /api/stock/categories
- POST /api/stock/movements, GET /api/stock/movements
- POST /api/usage-logs, GET /api/usage-logs
- GET /api/oil-change-status
- GET /api/notifications
- GET /api/dashboard

## User Personas
1. **Gestor de Frota**: Visualiza dashboard, acompanha custos, monitora alertas
2. **Mecânico**: Registra manutenções, anexa fotos, controla peças, registra horas
3. **Administrador**: Gerencia máquinas, categorias e estoque

## Backlog Priorizado

### P0 (Crítico) - ✅ CONCLUÍDO
- Autenticação
- CRUD de máquinas e manutenções
- Upload de fotos
- Controle de estoque
- Sistema de troca de óleo com alertas

### P1 (Importante) - Próximos Passos
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Gráficos de custos por categoria
- [ ] Integração estoque ↔ manutenção (baixa automática)
- [ ] Notificações por email/WhatsApp

### P2 (Desejável)
- [ ] App mobile (React Native)
- [ ] Integração com GPS/telemetria
- [ ] Multi-tenancy para múltiplas empresas

## Próximas Ações
1. Implementar exportação de relatórios
2. Adicionar gráficos de custos no dashboard
3. Integrar controle de estoque com manutenções (baixa automática)
