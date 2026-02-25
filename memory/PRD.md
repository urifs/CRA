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
  - Botão "Extrato" para visualizar todas as contas a pagar/receber vinculadas
  - Funcionalidade de expandir para ver movimentações (como um extrato bancário)
  - Resumo financeiro: Total a Pagar, Total a Receber, Saldo
  - Campo "Tipo" removido do formulário de cadastro
  - Filtro de busca por nome/código
  - Exportar relatório em PDF

### Sessões anteriores
- Plano de Contas hierárquico (contas pai e subcontas)
- Dropdowns dependentes nos formulários de Contas a Pagar/Receber
- Correção de bug de associação de subcontas (e.stopPropagation)
- Sistema de armazenamento de arquivos
- Dashboard financeiro com filtros
- Módulo de Aluguéis de Máquinas
- Centro de Notificações
- Painel Admin (usuários, auditoria, banco de dados)
- Chatbot com Gemini AI
- Exportação PDF/Excel/OFX

## Backlog (P1 - Próximas tarefas)
- Refatoração parcial do backend (server.py tem ~6800 linhas)
- Visualização de outros tipos de arquivo (Word, Excel) no armazenamento

## Backlog (P2 - Futuro)
- Refatoração completa do backend
- Integração Estoque ↔ Manutenção (baixa automática de peças)
- Notificações externas (email/WhatsApp)
- Reativar PWA

## Integrações de Terceiros
- **Gemini**: Chatbot AI
- **BrasilAPI**: Consulta CNPJ
- **ViaCEP**: Consulta CEP
- **reportlab**: Geração PDF
- **openpyxl**: Geração Excel
- **python-ofxparse**: Geração OFX

## Credenciais de Teste
- **Email**: test@test.com
- **Password**: password
- **Role**: admin

## URLs
- **Frontend**: https://gerenciamento-erp-1.preview.emergentagent.com
- **Rotas principais**:
  - /administrativo/plano-contas
  - /administrativo/a-pagar
  - /administrativo/a-receber
  - /administrativo/dashboard

## Arquivos Principais
- `/app/frontend/src/pages/admin/PlanoContasPage.jsx` - Página refatorada
- `/app/frontend/src/pages/admin/ContasPagarPage.jsx`
- `/app/frontend/src/pages/admin/ContasReceberPage.jsx`
- `/app/backend/server.py` - Monólito (~6800 linhas, precisa refatoração)
