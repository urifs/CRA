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
8. ✅ **Plano de Obras** - Gestão de obras com vinculação de máquinas
9. ✅ **Sistema Compartilhado** - Todos os funcionários veem os mesmos dados
10. ✅ **Sistema de Auditoria** - Histórico de alterações por funcionário
11. ✅ **PWA Mobile** - Versão instalável no celular

## Arquitetura

### Backend (FastAPI + MongoDB)
- **Auth**: JWT com bcrypt para hash de senhas
- **Collections**: users, categories, machines, maintenances, stock_items, stock_movements, stock_categories, usage_logs, obras, audit_logs
- **Upload**: Fotos armazenadas em base64 no MongoDB
- **Sistema Compartilhado**: Dados são globais (sem filtro por user_id nas queries)
- **Auditoria**: Todas as operações CRUD geram logs com nome do funcionário

### Frontend (React + Shadcn UI)
- **Design**: "Tactical Industrial" - Slate 900 + Safety Orange
- **Fonts**: Chivo (headings), Manrope (body), JetBrains Mono (data)
- **Components**: Shadcn UI customizado
- **PWA**: Service Worker, Manifest, ícones para instalação

### Mobile (PWA)
- **Instalável**: Pode ser adicionado à tela inicial em iOS e Android
- **Navegação inferior**: 5 itens principais (Início, Obras, Máquinas, Manutenções, Mais)
- **Botão flutuante**: Ação rápida para nova manutenção
- **Responsivo**: Layout otimizado para telas pequenas
- **Safe areas**: Suporte para dispositivos com notch

## O Que Foi Implementado (Fevereiro 2026)

### Funcionalidades Completas
- [x] Sistema de autenticação (login/registro com nome)
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
  - Alerta quando estoque < 5 unidades
- [x] **Sistema de Troca de Óleo**
  - Campo "Troca de Óleo" na ficha de manutenção
  - Página "Tempo de Uso" para registrar horas de uso das máquinas
  - Status visual com barras de progresso (horas e dias)
  - Alertas automáticos (50h para 500h, 2 meses para 1 ano)
  - Página de Notificações centralizada
- [x] **Plano de Obras**
  - CRUD completo de obras (criar, listar, editar, excluir)
  - Vincular máquinas a obras (tag)
  - Visualizar custos de manutenção por obra
  - Separação de custos preventivos vs corretivos
  - Página de listagem de obras com cards
  - Página de detalhes com máquinas e manutenções
  - Adicionar/remover máquinas de obras
  - Cálculo automático de custos
- [x] **Sistema Compartilhado**
  - Todos os funcionários veem os mesmos dados
  - Dados são globais, não mais filtrados por user_id
  - Registro de quem criou cada item (created_by)
- [x] **Sistema de Auditoria**
  - Registro automático de todas as alterações (criar, editar, excluir)
  - Nome e email do funcionário em cada registro
  - Detalhes da alteração (dados anteriores, etc.)
  - Página /audit com filtros por tipo e ação
  - Busca por funcionário, item ou detalhes
- [x] **PWA Mobile** (Fev 2026)
  - Manifest.json para instalação
  - Service Worker para cache e funcionamento offline
  - Ícones em múltiplos tamanhos (72x72 a 512x512)
  - Banner de instalação no mobile
  - Navegação inferior otimizada para mobile
  - Página "Mais" com acesso às funcionalidades secundárias
  - Botão flutuante (FAB) para nova manutenção
  - Suporte para safe areas (notch)
  - Layout responsivo otimizado

### Endpoints da API
- POST /api/auth/register, /api/auth/login, GET /api/auth/me
- GET/POST/PUT/DELETE /api/categories
- GET/POST/PUT/DELETE /api/machines
- PATCH /api/machines/{id}/obra
- GET/POST/DELETE /api/maintenances
- POST/DELETE /api/maintenances/{id}/photos
- GET/POST/PUT/DELETE /api/stock/items
- GET/POST/DELETE /api/stock/categories
- POST /api/stock/movements, GET /api/stock/movements
- POST /api/usage-logs, GET /api/usage-logs
- GET /api/oil-change-status
- GET /api/notifications
- GET /api/dashboard
- GET /api/balance
- GET/POST/PUT/DELETE /api/obras
- GET /api/audit-logs

## Como Instalar no Celular

### Android
1. Abra o Chrome e acesse a URL do sistema
2. Faça login com suas credenciais
3. O banner "Instalar CRA Construtora" aparecerá automaticamente
4. Clique em "Instalar"
5. O app será adicionado à sua tela inicial

### iPhone/iPad
1. Abra o Safari e acesse a URL do sistema
2. Faça login com suas credenciais
3. Toque no botão de compartilhar (quadrado com seta)
4. Role para baixo e toque em "Adicionar à Tela de Início"
5. Confirme tocando em "Adicionar"

## User Personas
1. **Gestor de Frota**: Visualiza dashboard, acompanha custos, monitora alertas, gerencia obras, audita alterações
2. **Mecânico**: Registra manutenções, anexa fotos, controla peças, registra horas
3. **Administrador**: Gerencia máquinas, categorias, estoque, obras e verifica auditoria

## Backlog Priorizado

### P0 (Crítico) - ✅ CONCLUÍDO
- Autenticação
- CRUD de máquinas e manutenções
- Upload de fotos
- Controle de estoque com alertas
- Sistema de troca de óleo com alertas
- Plano de Obras com vinculação de máquinas
- Sistema compartilhado para todos os funcionários
- Sistema de auditoria com nome do funcionário
- **PWA Mobile instalável**

### P1 (Importante) - Próximos Passos
- [ ] **Integração estoque ↔ manutenção** (baixa automática de peças)
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Gráficos de custos por categoria
- [ ] Notificações push (Web Push API)

### P2 (Desejável)
- [ ] Notificações por email/WhatsApp
- [ ] Integração com GPS/telemetria
- [ ] Multi-tenancy para múltiplas empresas
- [ ] Níveis de permissão (admin vs operador)
- [ ] Modo offline completo (sincronização)

## Credenciais de Teste
- **Email**: test@test.com
- **Senha**: password

## Próximas Ações
1. **Integrar estoque com manutenções** - Deduzir automaticamente peças do estoque ao registrar manutenção
2. Adicionar gráficos de custos no dashboard
3. Implementar exportação de relatórios
4. Implementar notificações push
