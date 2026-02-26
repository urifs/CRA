# PRD - Sistema de Gerenciamento ERP

## Problema Original
Sistema de gerenciamento de máquinas e manutenções com módulos administrativos (financeiro, estoque, cadastros), aluguéis, notificações, painel de super administrador, chatbot com IA, exportação PDF/Excel/OFX e sistema de armazenamento de arquivos.

## Arquitetura
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB (Motor)
- **Auth**: JWT com bcrypt
- **Integração**: Gemini AI para chatbot

## O que foi implementado

### Sessão Atual (26/02/2026)
- ✅ **Senhas em Pastas (Armazenamento)**:
  - Campo de senha opcional ao criar pasta
  - Modal para digitar senha ao acessar pasta protegida
  - Ícone de cadeado em pastas protegidas
  - Opção de definir/alterar/remover senha em pastas existentes
  - Endpoints: POST /storage/folder/check-password, POST /storage/folder/set-password

- ✅ **Sistema de Frotas (Gerenciamento)** - PARCIAL:
  - Backend completo: CRUD de Frotas e Subfrotas
  - Endpoints: /fleets, /subfleets
  - Modelo de máquina atualizado com fleet_id, subfleet_id, operator_id
  - Página FrotasPage.jsx criada
  - Rota e menu adicionados

### Sessões Anteriores
- Cards compactos no Tempo de Uso
- Excluir registros de uso e máquinas
- Aba "Vencidas" no Dashboard Financeiro
- Plano de Contas refatorado
- Dropdown de Cadastros
- Cadastro Rápido de Cliente/Fornecedor

## Backlog (Próxima Sessão)

### 🔴 P0 - Continuação das 5 Funcionalidades:
1. ~~Senhas em Pastas~~ ✅ DONE
2. ~~Sistema de Frotas~~ ✅ Backend + Página (FALTA: integrar dropdown no form de máquinas)
3. **Funcionários em Máquinas** - Dropdown com cadastros do sistema financeiro
4. **Subcategorias de Máquinas** - CRUD + campo opcional na criação
5. **Subcategorias de Estoque** - CRUD + campo opcional na criação

### 🟡 P1 - Pendentes:
- Verificar visualização de anexos (bug pendente)
- Refatoração parcial do backend

## Arquivos Modificados Nesta Sessão
- `/app/backend/server.py` - Endpoints de senha em pasta, frotas, subfrotas
- `/app/frontend/src/pages/ArmazenamentoPage.jsx` - UI de senha em pastas
- `/app/frontend/src/pages/FrotasPage.jsx` - NOVO
- `/app/frontend/src/App.js` - Rota de frotas
- `/app/frontend/src/components/Layout.jsx` - Menu de frotas

## Credenciais de Teste
- Email: test@test.com
- Password: password
- Role: admin
