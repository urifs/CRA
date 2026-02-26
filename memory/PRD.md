# PRD - Sistema de Gerenciamento ERP

## Problema Original
Sistema de gerenciamento de máquinas e manutenções com módulos administrativos (financeiro, estoque, cadastros), aluguéis, notificações, painel de super administrador, chatbot com IA, exportação PDF/Excel/OFX e sistema de armazenamento de arquivos.

## Arquitetura
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB (Motor)
- **Auth**: JWT com bcrypt
- **Integração**: Gemini AI para chatbot

## O que foi implementado

### Sessão Atual (26/02/2026) - Parte 3

#### ✅ Seleção Múltipla de Arquivos - COMPLETO
- Botão "Selecionar" para ativar modo de seleção
- Checkboxes em todos os arquivos/pastas
- "Selecionar Todos" e "Limpar Seleção"
- Barra de ações com contador de itens selecionados
- Destaque visual (borda azul) nos itens selecionados

#### ✅ Mover Arquivos - COMPLETO
- Endpoint `/api/storage/move` no backend
- Modal de seleção de destino
- Suporte para mover múltiplos arquivos simultaneamente
- Tratamento de conflitos de nome (renomeia automaticamente)
- Validação para não mover pasta dentro dela mesma

#### ✅ Copiar Arquivos - COMPLETO
- Endpoint `/api/storage/copy` no backend
- Modal de seleção de destino
- Suporte para copiar múltiplos arquivos simultaneamente
- Adiciona " - Cópia (n)" em conflitos de nome

#### ✅ Exclusão em Lote - COMPLETO
- Botão "Excluir" na barra de ações de seleção
- Confirmação antes de excluir
- Move todos os itens selecionados para lixeira

#### ✅ Menu de Contexto Atualizado
- Opções Mover e Copiar no menu de cada arquivo/pasta
- Funciona tanto para itens individuais quanto seleção múltipla

### Sessão Atual - Parte 2 (Preview)
- Correção preview de anexos usando Blob URL
- Suporte para Word/Excel no armazenamento

### Sessão Atual - Parte 1 (UI)
- Correção dropdown de categorias
- Visualização lista/grid no Estoque
- Página de Categorias de máquinas
- Seletor grid/lista em Máquinas

## Backlog

### 🟡 P1 - Pendentes
- Refatoração parcial do backend (server.py > 7700 linhas)

### 🔵 P2 - Futuros
- Integração Estoque ↔ Manutenção (baixa automática de peças)
- Notificações email/WhatsApp
- Reativar PWA

## Arquivos Principais
- `backend/server.py` - Backend monolítico (7700+ linhas)
- `frontend/src/pages/ArmazenamentoPage.jsx` - Sistema de arquivos completo
- `frontend/src/pages/MachinesPage.jsx` - Página de máquinas
- `frontend/src/pages/StockPage.jsx` - Controle de estoque
- `frontend/src/pages/CategoriesPage.jsx` - Categorias de máquinas
- `frontend/src/pages/FrotasPage.jsx` - Gerenciamento de frotas

## Novos Endpoints de Armazenamento
- `POST /api/storage/move` - Move arquivo/pasta
- `POST /api/storage/copy` - Copia arquivo/pasta
- `GET /api/storage/preview-office` - Preview Word/Excel como HTML

## Credenciais de Teste
- Email: test@test.com
- Password: password
- Role: admin

## Integrações de Terceiros
- Gemini AI (chatbot)
- BrasilAPI, ViaCEP
- reportlab, openpyxl, python-docx, python-ofxparse
