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

### 29/05/2026 (sessão 25 - Observações RH: filtros + exportação PDF)
- **Pedido**: aprimorar a ferramenta de Observações com filtros no quadro e exportação em PDF.
- **Backend** (`/app/backend/routes/rh.py`): novo endpoint `GET /api/rh/observacoes/export/pdf?funcionario_id=&lembrete=com|sem` → PDF (landscape, padrão "CRA Apoio") com tabela Título/Funcionário/Observação/Lembrete/Criada em, respeitando filtros. Helper `_build_observacoes_pdf`.
- **Frontend** (`ObservacoesPage.jsx`): linha de filtros (busca + dropdown de funcionário + dropdown de lembrete "Com/Sem"); botão **"Exportar PDF"** no cabeçalho que baixa o PDF aplicando os filtros ativos (axios blob).
- **Validação**: curl (export "todos"=2 registros, "com lembrete"=1, HTTP 200, CRA Apoio + colunas corretas via pypdf) ✅; screenshot dos filtros + botão renderizados ✅. Lint OK.

### 29/05/2026 (sessão 24 - Nova ferramenta "Observações" no RH)
- **Pedido**: criar uma função "Observações" na barra lateral do RH com formulário (título, texto, vínculo a funcionário via dropdown, anexar arquivo, agendamento de aviso) e um quadro listando todas as observações (título, descrição, funcionário, se tem lembrete e data, data de criação).
- **Decisões do usuário**: lembrete agendado deve **aparecer nas Notificações do RH quando a data chegar** (integração completa); agendamento é **somente data**.
- **Backend** (`/app/backend/routes/rh.py`):
  - Nova collection `rh_observacoes`.
  - Endpoints: `POST /api/rh/observacoes`, `GET /api/rh/observacoes`, `PUT /api/rh/observacoes/{id}`, `DELETE /api/rh/observacoes/{id}`. Campos: titulo, descricao, funcionario_id/nome, lembrete_ativo, lembrete_data, created_at.
  - Integração em `GET /api/rh/notificacoes`: nova chave `lembretes_observacoes` (observações com `lembrete_ativo` e `lembrete_data <= hoje`), incluída no contador (`/notificacoes/contagem`) e nos tipos dispensáveis (`lembrete_observacao`).
  - `observacao_rh` adicionado a `VALID_ENTITY_TYPES` em `/app/backend/routes/anexos.py` (anexos via AnexosManager).
- **Frontend**:
  - Nova página `/app/frontend/src/pages/rh/ObservacoesPage.jsx`: form em modal (Título, Observação, dropdown Funcionário, Switch "Agendar aviso" + data, AnexosManager) + quadro de cards. Busca + cards de resumo.
  - Rota `/rh/observacoes` em `App.js` e item "Observações" (ícone StickyNote) na sidebar `RHLayout.jsx`.
  - `RHNotificacoesPage.jsx`: nova seção "Lembretes de Observações" com botão Ver + dispensar.
- **Validação**: curl (create/list/put/delete + notificação retornando lembrete) ✅; screenshots da lista, do modal completo e da seção de lembretes nas Notificações ✅. Lint OK em todos os arquivos.


### 29/05/2026 (sessão 23 - Coluna "Saldo Restante" mostra saldo de contas com pagamento parcial)
- **Pedido**: o "SALDO" exibido no modal de Histórico de Pagamentos (ex: R$ 14.740,00) não aparecia na coluna **Saldo Restante** da tabela — mostrava "—" para contas únicas com pagamento parcial (só funcionava para parcelas agrupadas).
- **Causa raiz**: a coluna só renderizava valor quando `c.parcela_origem_id && c.grupo_parcelas` (grupo de parcelas). Contas únicas com status "parcial" (valor_pago/valor_recebido > 0, sem parcela_origem_id) caíam no `else` e exibiam "—".
- **Fix** em `/app/frontend/src/pages/admin/ContasPagarPage.jsx` e `ContasReceberPage.jsx`: novo ramo condicional — quando `valor_pago`/`valor_recebido > 0` e status ≠ quitada/cancelada, exibe `c.saldo_restante` (com fallback computado `(valor_final||valor) − valor_pago/recebido`). Mantido o botão clicável para grupos de parcelas.
- **Validação**: lint OK nas 2 páginas; banco confirma `saldo_restante` armazenado em contas parciais (`/api/admin/...` registra ao quitar parcialmente, financeiro.py linha 572/1018).
- **Obs deploy**: correção no preview; usuário precisa redeployar para refletir em produção.


### 29/05/2026 (sessão 22 - Nome da empresa no PDF segue o Centro de Custo selecionado)
- **Pedido**: o nome embaixo da logo nas exportações estava sempre fixo ("CRA Construtora"). Deve refletir o **Centro de Custo selecionado** na página de Exportar, valendo para TODA exportação.
- **Decisões do usuário**: (1) com CC selecionado → exibir o **Nome do Centro de Custo**; (2) sem CC ("Todos") → manter padrão atual ("CRA Construtora"); (3) RH continua SEMPRE "CRA Apoio", independente do CC.
- **Implementação** em `/app/backend/routes/exports_all.py`:
  - Novo helper `_company_name_for_export(name, centro_custo)`: parte do `_company_name_for_collection` (RH→"CRA Apoio" vence sempre) e, quando não-RH e há CC selecionado (≠ "todos"), retorna o nome do CC; senão "CRA Construtora".
  - `generate_pdf_report(category, data, title, centro_custo=None)`: cabeçalho (logo) e rodapé agora usam `_company_name_for_export`.
  - 3 pontos de chamada atualizados para repassar o CC: `/export/pdf/{cat}` (param `centro_custo`), `/export/combined` (`data.centro_custo`), `/export/individual-multiple` (`data.centro_custo`).
- **Validação via curl + extração pypdf**:
  - `/export/pdf/contas_pagar` sem CC → "CRA Construtora" ✅
  - `/export/pdf/contas_pagar?centro_custo=Administrativo` → "Administrativo" ✅
  - `/export/pdf/funcionarios?centro_custo=Administrativo` (RH) → "CRA Apoio" (não sobrescreve) ✅
  - `/export/combined` com `centro_custo=Obra Jardins do Vale` → "Obra Jardins do Vale" ✅


### 29/05/2026 (sessão 21 - Sincronização Drive → Sistema)
- **Pedido**: criar botão "Sincronizar" para que arquivos/pastas criados manualmente no Drive (fora do ERP) apareçam no módulo Armazenamento do sistema.
- **Implementação**:
  - `/app/backend/utils/storage.py`: helper `sync_from_drive()` que faz walk recursivo do `CRA-ERP/` no Drive, e para cada pasta/arquivo que ainda não existe em `storage_files`, cria a entrada compatível com o esquema esperado (`type`, `path`, `parent_path`, `name`, `object_key=drive/<id>`). Para arquivos, indexa também em `storage_index` apontando para `backend=drive` com o `drive_file_id`, garantindo que downloads via `get_object` funcionem.
  - Helper `_walk_drive(service, folder_id, parent_path)` faz busca recursiva ordenada (pastas antes de arquivos) com paginação.
  - `/app/backend/routes/drive.py`: novo endpoint `POST /api/drive/sync` (admin-only) que roda o `sync_from_drive` em thread auxiliar para não bloquear o event loop.
  - `/app/frontend/src/components/DriveConnectionCard.jsx`: novo handler `handleSync` + botão **"Sincronizar do Drive"** (azul, ícone `RefreshCw`) ao lado de "Testar conexão". Toast mostra X pastas + Y arquivos adicionados, Z já existentes.
- **Validação via curl**:
  - Antes: 6 itens em `storage_files`. Drive tinha 25 itens.
  - Após `POST /api/drive/sync`: 16 novos itens importados (6 pastas + 10 arquivos), 9 já existentes pulados ✅
  - Total após sync: 22 itens, com `synced_from_drive=True` marcando os importados ✅

### 29/05/2026 (sessão 20 - Drive como espelho: criar/excluir pastas reflete no Drive)
- **Pedido**: ao criar ou excluir uma pasta no sistema, a ação não estava sendo refletida no Google Drive — usuário pediu que "o sistema de armazenamento seja um reflexo do Google Drive".
- **Implementação** em `/app/backend/utils/storage.py`:
  - `drive_create_folder(virtual_path)`: cria toda a hierarquia em `CRA-ERP/<path>` se não existir (idempotente).
  - `drive_delete_folder(virtual_path)`: localiza pelo path e envia para a lixeira do Drive. Bloqueia tentativa de apagar a raiz `CRA-ERP`. Também limpa entries do `storage_index` sob esse prefixo.
  - `drive_delete_file(path_or_object_key)`: localiza via `storage_index` e apaga do Drive.
  - `drive_rename(virtual_path, new_name)`: renomeia pasta ou arquivo no Drive.
  - Helper `_find_folder_id` (busca exata) e `_virtual_path_parts` (normalização).
- **Integração nos endpoints** em `/app/backend/server.py` e `/app/backend/routes/storage.py`:
  - `POST /api/storage/folder` → chama `drive_create_folder` após criar no Mongo.
  - `DELETE /api/storage/delete` → chama `drive_delete_folder` / `drive_delete_file` antes da remoção local.
  - `POST /api/storage/rename` → chama `drive_rename`.
- **Validação via curl**:
  - Criar `TestePastaDrive` no sistema → Drive passou de 5 para 6 itens, com `TestePastaDrive` na lista ✅
  - Excluir `TestePastaDrive` no sistema → Drive voltou para 5 itens ✅

### 28/05/2026 (sessão 19 - Google Drive Fases 2+3: Storage abstraction + Migração)
- **Implementação Fase 2 — Abstração de Storage transparente**:
  - `/app/backend/utils/storage.py` reescrito: agora `put_object(path, data, content_type)` automaticamente roteia para Google Drive (se conectado) ou Object Storage. Mesma assinatura, todos os endpoints existentes (`/api/storage/upload`, `/api/attachments/upload`, `/api/anexos/upload`, módulos folha, RH, etc.) ganharam Drive de graça sem qualquer mudança no código.
  - Uso de PyMongo síncrono (não Motor) para o índice `storage_index` e leitura de `drive_credentials`, evitando conflito de event loops em FastAPI.
  - Nova collection `storage_index`: mapeia `{ path, backend: drive|object_storage, drive_file_id, size, mime_type }` — fonte de verdade do roteamento de downloads.
  - Fallback automático: se upload no Drive falhar, cai pro Object Storage e indexa como `object_storage` (migrável depois).
- **Implementação Fase 3 — Migração**:
  - `/app/backend/utils/migrate_to_drive.py`: CLI `python -m utils.migrate_to_drive [--dry-run]` que migra 3 fontes — collection `storage_files` (módulo Armazenamento), collection `anexos` (financeiro/OS/RH), e `/app/uploads/` (legacy filesystem). Idempotente via `storage_index`.
  - Endpoint `POST /api/drive/migrate?dry_run=true|false` (admin-only): roda a migração em thread auxiliar e retorna estatísticas por fonte.
  - Botões "Simular" / "Migrar tudo" no `DriveConnectionCard` (`/painel-admin → Integrações`).
- **Validação**:
  - Upload via `POST /api/storage/upload` → arquivo cai em `CRA-ERP/teste_drive_v2/hello.txt` no Drive ✅
  - Download via `GET /api/storage/download` → CCT.pdf (14MB) baixou direto do Drive em 2.5s ✅
  - Migração real: 6 arquivos migrados (CCT.pdf, LTCAT.pdf, PCMSO.pdf, PGR.pdf + 2 testes) com 0 falhas ✅
  - Drive hoje contém 4 pastas raiz: `rh_normativos`, `storage`, `teste_drive`, `teste_os` ✅

### 28/05/2026 (sessão 18 - Google Drive Fase 1: Conexão OAuth)
- **Pedido**: refatorar todo o sistema de armazenamento para usar Google Drive como backend, com OAuth do admin, migração total, escopo global e fallback para Object Storage local.
- **Decisões do usuário**: OAuth do admin (não service account, não per-user) · migrar tudo · escopo global (incluindo anexos do sistema) · fallback para Object Storage quando Drive desconectado · estrutura `CRA-ERP/` com subpastas por entidade.
- **Implementação Fase 1 — Conexão & UI**:
  - `/app/backend/services/google_drive_service.py`: serviço com OAuth flow, refresh automático de token, `upload_bytes`, `download_bytes`, `delete_file`, `list_folder`, `ensure_path` (cria hierarquia de pastas). Pasta raiz fixa: `CRA-ERP`. Credenciais persistidas em `drive_credentials` (key=`workspace`).
  - `/app/backend/routes/drive.py`: endpoints `/api/drive/status`, `/api/drive/connect` (gera authorization URL com state CSRF), `/api/drive/callback` (persiste tokens + busca email), `/api/drive/disconnect`, `/api/drive/test`. Redirect URI dinâmico baseado em `Origin/Referer` para funcionar em preview e produção.
  - `/app/backend/.env`: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_DRIVE_REDIRECT_URI`, `FRONTEND_URL`.
  - `/app/frontend/src/components/DriveConnectionCard.jsx`: card com tema escuro (amber/emerald translúcidos) mostrando status com botões Conectar / Testar / Desconectar. Lê `?drive=connected` ou `?drive=error` da URL após callback.
  - **Localização final**: aba "Integrações" no `/painel-admin` (Painel Admin) — após o usuário pedir explicitamente que ficasse no admin. A página `/armazenamento` voltou ao estado original.
- **Validação**:
  - `GET /api/drive/status` → `{"connected":false}` ✅
  - `GET /api/drive/connect` → URL `accounts.google.com/o/oauth2/auth?...&access_type=offline&prompt=consent` ✅
  - Screenshot mostra o card amber no topo do Armazenamento com botão de conectar ✅
- **Próximas fases**:
  - Fase 2: abstração `storage_service.py` que automaticamente roteia para Drive (se conectado) ou Object Storage. Refatorar endpoints `/api/anexos/upload`, `/api/attachments/upload`, `/api/storage/upload` para usar a abstração.
  - Fase 3: script `migrate_to_drive.py` que sobe todos os arquivos legados para o Drive.
  - Fase 4: ArmazenamentoPage listar arquivos do Drive quando conectado.

### 27/05/2026 (sessão 17 - Fix Exportação Combinada RH + contagens)
- **Pedido**: usuário relatou erro 400 "Erro ao exportar relatório combinado" ao tentar exportar funcionários no `/rh/exportar`, mesmo após o fix da sessão 15. Botão mostrava "0 itens" no total.
- **Causa raiz**: `category_configs` do endpoint `POST /api/export/combined` em `/app/backend/routes/exports_all.py` cobria apenas Gerenciamento + Administrativo (machines, contas_pagar, plano_contas, etc.), mas NÃO continha as categorias do módulo RH (funcionarios, funcionarios_ativos, funcionarios_desligados, ponto_*, folha_pagamento, holerites, ferias*, epi_*, custos_*). Resultado: todas as categorias do RH caíam no `continue` do loop e `all_data` ficava vazio → 400. Adicionalmente `_EXPORT_ITEMS_CONFIG` (usado em `/api/export/items-count`) também não tinha as categorias RH → contagem retornava `-1` e UI mostrava "0 itens".
- **Fix**: adicionadas 18 entradas do RH em ambos os configs (`category_configs` do combined e `_EXPORT_ITEMS_CONFIG` do items-count): funcionarios, funcionarios_ativos, funcionarios_desligados, ponto_registros, ponto_hoje, ponto_mes, folha_pagamento, holerites, ferias, ferias_proximas, ferias_vencidas, epi_fichas, epi_vencidos, custos_funcionarios, custos_encargos.
- **Validação**:
  - `GET /api/export/items-count?collections=funcionarios,...` → retorna 9, 9, 0, 135, 1, 0, 1 (valores reais) ✅
  - `POST /api/export/combined` com `["funcionarios","funcionarios_ativos","funcionarios_desligados"]` → 200 + PDF 73KB ✅
  - Screenshot do `/rh/exportar`: "Exportar (3 categorias · 18 itens)" + badges visíveis em todas as subcategorias ✅

### 27/05/2026 (sessão 16 - Prévia de contagem antes de exportar)
- **Pedido**: mostrar a quantidade de itens que cada subcategoria retornará antes do usuário clicar em Exportar (evitar exportações vazias / surpresas).
- **Implementação em `/app/frontend/src/pages/ExportPage.jsx`**:
  - `fetchSubcategoryCounts` agora coleta **todas** as subcategorias visíveis (antes só pegava `EXPANDABLE_SUBCATEGORIES`). Backend já devolve `-1` para subcategorias inválidas (UI ignora).
  - Badge de contagem agora aparece em **todas** as subcategorias, não só nas expansíveis. Cores: cinza quando 0 itens, indigo quando há filtros ativos, cinza normal sem filtros.
  - Botão "Exportar" agora mostra "Exportar (X categorias · Y itens)" calculando o total de itens das subcategorias selecionadas (somando `subcategoryCounts`).
- **Validado via curl + screenshot**:
  - `GET /api/export/items-count?collections=...` retorna contagem para todas as categorias mapeadas e `-1` para inválidas.
  - Screenshot mostra: "Exportar (2 categorias · 60 itens)" quando 42 + 18 selecionados.

### 27/05/2026 (sessão 15 - Fix Exportação P0: state corrompido + endpoint 404)
- **Pedido**: usuário relatou que "qualquer coisa que tenta exportar dá erro 400 / Erro ao exportar relatório combinado". Console mostrava também 404 em `/api/formas-pagamento`.
- **Causas identificadas**:
  1. **State corrompido (`/app/frontend/src/pages/ExportPage.jsx` linha 203)**: o `useEffect` que reagia a mudanças de filtro global (período / centro de custo) chamava `setSelectedItems({})` — mas `selectedItems` é declarado como **array** (`useState([])`) e usado em todo o componente com `.length`, `.includes()`, `.filter()` e spread. Resultado: ao mudar qualquer filtro, o state virava `{}`, quebrando todas as operações subsequentes e enviando ao backend `categories: {}` → Pydantic retornava 422 / 400.
  2. **Endpoint 404 (`fetchFormasPagamento`)**: chamava `/api/formas-pagamento` mas o endpoint real é `/api/admin/formas-pagamento`.
- **Fix**:
  - `setSelectedItems({})` → `setSelectedItems([])`.
  - `${API}/formas-pagamento` → `${API}/admin/formas-pagamento`.
- **Validação via curl**:
  - `GET /api/admin/formas-pagamento` → 200 ✅
  - `POST /api/export/combined` com array correto → 200 + PDF 43KB ✅
  - `POST /api/export/combined` com objeto vazio (bug antigo) → 422 (confirmação da reprodução)

### 27/05/2026 (sessão 14 - Excluir Fichas de EPI)
- **Pedido**: permitir excluir fichas de EPI no módulo RH.
- **Implementação**:
  - **Backend** (`/app/backend/routes/rh.py`): novo endpoint `DELETE /api/rh/epi/fichas/{ficha_id}` que retorna 200 em caso de sucesso e 404 se a ficha não existir.
  - **Frontend** (`/app/frontend/src/pages/rh/EPIPage.jsx`): adicionado botão "Excluir" (vermelho, ícone `Trash2`) ao lado de "Ficha" e "Termo" em cada card de funcionário. Confirmação via `window.confirm` antes da exclusão. Toast de sucesso/erro e refresh automático da lista.
- **Validação via curl**: criação + delete (200) + delete novamente (404 esperado) → ✅ funcionando.

### 27/05/2026 (sessão 13 - PDFs do RH agora assinam como "CRA Apoio")
- **Pedido**: todas as exportações do módulo de RH (financeiro/admin continuam como "CRA Construtora") devem sair com o nome **"CRA Apoio"**.
- **Implementação**:
  - **Helper genérico em `/app/backend/utils/pdf_template.py`**: `add_corporate_header` agora aceita parâmetro opcional `company_name` (default "CRA Construtora"). Esse helper é usado por todos os PDFs corporativos da plataforma.
  - **`/app/backend/routes/exports_all.py`**: criado helper `_company_name_for_collection(name)` que retorna "CRA Apoio" para coleções/categorias do RH (`funcionarios`, `holerites`, `ponto_*`, `ferias*`, `epi_*`, `folha_*`, `custos_func*`, `custos_rh`, etc.) e "CRA Construtora" para o resto. Aplicado em `generate_pdf_report` (title + footer).
  - **`/app/backend/routes/rh.py`**: 5 chamadas a `add_corporate_header` (extrato banco de horas, espelho de ponto, holerite, ficha de EPI, termo de responsabilidade) passam `company_name="CRA Apoio"`. Textos de declaração que mencionavam "CRA Construtora" foram trocados por "CRA Apoio".
  - **`/app/backend/routes/chatbot.py`**: `_execute_chat_tool` aceita `module` da conversa. `gerar_pdf_documento` (tool genérica) usa "CRA Apoio" quando módulo é RH. PDFs de notificação formal, ficha do funcionário e lista de funcionários sempre usam "CRA Apoio". Footers ("Assistente IA do RH · CRA Construtora") trocados por "... · CRA Apoio".
- **Validação via curl + extração de texto com pypdf**:
  - `/export/pdf/funcionarios`: ✅ contém "CRA Apoio", NÃO contém "CRA Construtora"
  - `/export/pdf/contas_pagar`: ✅ contém "CRA Construtora", NÃO contém "CRA Apoio"
  - Teste direto do template com `company_name="CRA Apoio"`: ✅ correto

### 27/05/2026 (sessão 12 - Fix Exportação P0: filtro CC não chegava nos seletores de itens)
- **Causa raiz**: o fix da sessão 8 cobria os endpoints de **geração** do PDF/Excel (`/export/pdf/{cat}`, `/export/combined`, etc.), mas os endpoints que **listam itens disponíveis para o usuário selecionar** não recebiam nem aplicavam o filtro:
  - `GET /api/export/items/{collection}` — montava a lista do checkbox sem filtro de CC → o usuário VIA itens de outros CCs e podia marcá-los acidentalmente.
  - `GET /api/export/items-count` — contagem de itens por subcategoria também sem filtro.
  - `POST /api/export/individual-multiple` — gerava o PDF com os IDs marcados sem revalidar o CC.
- **Fix em `/app/backend/routes/exports_all.py`**:
  - Adicionado parâmetro `centro_custo` aos 3 endpoints acima.
  - Aplicação consistente via `_apply_centro_custo_filter` em todos eles (defesa em profundidade no `/export/individual-multiple`).
- **Fix em `/app/frontend/src/pages/ExportPage.jsx`**:
  - `fetchSubcategoryItems` e `fetchSubcategoryCounts` agora enviam `centro_custo` na query string.
  - `POST /export/individual-multiple` envia `centro_custo` no body.
  - `useEffect` de invalidação de cache passa a observar `selectedCentroCusto` — quando o usuário troca o CC, as listas e contagens são recarregadas automaticamente e seleções são limpas.
- Validado via curl: filtro `centro_custo=Obra Jardins do Vale` reduz contas_pagar de 42 → 1, maintenances de 6 → 0.

### 27/05/2026 (sessão 11 - Coluna "Pago R$" / "Recebido R$" nas listagens)
- **Pedido**: além de "Valor R$" e "Saldo Restante", exibir nas tabelas de Contas a Pagar e Contas a Receber uma coluna com o **valor já pago/recebido** de cada conta.
- **Implementação** em `/app/frontend/src/pages/admin/`:
  - `ContasPagarPage.jsx`: nova coluna **"Pago R$"** (verde esmeralda) entre "Valor R$" e "Saldo Restante", lê `c.valor_pago` (ou "—" se zerado).
  - `ContasReceberPage.jsx`: nova coluna **"Recebido R$"** (verde esmeralda) entre "Valor R$" e "Saldo Restante", lê `c.valor_recebido` (ou "—" se zerado).
- Lint passou nos dois arquivos sem warnings.

### 27/05/2026 (sessão 10 - P0: Endpoint de recuperação para parcela_origem_id zerado)
- **Contexto**: O bug da sessão 7 (PUT zerando `parcela_origem_id`) afetou parcelas em produção. Foi criado um endpoint admin para detectar e restaurar os vínculos automaticamente.
- **Endpoint**: `POST /api/admin/recover-parcela-vinculos?dry_run=true|false`
  - `dry_run=true`: preview do que será feito (sem alterar nada).
  - `dry_run=false`: aplica as correções e cria audit log.
- **Estratégia em `/app/backend/routes/financeiro.py`**:
  1. Busca contas com `parcela_origem_id=None` E `total_parcelas > 1` (órfãs candidatas).
  2. Agrupa pelo critério: `fornecedor_id/cliente_id + documento + numero_doc + data_emissao + valor + total_parcelas`.
  3. **Reaproveita origem_id**: se já existe alguma parcela COM origem_id e mesmo critério (caso típico: editou apenas 1 das 3 parcelas), aplica esse origem_id existente nas órfãs.
  4. **Cria novo origem_id**: se todas as N parcelas do grupo estão órfãs e count == total_parcelas.
  5. **Conflitos**: grupos incompletos (ex: 1 de 12 parcelas) ficam sem ação — exigem revisão manual.
- Validado via curl com 2 cenários reais:
  - Grupo A (3 parcelas, 1 órfã): reaproveitou origem_id das irmãs ✅
  - Grupo B (2 parcelas órfãs): criou novo origem_id ✅
- Rodou com `dry_run=false`: 3 parcelas restauradas, 2 conflitos listados (de dados legados antigos).

### 27/05/2026 (sessão 9 - Fix Chat RH: erro "campo 'conteudo' é obrigatório para gerar o PDF")
- **Bug**: Ao pedir geração de O.S. (Ordem de Serviço) pelo Chat IA do RH, o Gemini emitia o bloco `<<TOOL>>{"action":"gerar_pdf_documento", "params":{...}}<<END>>` com `conteudo` vazio (ou ausente), só escrevendo o texto narrativo ao redor. Resultado: erro "⚠ Falha ao executar a ação solicitada: O campo 'conteudo' é obrigatório para gerar o PDF.".
- **Fix em `/app/backend/routes/chatbot.py`**:
  - **Fallback inteligente**: quando o tool `gerar_pdf_documento` chega com `conteudo` vazio E a IA já produziu pelo menos 30 caracteres de texto narrativo, usamos esse texto como conteúdo do PDF — evitando o erro e ainda gerando um documento útil.
  - **Reforço no prompt do sistema**: adicionada regra crítica explícita com exemplo VÁLIDO completo do bloco TOOL e um requisito mínimo de ~1.500 caracteres de conteúdo para uma OS típica.
- Validado via curl: enviar "Redija uma O.S. de Motorista CAT E baseado no PGR/PCMSO" agora retorna PDF de 42KB sem erro.

### 27/05/2026 (sessão 8 - Fix Exportação: filtro centro de custo ignorado em coleções não-financeiras)
- **Bug**: Ao selecionar um Centro de Custo na página de Exportação e exportar categorias como Ordens de Serviço, Aluguéis, Manutenções, Folha de Pagamento, Custos RH, etc., o filtro era IGNORADO — vinham registros de todos os centros de custo. O filtro só era aplicado em `contas_pagar` e `contas_receber` (hard-coded em `FINANCIAL_COLLECTIONS`).
- **Fix em `/app/backend/routes/exports_all.py`**:
  - Nova função helper `_apply_centro_custo_filter(collection_name, query, centro_custo)` que filtra qualquer coleção do conjunto `CENTRO_CUSTO_COLLECTIONS` casando contra os 3 campos possíveis (`centro_custo`, `centro_custo_nome`, `centro_custo_id` resolvido via lookup em `centros_custo`).
  - 15 coleções agora respeitam o filtro: contas_pagar, contas_receber, ordens_servico, alugueis, maintenances, obras, folha_pagamento, custos_rh, combustivel, abastecimentos, imoveis, stock_movements, ferias, ponto_registros, epi_fichas.
  - Substituído o gate hard-coded `FINANCIAL_COLLECTIONS` em 4 endpoints: `/export/pdf/{cat}`, `/export/combined`, `/export/excel/{cat}`, `/export/ofx/{cat}`.
- Validado via curl + análise do PDF: filtro `centro_custo=Obra Jardins do Vale` agora retorna apenas 1 conta (a única com esse CC), versus 42 sem filtro.

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
