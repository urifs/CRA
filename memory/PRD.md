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
  - Removida separação Receitas/Despesas - cadastro livre
  - Lista única com subcontas em dropdown
  - Botão "Extrato" para visualizar movimentações

- ✅ **Dropdown de Cadastros em Contas a Pagar/Receber**:
  - Campo Fornecedor/Cliente agora é dropdown
  - Lista automaticamente os cadastros do sistema
  - Mostra nome + CNPJ/CPF

- ✅ **Botão "Cadastrar Novo" no Dropdown**:
  - Ao lado do dropdown há um botão com ícone de pessoa
  - Abre modal de cadastro rápido de Fornecedor/Cliente
  - Campos: Nome, CNPJ/CPF, Telefone, Email
  - Após cadastrar, seleciona automaticamente no dropdown

- ✅ **Melhorias na Visualização de Anexos**:
  - Melhor tratamento de erros no preview
  - Fallback quando arquivo não carrega

## Backlog (P1)
- Refatoração parcial do backend (server.py ~6800 linhas)
- Visualização de Word/Excel no armazenamento

## Backlog (P2)
- Integração Estoque ↔ Manutenção
- Notificações por email/WhatsApp
- Reativar PWA

## Integrações
- Gemini, BrasilAPI, ViaCEP, reportlab, openpyxl, python-ofxparse

## Credenciais de Teste
- **Email**: test@test.com | **Password**: password | **Role**: admin

## Arquivos Modificados
- `/app/frontend/src/pages/admin/PlanoContasPage.jsx`
- `/app/frontend/src/pages/admin/ContasPagarPage.jsx`
- `/app/frontend/src/pages/admin/ContasReceberPage.jsx`
- `/app/frontend/src/components/AttachmentsSection.jsx`
