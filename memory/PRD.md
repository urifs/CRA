# PRD - Sistema de Gerenciamento ERP

## Problema Original
Sistema de gerenciamento de máquinas e manutenções com módulos administrativos (financeiro, estoque, cadastros), aluguéis, notificações, painel de super administrador, chatbot com IA, exportação PDF/Excel/OFX e sistema de armazenamento de arquivos.

## Arquitetura
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB (Motor)
- **Auth**: JWT com bcrypt
- **Integração**: Gemini AI para chatbot

## O que foi implementado

### Sessão Atual (26/02/2026) - Parte 2

#### ✅ 1. Correção Preview de Anexos (P0) - COMPLETO
- Implementada visualização usando Blob URL em vez de URL direta
- PDFs agora usam `<object>` tag para melhor compatibilidade
- Imagens e vídeos funcionando corretamente
- Estado de loading durante carregamento do preview

#### ✅ 2. Suporte Word/Excel no Armazenamento - COMPLETO
- Novo endpoint `/api/storage/preview-office` para conversão para HTML
- Suporte para arquivos `.doc`, `.docx`, `.xls`, `.xlsx`
- Word: Renderiza títulos, parágrafos, headers e tabelas
- Excel: Renderiza planilhas com nome da aba e dados formatados em tabela
- Dependências: python-docx, openpyxl

### Sessão Atual (26/02/2026) - Parte 1

#### ✅ Correção do Dropdown de Categorias
- Corrigido problema de autenticação nas chamadas axios
- Dropdown funciona corretamente no formulário de nova máquina

#### ✅ Visualização Lista/Grid no Estoque
- Implementado viewMode com lista como padrão
- Seletor de visualização lista/grid funcional

#### ✅ Página de Categorias de Máquinas
- Nova página `/categories` para gerenciamento
- CRUD completo de categorias e subcategorias

#### ✅ Seletor Grid/Lista em Máquinas
- Toggle para alternar entre grid e lista

### Sessões Anteriores
- Sistema de Frotas completo
- Senhas em Pastas no Armazenamento
- Subcategorias de Máquinas e Estoque
- Dashboard Financeiro com aba "Vencidas"
- Tempo de Uso com exclusão e cards compactos

## Backlog

### 🟡 P1 - Pendentes
- Refatoração parcial do backend (server.py > 7500 linhas)

### 🔵 P2 - Futuros
- Integração Estoque ↔ Manutenção (baixa automática de peças)
- Notificações email/WhatsApp
- Reativar PWA

## Arquivos Principais
- `backend/server.py` - Backend monolítico (7600+ linhas)
- `frontend/src/pages/ArmazenamentoPage.jsx` - Sistema de arquivos com preview
- `frontend/src/pages/MachinesPage.jsx` - Página de máquinas
- `frontend/src/pages/StockPage.jsx` - Controle de estoque
- `frontend/src/pages/CategoriesPage.jsx` - Categorias de máquinas
- `frontend/src/pages/FrotasPage.jsx` - Gerenciamento de frotas

## Credenciais de Teste
- Email: test@test.com
- Password: password
- Role: admin

## Integrações de Terceiros
- Gemini AI (chatbot)
- BrasilAPI, ViaCEP
- reportlab, openpyxl, python-docx, python-ofxparse
