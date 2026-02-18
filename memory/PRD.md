# FleetPro - Sistema de Gerenciamento de Manutenção de Máquinas

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

## Arquitetura

### Backend (FastAPI + MongoDB)
- **Auth**: JWT com bcrypt para hash de senhas
- **Collections**: users, categories, machines, maintenances
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

### Endpoints da API
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- GET/POST/DELETE /api/categories
- GET/POST/PUT/DELETE /api/machines
- GET/POST/DELETE /api/maintenances
- POST/DELETE /api/maintenances/{id}/photos
- GET /api/dashboard

## User Personas
1. **Gestor de Frota**: Visualiza dashboard, acompanha custos
2. **Mecânico**: Registra manutenções, anexa fotos
3. **Administrador**: Gerencia máquinas e categorias

## Backlog Priorizado

### P0 (Crítico) - ✅ CONCLUÍDO
- Autenticação
- CRUD de máquinas e manutenções
- Upload de fotos

### P1 (Importante) - Próximos Passos
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Notificações de manutenção preventiva
- [ ] Filtro por período de data
- [ ] Gráficos de custos por categoria

### P2 (Desejável)
- [ ] App mobile (React Native)
- [ ] Integração com GPS/telemetria
- [ ] Controle de estoque de peças
- [ ] Multi-tenancy para múltiplas empresas

## Próximas Ações
1. Implementar exportação de relatórios
2. Adicionar gráficos de custos no dashboard
3. Sistema de alertas para manutenções pendentes
