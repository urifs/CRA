# PRD - Sistema de Gerenciamento ERP

## Problema Original
Sistema de gerenciamento de máquinas e manutenções com módulos administrativos (financeiro, estoque, cadastros), aluguéis, notificações, painel de super administrador, chatbot com IA, exportação PDF/Excel/OFX e sistema de armazenamento de arquivos.

## Arquitetura
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB (Motor)
- **Auth**: JWT com bcrypt
- **Integração**: Gemini AI para chatbot

## O que foi implementado

### Última sessão (25/02/2026)
- ✅ **Plano de Contas Refatorado**:
  - Removida separação Receitas/Despesas - cadastro agora é livre
  - Lista única de Planos de Conta com subcontas em dropdown
  - Botão "Extrato" para visualizar contas a pagar/receber vinculadas
  - Campo "Tipo" removido do formulário

- ✅ **Dropdown de Cadastros em Contas a Pagar/Receber**:
  - Campo Fornecedor/Cliente agora é dropdown com lista de cadastros
  - Integração automática com módulo de Cadastros

- ✅ **Melhorias na Visualização de Anexos**:
  - Melhor tratamento de erros no preview
  - Fallback quando PDF não carrega no iframe
  - Mensagens informativas ao usuário

### Sessões anteriores
- Plano de Contas hierárquico (contas pai e subcontas)
- Dropdowns dependentes nos formulários
- Sistema de armazenamento de arquivos
- Dashboard financeiro com filtros
- Módulo de Aluguéis de Máquinas
- Centro de Notificações
- Painel Admin (usuários, auditoria, banco de dados)
- Chatbot com Gemini AI
- Exportação PDF/Excel/OFX

## Backlog (P1 - Próximas tarefas)
- Refatoração parcial do backend (server.py ~6800 linhas)
- Visualização de Word/Excel no armazenamento

## Backlog (P2 - Futuro)
- Integração Estoque ↔ Manutenção
- Notificações por email/WhatsApp
- Reativar PWA

## Integrações
- Gemini, BrasilAPI, ViaCEP, reportlab, openpyxl, python-ofxparse

## Credenciais de Teste
- **Email**: test@test.com | **Password**: password | **Role**: admin

## Arquivos Principais Modificados
- `/app/frontend/src/pages/admin/PlanoContasPage.jsx`
- `/app/frontend/src/pages/admin/ContasPagarPage.jsx`
- `/app/frontend/src/pages/admin/ContasReceberPage.jsx`
- `/app/frontend/src/components/AttachmentsSection.jsx`
