# PRD - Sistema de Gerenciamento ERP

## Problema Original
Sistema de gerenciamento de máquinas e manutenções com módulos administrativos (financeiro, estoque, cadastros), aluguéis, notificações, painel de super administrador, chatbot com IA, exportação PDF/Excel/OFX e sistema de armazenamento de arquivos.

## Arquitetura
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB (Motor)
- **Auth**: JWT com bcrypt
- **Integração**: Gemini AI para chatbot

## O que foi implementado

### Sessão Atual (26/02/2026) - Correções de UI

#### ✅ 1. Correção do Dropdown de Categorias - COMPLETO
- Corrigido o problema de autenticação nas chamadas axios
- Alterado endpoint de `/cadastros` para `/admin/cadastros`
- Dropdown de categorias agora funciona corretamente no formulário de nova máquina

#### ✅ 2. Visualização Lista/Grid no Estoque - COMPLETO
- Implementado viewMode com lista como padrão
- Adicionado seletor de visualização lista/grid
- Visualização em tabela mostra todas as informações dos itens
- Aba Categorias para gerenciar categorias/subcategorias de estoque

#### ✅ 3. Página de Categorias de Máquinas - COMPLETO
- Nova página `/categories` para gerenciamento
- CRUD completo de categorias
- CRUD completo de subcategorias
- Layout similar à página de Frotas
- Estatísticas: total de categorias, subcategorias e máquinas

#### ✅ 4. Seletor Grid/Lista em Máquinas - COMPLETO
- Adicionado toggle para alternar entre grid e lista
- Grid como visualização padrão
- Lista mostra máquinas em formato de tabela

### Sessões Anteriores

#### Sistema de Frotas
- Página FrotasPage.jsx com CRUD completo
- Criar/editar/excluir Frotas e Subfrotas
- Dropdowns no formulário de máquinas

#### Senhas em Pastas (Armazenamento)
- Campo de senha opcional ao criar pasta
- Modal para digitar senha ao acessar pasta protegida
- Endpoints: check-password, set-password, has-password

#### Subcategorias de Máquinas e Estoque
- Backend com CRUD de subcategorias
- Dropdowns integrados nos formulários

#### Dashboard Financeiro
- Aba "Vencidas" com resumos e listas detalhadas

#### Tempo de Uso
- Exclusão de registros individuais
- Exclusão de máquinas via card de status
- Cards compactos em grid de 4 colunas

## Backlog

### 🔴 P0 - Críticos
- [PENDENTE] Visualização de anexos no Armazenamento - bug herdado da sessão anterior

### 🟡 P1 - Pendentes
- Suporte para preview de Word/Excel no armazenamento
- Refatoração parcial do backend (server.py > 7500 linhas)

### 🔵 P2 - Futuros
- Integração Estoque ↔ Manutenção (baixa automática de peças)
- Notificações email/WhatsApp
- Reativar PWA

## Arquivos Principais
- `backend/server.py` - Backend monolítico (7500+ linhas)
- `frontend/src/pages/MachinesPage.jsx` - Página de máquinas
- `frontend/src/pages/StockPage.jsx` - Controle de estoque
- `frontend/src/pages/CategoriesPage.jsx` - Categorias de máquinas
- `frontend/src/pages/FrotasPage.jsx` - Gerenciamento de frotas
- `frontend/src/pages/ArmazenamentoPage.jsx` - Sistema de arquivos

## Credenciais de Teste
- Email: test@test.com
- Password: password
- Role: admin

## Integrações de Terceiros
- Gemini AI (chatbot)
- BrasilAPI, ViaCEP
- reportlab, openpyxl, python-ofxparse
