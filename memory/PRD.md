# ERP CRA - Product Requirements Document

## Visão Geral
ERP Full-stack (React + FastAPI + MongoDB) para gestão de Frota, Finanças, RH e Operações.

## Módulos Principais
- **Gerenciamento**: Máquinas, Manutenções, Estoque, Obras, Categorias
- **Administrativo (Financeiro)**: Contas a Pagar/Receber, OS, Cadastros, Plano de Contas, Centro de Custo, Conciliação, Aluguéis, Imóveis, Importação NF-e/NFS-e
- **RH**: Funcionários, Jornadas de Trabalho, Ponto Eletrônico (dinâmico), Banco de Horas, EPIs, Solicitações de Folha, Anexos de Documentos
- **Armazenamento**: Pastas, Upload, Documentos
- **Painel Admin**: Usuários, Permissões, Auditoria (com Rollback), Database Manager, Backup Exportação

## Histórico de Implementações

### 25/05/2026
- **Histórico de Ações** restaurado ao filtro Administrativo (módulo financeiro) com limite ampliado para 200 registros (FinanceiroHistoryPanel).
- **Exportação PDF de Contas (Pagar/Receber)** ampliada (`/app/backend/routes/exports_all.py` → `export_individual_item`):
  - "Já Pago" / "Já Recebido" / "Saldo Restante" na seção VALORES.
  - Nova seção HISTÓRICO DE PAGAMENTOS/RECEBIMENTOS PARCIAIS detalhada.
  - Status: QUITADA / PAGAMENTO PARCIAL — Falta R$ X / EM ABERTO / CANCELADA.
- **Fix Bug Seleção Filtrada (ExportPage)**: master checkbox agora respeita o filtro de busca (Selecionar visíveis (X/Y) — Z no total).
- **Fix Bug Anexos de Funcionários (RH)**: criados 3 endpoints faltantes em `/app/backend/routes/rh.py`:
  - `POST /rh/funcionarios/{id}/anexos` — upload (max 50MB, salva em `uploads/funcionarios`)
  - `DELETE /rh/funcionarios/{id}/anexos/{anexo_id}` — remove anexo do disco e do array
  - `GET /rh/funcionarios/{id}/anexos/{anexo_id}/download` — download

### Sessões anteriores
- Coluna "Saldo Restante" e modal de parcelas em Contas a Pagar/Receber
- Audit Logs e Rollback expandidos (`reversible=True`)
- Ordenação de colunas server-side na Importação NF-e/NFS-e
- Bug fix RH: Ponto Eletrônico passou a usar `jornada_id` dinâmica
- Bug fix Financeiro: Filtros incluem contas `parcial`
- Endpoint admin de exportação ZIP completa do banco (MongoDB → Supabase)
- Bug fix Financeiro: PUT em conta quitada não reverte mais o status

## Backlog (Pendente)
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
