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
