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

### 27/05/2026 (sessão 7 - Fix CRÍTICO: PUT contas perdendo vínculo de parcela)
- **Bug**: Ao editar uma conta parcelada (PUT `/api/admin/contas-pagar/{id}`) sem enviar `parcela_origem_id` no payload (caso típico do form do frontend), o Pydantic `ContaPagarCreate` preenchia o campo com `None` (default) e o `$set` SOBRESCREVIA o vínculo da parcela com o grupo. Sintomas para o usuário:
  - A parcela editada saía do grupo (coluna "Saldo Restante" virava "—")
  - As demais parcelas do grupo recalculavam o saldo total considerando apenas N-1 parcelas
  - Aparência de que a parcela tinha sido "quitada" (mesmo sem ser)
- **Fix**: adicionado `parcela_origem_id` à lista `PAYMENT_FIELDS` em `update_conta_pagar` e `update_conta_receber` (`/app/backend/routes/financeiro.py:472,907`). Agora o campo é removido do payload antes do `$set`, preservando o vínculo da parcela com o grupo.
- Bônus em contas a receber: incluídos também `valor_recebido`, `recebimentos`, `data_recebimento`, `data_ultimo_recebimento` na lista de campos protegidos.
- Reproduzido via curl: parcela 1/3 perdia origem_id e grupo virava `None`. Após o fix: TODAS as 3 parcelas mantêm `parcela_origem_id` e `grupo=(total=8196, saldo=8196)`.

### 27/05/2026 (sessão 6 - Fix Storage: pastas faltando no modal + duplicação "Sistemas")
- **Fix StoragePickerModal**: trocado filtro hard-coded `i.name !== "Sistemas"` por `!i.virtual` em `/app/frontend/src/components/StoragePickerModal.jsx:73`. Agora pastas reais (mesmo se chamadas "Sistemas") aparecem no modal — só a virtual fica oculta (arquivos virtuais não podem ser anexados).
- **Fix duplicação "Sistemas"**: renomeado `VIRTUAL_ROOT` em `/app/backend/server.py:7610` de `"Sistemas"` para `"Sistemas (Anexos)"`. Resolve dois problemas:
  - Página principal não exibe mais duas pastas "Sistemas" duplicadas (virtual vs real do user).
  - Pasta REAL chamada `/Sistemas` (criada pelo usuário) agora é navegável (antes era interceptada pela virtual).
- Validado via curl: `/api/storage/list?path=/` retorna agora `"Sistemas (Anexos)"` como virtual. Navegação `/Sistemas (Anexos)/RH/...` funciona normalmente.
- **Auditoria de anexos**: novo script `/app/backend/utils/audit_anexos.py` para diagnosticar persistência de anexos. Resultado preview: 13/18 (72%) já em Object Storage; 5/18 (28%) ainda em FS local (precisam migrar); 0 órfãos.

### 25/05/2026 (sessão 5 - Fix definitivo Exportação PDF Múltipla)
- **Fix Exportação Selecionados (correção definitiva)**: O endpoint `POST /api/export/individual-multiple` em `exports_all.py` (linhas 2186-2206) agora chama o helper `generate_pdf_report(base_category, items, title)` produzindo uma **TABELA CONSOLIDADA única** (mesmo padrão da "Exportação Total"), em vez de gerar recibos individuais concatenados.
- Validado via curl + `analyze_file_tool`: PDF gerado é uma única página com tabela contendo colunas Fornecedor / Vencimento / Quitação / Valor / Pago / Descrição / Status e TOTAL GERAL — exatamente o formato solicitado pelo usuário.
- O parâmetro `base_category` (ex: `contas_pagar`) é derivado da `config["collection"]`, garantindo que `generate_pdf_report` selecione o layout correto.

### 25/05/2026 (sessão 4 - Object Storage Persistente)
- **NOVO: Módulo de Armazenamento migrado para Object Storage persistente** (resolução definitiva do problema "arquivos perdidos no deploy"):
  - Nova camada de metadados em MongoDB (`storage_files`) — pasta + arquivo com `path`, `parent_path`, `name`, `type`, `size`, `object_key`, `modified_at`
  - Helper `/app/backend/utils/storage_metadata.py`: list_children, create_folder, put_file, fetch_file_bytes, delete_node, rename_node, move_node, search
  - Endpoints reescritos para usar MongoDB + Object Storage:
    - `GET /api/storage/list` — Mongo primário + FS fallback (legado)
    - `POST /api/storage/upload` — sobe para OS + Mongo metadata
    - `GET /api/storage/download` — OS primário, FS fallback
    - `POST /api/storage/folder` — cria registro em Mongo
    - `DELETE /api/storage/delete` — remove de Mongo + FS legado (lixeira preservada)
    - `GET /api/storage/search` (em `routes/storage.py`) — Mongo + FS
  - Anexos universais (`routes/anexos.py`): `from-storage` e download integram com a nova camada (OS primário, FS fallback)
  - **3 novos endpoints admin** em `routes/storage_migrate.py`:
    - `POST /api/storage/migrate-to-object-storage` — varre FS local e migra tudo para OS+Mongo (idempotente)
    - `GET /api/storage/export-zip` — baixa ZIP completo (todos os arquivos do Mongo+OS+FS)
    - `POST /api/storage/import-zip` — recebe ZIP e popula MongoDB+OS (uso ideal: preview→produção)
  - **UI no Painel Admin** (aba "Banco de Dados"): card "Armazenamento (Object Storage)" com 3 botões (Migrar / Exportar ZIP / Importar ZIP)
- Testado em preview: 4 arquivos do `rh_normativos` (~18MB) migrados; upload/download/folder/delete/search funcionando 100%

### 25/05/2026 (sessão 3)
- **Fix Export Selecionados (PDF Multi-Item)**: rewriting do bloco contas_pagar/contas_receber em `/api/export/individual-multiple` para espelhar EXATAMENTE o layout do PDF single-item:
  - Logo CRA no topo de cada item
  - Seções IDENTIFICAÇÃO, DESCRIÇÃO, DATAS, CLASSIFICAÇÃO, VALORES
  - VALOR TOTAL destacado em amarelo/dourado (#D4A000)
  - HISTÓRICO DE PAGAMENTOS PARCIAIS quando aplicável
  - Status colorido no rodapé (QUITADA=verde, EM ABERTO=vermelho, PARCIAL=amarelo)
  - Título singularizado por item ("Conta a Pagar (Quitada)" em vez de "Contas a Pagar Quitadas")
  - Proteção contra valores None em `.get()` que crashavam o Paragraph
- Arquivo de validação: `/app/test_reports/multi_export_test_NEW.pdf` (37KB)

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
