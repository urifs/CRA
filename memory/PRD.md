# PRD - Sistema de Gerenciamento ERP

## Problema Original
Sistema de gerenciamento de máquinas e manutenções com módulos administrativos (financeiro, estoque, cadastros), aluguéis, notificações, painel de super administrador, chatbot com IA, exportação PDF/Excel/OFX e sistema de armazenamento de arquivos.

## Arquitetura
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB (Motor)
- **Auth**: JWT com bcrypt
- **Integração**: Gemini AI para chatbot

## O que foi implementado

### Sessão Atual (25/02/2026)
- ✅ **Aba "Vencidas" no Dashboard Financeiro**:
  - Nova aba com badge indicador de quantidade de contas vencidas
  - Cards de resumo: Total Vencido, A Pagar Vencido, A Receber Vencido
  - Listas detalhadas de contas vencidas com:
    - Descrição, fornecedor/cliente, centro de custo
    - Data de vencimento e dias de atraso
    - Valor da conta
  - Estados vazios amigáveis quando não há contas vencidas
  - Backend atualizado para retornar lista completa de contas vencidas

- ✅ **Função de Excluir Registros de Uso (Tempo de Uso)**:
  - Botão de excluir (ícone lixeira) em cada linha do histórico de uso
  - Modal de confirmação antes de excluir com detalhes do registro
  - Aviso que as horas serão subtraídas do total da máquina
  - Endpoint DELETE `/api/usage-logs/{log_id}` implementado no backend
  - Atualização automática das horas da máquina ao excluir

### Sessão Anterior (25/02/2026)
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
- `/app/frontend/src/pages/admin/AdminDashboardPage.jsx` - Nova aba Vencidas
- `/app/frontend/src/pages/UsagePage.jsx` - Função de excluir registros de uso
- `/app/backend/server.py` - Endpoint dashboard com lista de contas vencidas + DELETE usage-logs
- `/app/frontend/src/pages/admin/PlanoContasPage.jsx`
- `/app/frontend/src/pages/admin/ContasPagarPage.jsx`
- `/app/frontend/src/pages/admin/ContasReceberPage.jsx`
- `/app/frontend/src/components/AttachmentsSection.jsx`
