# ERP CRA - Product Requirements Document

## Visão Geral
ERP Full-stack (React + FastAPI + MongoDB) para gestão de Frota, Finanças, RH e Operações.

## Módulos Principais
- **Gerenciamento**: Máquinas, Manutenções, Estoque, Obras, Categorias, Frotas
- **Administrativo (Financeiro)**: Contas a Pagar/Receber, OS, Cadastros, Plano de Contas, Centro de Custo, Conciliação, Aluguéis, Imóveis, Importação NF-e/NFS-e
- **RH**: Funcionários, Jornadas de Trabalho, Ponto Eletrônico, Banco de Horas, EPIs, Solicitações de Folha, Férias, Anexos de Documentos
- **Armazenamento**: Pastas, Upload, Documentos
- **Painel Admin**: Usuários, Permissões, Auditoria (com Rollback), Database Manager, Backup Exportação
- **Sistema de Anexos Universal** (novo): qualquer formulário pode anexar arquivos via upload local OU vínculo com o módulo Armazenamento

## Histórico de Implementações

### 25/05/2026
- **Sistema de Anexos Universal** (NOVO):
  - Backend (`/app/backend/routes/anexos.py`): rotas genéricas `/api/anexos/{entity_type}/{entity_id}/...` para upload local, vínculo por referência do storage, listagem, download e remoção. Coleção MongoDB: `entity_anexos`.
  - Frontend componente reutilizável (`/app/frontend/src/components/AnexosManager.jsx`): 2 botões — "Do computador" (upload) e "Do armazenamento" (abre picker). Modo criação mantém pendentes em memória; após salvar a entidade o pai chama `flushPending(newId)` via ref.
  - Modal `StoragePickerModal.jsx`: navega pastas em árvore, busca por nome (server-side `/storage/search`), prompt de senha para pastas protegidas, multi-seleção.
  - Aplicado em ~21 formulários: Máquinas, Estoque, Obras, Frotas, Categorias, Cadastros, Fornecedores, Produtos, Contas Pagar, Contas Receber, Centro Custo, Plano Contas, Contas Bancárias, Formas Pagamento, Aluguéis, Imóveis, OS, Funcionários, Férias.
- **Histórico de Ações** restaurado ao filtro Administrativo com limite ampliado para 200 registros.
- **Exportação PDF de Contas Parciais** corrigida (Já Pago / Saldo Restante / Histórico de Pagamentos / Status com valor faltante).
- **Fix Seleção Filtrada (ExportPage)**: master checkbox respeita o filtro de busca.
- **Fix Anexos Funcionários (RH)**: criados endpoints `/rh/funcionarios/{id}/anexos[...]` (mantidos para retrocompatibilidade).

### Sessões anteriores
- Coluna "Saldo Restante" e modal de parcelas em Contas a Pagar/Receber
- Audit Logs e Rollback expandidos (`reversible=True`)
- Ordenação de colunas server-side na Importação NF-e/NFS-e
- Bug fix RH: Ponto Eletrônico usa `jornada_id` dinâmica
- Bug fix Financeiro: Filtros incluem contas `parcial`
- Exportação ZIP completa do banco (MongoDB → Supabase)
- Bug fix Financeiro: PUT em conta quitada não reverte mais o status

## Backlog (Pendente)
- **P2**: Aplicar AnexosManager nos formulários restantes não cobertos (Manutenções, Folha Pagamento, EPI, Custos RH, Banco Horas, Solicitações Folha, etc.) — esses não têm padrão `editingX` claro
- **P2**: Refatoração Fase 2 do `server.py`
- **P2**: Parcelas automáticas em Contas a Receber via OS recorrente
- **P2**: Mini-histórico do cliente no dropdown da OS
- **P3**: Dashboard de Custo por Máquina
- **P3**: Links públicos para relatórios PDF

## Integrações
- ABRASF Webservice (SOAP)
- Emergent LLM Key (OCR / Chat / Object Storage)
- ViaCEP / BrasilAPI / CBO API

## Credenciais de Teste
Email: test@test.com / Senha: password
