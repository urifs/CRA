# PRD - Sistema de Gerenciamento ERP

## Problema Original
Sistema de gerenciamento de máquinas e manutenções com módulos administrativos (financeiro, estoque, cadastros), aluguéis, notificações, painel de super administrador, chatbot com IA, exportação PDF/Excel/OFX e sistema de armazenamento de arquivos.

## Arquitetura
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB (Motor)
- **Auth**: JWT com bcrypt
- **Integração**: Gemini AI para chatbot

## O que foi implementado

### Sessão Atual (26/02/2026) - 5 Funcionalidades Solicitadas

#### ✅ 1. Senhas em Pastas (Armazenamento) - COMPLETO
- Campo de senha opcional ao criar pasta
- Modal para digitar senha ao acessar pasta protegida
- Ícone de cadeado em pastas protegidas
- Opção de definir/alterar/remover senha em pastas existentes
- Endpoints: check-password, set-password, has-password

#### ✅ 2. Sistema de Frotas (Gerenciamento) - COMPLETO
- Página FrotasPage.jsx com CRUD completo
- Criar/editar/excluir Frotas
- Criar/editar/excluir Subfrotas dentro de Frotas
- Dropdowns de Frota e Subfrota no formulário de máquinas
- Backend com endpoints /fleets, /subfleets

#### ✅ 3. Funcionários em Máquinas (Gerenciamento) - COMPLETO
- Dropdown "Operador/Funcionário" no formulário de máquinas
- Lista todos os cadastros do sistema financeiro
- Campo opcional

#### ✅ 4. Subcategorias de Máquinas (Gerenciamento) - COMPLETO
- Backend com CRUD de subcategorias (/subcategories)
- Dropdown de Subcategoria no formulário de máquinas
- Filtra subcategorias baseado na categoria selecionada
- Campo opcional

#### ✅ 5. Subcategorias de Estoque (Gerenciamento) - COMPLETO (Backend)
- Backend com CRUD de subcategorias de estoque (/stock/subcategories)
- Modelo StockItemCreate/Response atualizado com subcategory_id
- Falta: integrar dropdown no frontend do estoque

### Outras Melhorias
- Placa agora é opcional no cadastro de máquinas
- Menu "Frotas" adicionado ao menu lateral

## Backlog

### 🟡 P1 - Pendentes
- Integrar dropdown de subcategoria no StockPage.jsx
- Verificar visualização de anexos (bug pendente)
- Refatoração parcial do backend

### 🔵 P2 - Futuros
- Integração Estoque ↔ Manutenção
- Notificações email/WhatsApp
- Reativar PWA

## Credenciais de Teste
- Email: test@test.com
- Password: password
- Role: admin
