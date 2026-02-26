# PRD - Sistema de Gerenciamento ERP

## Problema Original
Sistema de gerenciamento de máquinas e manutenções com módulos administrativos (financeiro, estoque, cadastros), aluguéis, notificações, painel de super administrador, chatbot com IA, exportação PDF/Excel/OFX e sistema de armazenamento de arquivos.

## Arquitetura
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB (Motor)
- **Auth**: JWT com bcrypt
- **Integração**: Gemini AI para chatbot

## O que foi implementado

### Sessão Atual (26/02/2026) - Parte 4

#### ✅ Correção Exportação de Contas a Pagar - COMPLETO
- Corrigido filtro de status: de "pendente" para "em_aberto"
- PDFs de Contas a Pagar agora contêm os dados corretamente

#### ✅ Exportação Combinada - COMPLETO
- Novo endpoint `POST /api/export/combined` para exportar múltiplas categorias em um único PDF
- Frontend atualizado para usar exportação combinada ao clicar em "Exportar (N)"
- Todos os itens selecionados são exportados em um único arquivo

#### ✅ Filtros Específicos na Exportação - COMPLETO
- Novo endpoint `GET /api/export/items/{collection}` para listar itens para filtro
- UI com botão de filtro (ícone de filtro) nas subcategorias que suportam
- Área expandível com chips selecionáveis para cada item
- Suporta: plano_contas, centros_custo, fleets, cadastros, formas_pagamento

#### ✅ Dropdown de Frotas em Contas a Pagar/Receber - COMPLETO
- Adicionado campo `frota_id` e `frota_nome` nos modelos Pydantic
- Dropdown "Frota (Opcional)" no formulário de Nova Conta a Pagar
- Dropdown "Frota (Opcional)" no formulário de Nova Conta a Receber
- Integração com sistema de frotas existente

### Sessões Anteriores
- Sistema de seleção múltipla no Armazenamento
- Funcionalidades de Mover e Copiar arquivos
- Preview de Word/Excel no armazenamento
- Correção preview de anexos
- Sistema de Frotas completo
- Senhas em Pastas no Armazenamento
- Dashboard Financeiro com aba "Vencidas"

## Backlog

### 🟡 P1 - Pendentes
- Refatoração parcial do backend (server.py > 7850 linhas)

### 🔵 P2 - Futuros
- Integração Estoque ↔ Manutenção (baixa automática de peças)
- Notificações email/WhatsApp
- Reativar PWA

## Novos Endpoints
- `POST /api/export/combined` - Exporta múltiplas categorias em um PDF
- `GET /api/export/items/{collection}` - Lista itens para filtro de exportação

## Modelos Atualizados
- `ContaPagarCreate/Response` - Adicionado `frota_id`, `frota_nome`
- `ContaReceberCreate/Response` - Adicionado `frota_id`, `frota_nome`

## Credenciais de Teste
- Email: test@test.com
- Password: password
- Role: admin

## Integrações de Terceiros
- Gemini AI (chatbot)
- BrasilAPI, ViaCEP
- reportlab, openpyxl, python-docx, python-ofxparse, PyPDF2
