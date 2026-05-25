# ERP CRA - Product Requirements Document

## Visão Geral
ERP Full-stack (React + FastAPI + MongoDB) para gestão de Frota, Finanças, RH e Operações.

## Módulos Principais
- **Gerenciamento**: Máquinas, Manutenções, Estoque, Obras, Categorias, Frotas
- **Administrativo (Financeiro)**: Contas a Pagar/Receber, OS, Cadastros, Plano de Contas, Centro de Custo, Conciliação, Aluguéis, Imóveis, Importação NF-e/NFS-e
- **RH**: Funcionários, Jornadas de Trabalho, Ponto Eletrônico, Banco de Horas, EPIs, Solicitações de Folha, Férias
- **Armazenamento**: Pastas, Upload, Documentos
- **Sistema de Anexos Universal**: anexar arquivos a qualquer entidade via upload local ou vínculo com Armazenamento + preview inline

## Histórico de Implementações

### 25/05/2026 (sessão 2)
- **AnexosManager aplicado a TODOS os formulários restantes**:
  - `NewMaintenancePage.jsx` — anexos pendentes em criação + flushPending após POST
  - `MaintenanceDetailPage.jsx` — anexos vinculados à manutenção existente
  - `FolhaPagamentoPage.jsx` — modal "Detalhes da Folha" (read-mode)
  - `EPIPage.jsx` — modal "Nova Ficha EPI" com flushPending
  - `CustosPage.jsx` — modal "Configurar Custos" para tabelas oficiais (INSS/FGTS/CCT)
  - Fix import em `MedicoesPage.jsx` (AnexosManager + useRef estavam usados sem import)
- Backend `VALID_ENTITY_TYPES` já contempla todos os tipos (manutencao, epi_ficha, folha_pagamento, custo_rh, medicao, horimetro, combustivel)
- Testing agent: 12/12 backend (100%) + 6/7 frontend validados em runtime

### 25/05/2026
- **Preview Inline de Anexos** (NOVO): modal abre direto no AnexosManager mostrando:
  - **Imagens** (.jpg/.png/.gif/.webp/.svg) inline
  - **PDFs** em iframe interno
  - **Vídeos** (.mp4/.webm/.ogg) com player nativo
  - **Áudios** (.mp3/.wav/.ogg) com player nativo
  - **Texto** (.txt/.csv/.json/.xml/.md/.log) em iframe
  - Outros formatos: mensagem com botão "Baixar"
  - Endpoint `/api/anexos/download/{id}` aceita `?token=` query param para uso em <iframe>
- **Sistema de Anexos Universal** (NOVO):
  - Backend (`/app/backend/routes/anexos.py`): rotas genéricas para upload local, vínculo por referência do storage, listagem, download, remoção.
  - Frontend componentes: `AnexosManager.jsx` (botões "Do computador" / "Do armazenamento") e `StoragePickerModal.jsx` (navegação, busca, senha de pasta).
  - Aplicado em ~21 formulários.
- **Histórico de Ações** restaurado ao filtro Administrativo com limite 200.
- **Exportação PDF Contas Parciais** corrigida (Já Pago / Saldo / Histórico de pagamentos).
- **Fix Seleção Filtrada (ExportPage)**: master checkbox respeita filtro.

### Sessões anteriores
- Coluna "Saldo Restante" e modal de parcelas
- Audit Logs e Rollback expandidos
- Ordenação server-side Importação NF
- Bug fix RH Ponto Eletrônico com `jornada_id` dinâmica
- Bug fix Financeiro: filtros incluem `parcial`
- Exportação ZIP do banco (MongoDB → Supabase)
- Bug fix Financeiro: PUT em conta quitada preserva status

## Backlog (Pendente)
- **P1**: Rotação/zoom/anterior-próximo no modal de Preview Inline de anexos
- **P1**: Adicionar `<DialogDescription>` aos modais "Nova Ficha EPI" e "Configurar Custos" (a11y warning Radix)
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
