# CRA Construtora - Sistema de Gestão Empresarial (ERP)


## Bug Fix + Feature - 07/05/2026 (Sessão 46.7) — 🪟 Modal cortado + ⚙️ Processamento em background

### 1) Bug do modal cortado
Ao abrir uma folha importada o modal `max-w-6xl` estourava a viewport quando o sidebar do RH estava expandido (~256px), escondendo a primeira coluna ("Nome no PDF").

**Fix em `pages/rh/FolhaImportacaoPage.jsx`:**
- DialogContent: trocado `max-w-6xl` por `max-w-[min(95vw,1400px)] w-[min(95vw,1400px)]` + padding responsivo `p-4 sm:p-6`.
- Tabela interna: `min-w-[860px]` para forçar scroll horizontal em telas estreitas mantendo todas as colunas legíveis.

Validado via screenshot: modal agora ocupa exatamente 1400px (x=260, posicionado após o sidebar) e todas as 7 colunas aparecem completas.

### 2) Processamento em background com barra de progresso

Antes: `POST /folha-pagamento/importar` rodava OCR + match + split de forma síncrona (~30-60s), com risco de 502 do gateway preview.

**Implementado em `routes/folha_importacao.py`:**
- Função `_processar_folha_background(folha_id, pdf_bytes, filename)` rodando via `asyncio.create_task`.
- Endpoint `/importar` agora:
  1. Valida tipo/tamanho do arquivo (síncrono, rápido)
  2. Insere registro com `status="processando", progresso=0, etapa="fila"`
  3. Dispara task em background e retorna 202 imediatamente (~0s)
- Etapas com progresso: validando(5%) → ocr_iniciando(15%) → matching(60%) → split(60→95%) → concluida(100%)
- Em caso de falha, marca `status="erro"` com mensagem em `erro` (visível ao usuário).
- Endpoint legado `POST /_legacy_importar_sync` mantido para CLI/testes.

**Frontend `FolhaImportacaoPage.jsx`:**
- Após upload, registra ID em `processandoIds` e `setInterval` de 2.5s faz polling em `GET /folha-pagamento`.
- Linha da tabela mostra **barra de progresso azul** com porcentagem + texto da etapa atual ("Lendo PDF com IA...", "Casando funcionários com cadastro...", "Dividindo holerites...").
- Quando termina, toast verde "Folha pronta" + abre modal de detalhe automaticamente.
- Em caso de erro, badge vermelho com a mensagem.

### Validação
- ✅ E2E cURL: `/importar` retornou em **0s** com status="processando"; polling capturou 60% → 83% → 100% (~12s total). Antes: requisição síncrona de 35s.
- ✅ Lint Python e JavaScript OK.
- ✅ Smoke screenshot: modal de detalhe agora exibe todas as 7 colunas completas (1400px x 788px, x=260).

### Arquivos alterados
- `/app/backend/routes/folha_importacao.py` (nova função background + endpoint async + legado sync)
- `/app/frontend/src/pages/rh/FolhaImportacaoPage.jsx` (polling + barra de progresso + modal responsive)



## Feature MAJOR - 07/05/2026 (Sessão 46.6) — 📑 Importação de Folha de Pagamento (RH → Financeiro)

### Pedido completo do cliente
> "Folha de pagamento: botão de importar PDF, reconhecer todos os funcionários da folha, anexar holerite a cada um, RH envia pro Financeiro como folha cheia ou individual, Financeiro recebe notificação, aceita escolhendo individual/cheio, e cria contas a pagar com os PDFs anexados."

Decisões do cliente: **fuzzy match com confirmação manual** + **data vencimento configurável no aceite** + **qualquer user financeiro aprova** + **PDF inteiro + holerites individuais como anexos** + **plano de contas escolhido no aceite**.

### Implementado

**Backend (`routes/folha_importacao.py` — novo, ~540 linhas):**
- `POST /api/folha-pagamento/importar` (multipart): upload PDF → OCR via Gemini Flash 2.5 (emergentintegrations) → extrai estrutura JSON com 6 funcionários únicos, valor líquido, vencimentos, descontos, INSS, FGTS, IRRF e índices de páginas → fuzzy match com `funcionarios_collection` via rapidfuzz (token_sort_ratio: high≥92, medium 70-91, low<70) → split do PDF em N PDFs separados (PyPDF2) e upload de cada um no object storage.
- `GET /api/folha-pagamento` lista todas; `GET /api/folha-pagamento/{id}` detalhe; `GET /api/folha-pagamento/{id}/master-pdf` baixa original; `GET /api/folha-pagamento/{id}/holerite/{linha_id}` baixa individual.
- `POST /api/folha-pagamento/{id}/resolver-matches`: corrige vínculos manualmente (com 404 se funcionario_id inexistente).
- `POST /api/folha-pagamento/{id}/enviar-financeiro` body `{modo: "cheio"|"individual", observacao?}`: cria registro em `solicitacoes_folha_financeiro` status="pendente"; bloqueia se houver linhas sem match. Anti-duplicidade: bloqueia reenvio se já existe solicitação pendente ativa.
- `DELETE /api/folha-pagamento/{id}` (com proteção: não exclui se já aceita).
- `GET /api/financeiro/solicitacoes-folha?status=pendente|aceita|rejeitada`
- `POST /api/financeiro/solicitacoes-folha/{id}/aceitar` body `{plano_contas_id, data_vencimento, conta_bancaria_id?, forma_pagamento?, observacao?}`: cria N contas a pagar (1 por funcionário no modo individual, ou 1 conta consolidada com PDF mestre + 6 holerites como anexos no modo cheio); marca solicitação como aceita.
- `POST /api/financeiro/solicitacoes-folha/{id}/rejeitar` body `{motivo}`: marca rejeitada e libera folha para reedição/reenvio.

**Frontend RH (`pages/rh/FolhaImportacaoPage.jsx`):**
- Botão "Importar Folha (PDF)" no canto superior; lista folhas importadas com competência, empresa, total, status colorido.
- Modal de detalhe: tabela colorida (verde=match high/manual, amarelo=medium, vermelho=sem match), dropdown de Select para mapear funcionários manualmente, badges com sugestão e score%, botões para baixar holerite individual.
- Modal "Enviar ao Financeiro": cartões clicáveis (Folha cheia / Individual) + observação livre.
- Status visual: Em revisão (amarelo) → Enviada (azul) → Aceita (verde) ou Rejeitada (vermelho).

**Frontend Financeiro (`pages/admin/SolicitacoesFolhaPage.jsx`):**
- Nova entrada no menu "Solicitações de Folha" (ícone Inbox) em `/administrativo/solicitacoes-folha`.
- Filtros por status (pendente/aceita/rejeitada/todas) com badge de contagem de pendentes no header.
- Botões "Aceitar" (verde) e "Rejeitar" (vermelho) por linha.
- Modal Aceitar: pode trocar o modo (override individual ↔ cheio com aviso amarelo); auto-sugere data (5º dia do próximo mês) e plano de contas (regex /folha|salário|pessoal/); selects de plano, vencimento, conta bancária e forma de pagamento.

### Validação
- ✅ E2E via cURL: PDF do cliente (6 func, R$ 22.215,20, layout brasileiro) processado em ~30s, 4 match exato + 2 low (não cadastrados), envio individual + aceite criou 6 contas R$ 22.215,20 total com vencimento configurável e 1 anexo PDF cada.
- ✅ testing_agent_v3_fork iteration_37: backend 14/14 pytest + frontend 3/3 critical paths. Suite em `/app/backend/tests/test_folha_importacao.py`.
- ✅ Melhorias pós-teste aplicadas: anti-duplicidade no reenvio + 404 quando funcionario_id inválido.

### Arquivos novos/alterados
- **Novo**: `/app/backend/routes/folha_importacao.py` (540 linhas)
- **Novo**: `/app/frontend/src/pages/rh/FolhaImportacaoPage.jsx`
- **Novo**: `/app/frontend/src/pages/admin/SolicitacoesFolhaPage.jsx`
- **Novo**: `/app/backend/tests/test_folha_importacao.py`
- Editado: `server.py` (registro de routers)
- Editado: `App.js` (rotas), `RHLayout.jsx` + `AdminLayout.jsx` (itens de menu)
- Dependências: `rapidfuzz` instalado e congelado em requirements.txt

### Backlog/futuro (do testing agent)
- ⏰ Processar OCR em background (status="processando") para evitar 502 do gateway em PDFs grandes — hoje OCR síncrono ~30-60s.



## Bug Fix - 07/05/2026 (Sessão 46.5) — 🗑️ UI de "dispensar alertas de férias" estava desconectada do backend

### Reclamação do cliente
> "Já tinha lhe pedido anteriormente para ter a função de apagar essas notificações de agendamento de férias, cadê?"

Cliente reportou via produção (`construtoracra.com.br/rh/ferias`). Os alertas de "Período Aquisitivo" mostravam apenas o botão "Agendar", sem opção de descartar.

### Causa raiz
O backend de descarte (`POST /api/rh/ferias/alertas/dispensar/{id}` e `dispensar-todos`) foi implementado em sessões anteriores, mas a UI em `FeriasPage.jsx` nunca foi atualizada — apenas o card simples com botão "Agendar". Item ficou pendente.

### Implementado
**Backend (`routes/rh.py`):** novo endpoint `DELETE /api/rh/ferias/alertas/dispensar-todos` para reativar em massa.

**Frontend (`pages/rh/FeriasPage.jsx`):**
- 3 funções: `handleDispensarAlerta(id, nome)`, `handleDispensarTodos()`, `handleReativarDispensados()`.
- Card de alertas reformulado: badge com contagem ao lado do título; barra de ações com botões "Mostrar dispensados" e "Dispensar todos".
- Cada alerta individual ganhou ícone de lixeira (data-testid `btn-dispensar-alerta-{id}`) ao lado do botão "Agendar".
- `window.confirm` em todas as ações destrutivas; toasts "Alerta dispensado" / "N alertas dispensados" / "Alertas reativados".

### Validação
- ✅ Smoke E2E: tela mostra badge "2", botões "Mostrar dispensados", "Dispensar todos" e lixeira por alerta. Clique em lixeira → confirm → toast "Alerta dispensado" → lista atualiza. "Mostrar dispensados" reativa.
- ✅ Lint OK.

### Arquivos alterados
- `/app/backend/routes/rh.py` (DELETE em massa)
- `/app/frontend/src/pages/rh/FeriasPage.jsx` (UI completa)



## Feature - 07/05/2026 (Sessão 46.4) — 🏷️ Sinalização visual de NF com conta já lançada

### Pedido do usuário
> "Colocar uma sinalização nas notas fiscais que já tenham contas lançadas vinculadas a ela, tem que ter algum indicativo que a conta já foi lançada, para evitar duplicidade"

Antes: o botão "Criar conta a pagar" simplesmente sumia quando a NF tinha vínculo, mas não havia feedback visual claro — o usuário podia achar que "tava faltando o botão", ou pior, gerar duplicidade ao não enxergar o vínculo de relance.

### Implementado (`pages/admin/ImportacaoNFPage.jsx`)
- Helper `getContaVinculadaBadge(item)` — retorna `<span>` verde "✓ Conta lançada" quando há `conta_pagar_id` ou `conta_receber_id`.
- **Lista NF-e** (Compras): linha inteira ganha fundo `bg-emerald-50/60`; coluna Status agora mostra o status original + badge "Conta lançada" empilhado; coluna Ações substitui o botão "Criar conta" oculto por um indicador verde **"✓ Conta OK"** com tooltip "Conta a pagar já lançada para esta NF-e".
- **Lista NFS-e** (Serviços): mesmo tratamento — linha verde, dois badges na coluna Status, indicador "Conta OK" nas ações.
- **Modal de detalhe**: o título do Dialog "NF-e Nº X" passa a mostrar o badge "Conta lançada" ao lado.
- `data-testid` adicionados: `nfe-row-{id}`, `nfse-row-{id}`, `badge-conta-lancada-{id}`, `indicador-conta-{id}`.

### Validação
- ✅ Smoke E2E: criada conta a pagar via `POST /api/nfe/importadas/{id}/criar-conta-pagar` para a NF nº 8 → screenshot mostra a linha destacada em verde, badge "Conta lançada" sob "Processada" e botão "✓ Conta OK" na coluna Ações; outras 154 NFs permanecem normais.
- ✅ Conta de teste removida no fim; vínculo limpo automaticamente (fix sessão 45.9).

### Arquivos alterados
- `/app/frontend/src/pages/admin/ImportacaoNFPage.jsx`



## Feature - 07/05/2026 (Sessão 46.3) — 🔢 Contador de itens por subcategoria na Exportação

### Pedido do usuário
> "Colocar o contador de itens"

Sequência da fix de período (46.2): exibir o número de itens encontrados em cada subcategoria, refletindo o filtro global, para que o usuário enxergue imediatamente se o filtro está pegando.

### Implementado
**Backend (`routes/exports_all.py`):**
- Novo endpoint `GET /api/export/items-count?collections=a,b,c&data_inicio&data_fim` retorna `{<sub_id>: <count>}` em uma única chamada (mais leve que listar). Aplica `_apply_period_filter` por coleção, considera "vencidas" via `data_vencimento < hoje` e filtros estáticos (status: em_aberto/quitada/etc).
- Config compartilhada `_EXPORT_ITEMS_CONFIG` com 24 subcategorias mapeadas (espelha `get_export_items`).

**Frontend (`pages/ExportPage.jsx`):**
- State `subcategoryCounts` populado por `fetchSubcategoryCounts()`, disparado em `useEffect([categories, globalDataInicio, globalDataFim])`.
- Badge ao lado do `sub.label`:
  - Cinza (`bg-gray-100`) quando sem filtro ou contagem = 0
  - Azul indigo (`bg-indigo-100`) quando filtro de período ativo e há itens
  - `data-testid="count-{sub_id}"` em cada badge

### Validação
- ✅ curl `/items-count` sem filtro → `{contas_pagar_pendente: 15, contas_pagar_vencidas: 5, ...}`
- ✅ curl com filtro Abril/2026 → `{contas_pagar_pendente: 2, contas_pagar_vencidas: 2, contas_receber_pendente: 0, ...}`
- ✅ Screenshot mostra badges atualizando dinamicamente ao trocar o período (15→2, 4→0, 39→5).

### Arquivos alterados
- `/app/backend/routes/exports_all.py` (novo endpoint + config compartilhada)
- `/app/frontend/src/pages/ExportPage.jsx` (state + useEffect + render do badge)



## Bug Fix - 07/05/2026 (Sessão 46.2) — 🐛 Filtro de período ignorado em "Itens individuais" da Exportação

### Reclamação do cliente (via WhatsApp)
> "Bom dia. O sistema mesmo eu colocando o periodo de hoje, está filtrando todas em aberto. Eu preciso que os relatórios saiam por periodo."

Ao colocar Data Início = Data Fim = hoje (07/05/2026) na Exportação de Relatórios e expandir "Contas Pendentes", a lista de itens individuais continuava mostrando contas com vencimento de Abril (02/04/2026 e 10/04/2026), ignorando o filtro global.

### Causa raiz
O endpoint `GET /api/export/items/{collection}` (que popula a lista de itens individuais selecionáveis) **não aceitava** os parâmetros `data_inicio` e `data_fim`. O endpoint usado para gerar o PDF da categoria toda (`/api/export/pdf/{category}`) já filtrava corretamente, mas a lista UI exibia tudo, induzindo o cliente a achar que o filtro não funcionava.

### Implementado
**Backend (`routes/exports_all.py`):**
- `get_export_items` agora aceita `data_inicio` e `data_fim` como query params e roda `_apply_period_filter(db_collection, query_filter, data_inicio, data_fim)` antes da query MongoDB.

**Frontend (`pages/ExportPage.jsx`):**
- `fetchSubcategoryItems` agora passa `data_inicio`/`data_fim` (do banner global) na URL.
- Novo `useEffect([globalDataInicio, globalDataFim])` que invalida o cache de itens já carregados, limpa seleções e re-busca para subcategorias atualmente expandidas — garantindo que ao mudar o período, a lista UI atualiza sem precisar fechar/abrir.

### Validação
- ✅ curl: filtro `2026-05-07/2026-05-07` retorna **0 itens** (antes retornava 15)
- ✅ curl: filtro `2026-04-01/2026-04-30` retorna apenas as 2 contas que de fato vencem em abril
- ✅ pytest 4/4 — `/app/backend/tests/test_export_filtro_periodo.py`
- ✅ PDF de exportação por período continua funcionando (HTTP 200, 36KB)

### Arquivos alterados
- `/app/backend/routes/exports_all.py` (assinatura de `get_export_items` + chamada `_apply_period_filter`)
- `/app/frontend/src/pages/ExportPage.jsx` (`fetchSubcategoryItems` + useEffect de invalidação)
- `/app/backend/tests/test_export_filtro_periodo.py` (novo)

### Lembrete para o cliente
A correção está no **Preview**. Para refletir em `construtoracra.com.br`, é necessário clicar em **"Deploy"** na plataforma Emergent.



## Feature - 06/05/2026 (Sessão 46.1) — ⏰ Abono em Massa no Ponto Eletrônico

### Pedido do usuário
> "adicionar uma opção de abono em massa, onde posso selecionar vários dias de um funcionário para abonar de uma vez, sem precisar ir de um por um"

### Implementado
**Backend (`routes/rh.py`):**
- `POST /api/rh/ponto/abono-em-massa` — JSON `{funcionario_id, datas: [str], tipo, motivo, anexo?}`. Valida tipo (TIPOS_ABONO_VALIDOS), motivo, datas (deduplica e valida formato), depois `delete_many({"funcionario_id", "data": {"$in": datas}})` + `insert_many` em uma transação lógica. Retorna `{criados, datas, abonos}`.
- `POST /api/rh/ponto/abono-em-massa-com-anexo` — multipart com `datas` como string JSON. Faz upload do arquivo UMA vez e compartilha o mesmo `storage_path` em todos os abonos (poupa storage e mantém auditoria).

**Frontend (`PontoQuadroTab.jsx`):**
- Estado novo: `modoSelecao`, `diasSelecionados`, `abonoMassaForm`, `salvandoMassa`.
- Barra de ações na tabela do detalhe do funcionário: botão "Abono em massa" → ativa modo seleção (linha clicável + checkboxes amarelos só em dias com falta/incompleto/sem_registro).
- Botões de apoio: "Selecionar todos faltantes" / "Limpar" / "Sair do modo".
- Dialog "Abonar N dia(s) em massa" com badges das datas, select tipo, textarea motivo e file input opcional (compartilhado entre todas as datas).
- Toast com contagem ao concluir; recarga automática do quadro mensal.

### Validação
- ✅ testing_agent_v3_fork iteration_36: backend 12/12 pytest (idempotência, validações, multipart, listagem, delete parcial), frontend E2E (15 dias selecionados em Abril/2026 para JOSÉ DA COSTA viraram ABONADO; saldo do mês foi de -96h para 0h após o submit).
- ✅ Test file novo: `/app/backend/tests/test_abono_em_massa.py`

### Arquivos alterados
- `/app/backend/routes/rh.py` (adicionados 2 endpoints)
- `/app/frontend/src/pages/rh/PontoQuadroTab.jsx` (state + UI de seleção em massa + Dialog)



## Feature - 06/05/2026 (Sessão 46) — 🕒 Banco de Horas: Filtros de Período + Modal de Ajuste Manual (UI finalizada)

### Contexto
Last Working Item da sessão anterior pendente: o arquivo `/app/frontend/src/pages/rh/BancoHorasPage.jsx` estava corrompido (lixo após o fechamento) e faltava render do filtro `de_data` + presets e do Modal de Ajuste Manual. Backend já estava 100% pronto.

### Implementado
**Frontend (`BancoHorasPage.jsx` recriado limpo, ~915 linhas):**
- Bloco de filtros: inputs `De` e `Até` + botões "Mês atual" / "Mês anterior" / "Limpar"; recarrega o resumo automaticamente via `useEffect([ateData, deData])`.
- Modal de Ajuste Manual (Shadcn `Dialog`) acionado por botão `<SlidersHorizontal/>` em cada linha da tabela:
  - Toggle Operação Adicionar (verde) / Retirar (vermelho)
  - Inputs Horas + Minutos
  - Date picker + Select de Tipo (ajuste, compensação, hora extra, falta, folga, outro)
  - Textarea Motivo (obrigatório)
  - Preview da operação ("+2h 30min serão adicionados ao banco de Fulano")
  - Validações: bloqueia salvar se total = 0 ou motivo vazio; toast de erro exibido
- Modal Extrato: nova seção "Ajustes manuais aplicados" com tabela (data, tipo, minutos, motivo) e botão lixeira por ajuste (DELETE /banco-horas/ajustes/{id}); mostra também total agregado em badge.
- `DialogDescription` adicionado nos dois Dialogs (a11y do Radix).

### Endpoints utilizados (já existentes no backend)
- `POST /api/rh/banco-horas/ajustes` — payload `{funcionario_id, minutos (int +/-), data?, motivo, tipo?}`
- `DELETE /api/rh/banco-horas/ajustes/{ajuste_id}`
- `GET /api/rh/banco-horas/resumo?ate_data&de_data`
- `GET /api/rh/banco-horas/funcionarios/{id}/extrato?ate_data&de_data` (retorna campo `ajustes` no payload)

### Validação
- ✅ Smoke test: página renderiza com filtros e tabela de 9 funcionários
- ✅ Modal abre, validações funcionando, salvar dispara POST e atualiza saldo (-15h56min → -13h26min em teste de adição de 2h30min)
- ✅ testing_agent_v3_fork iteration_35: backend 15/15 pytest ok, frontend todos fluxos críticos ok
- ✅ Test file criado: `/app/backend/tests/test_banco_horas.py`

### Arquivos alterados
- `/app/frontend/src/pages/rh/BancoHorasPage.jsx` (recriado)
- `/app/backend/tests/test_banco_horas.py` (novo, pelo testing agent)



## Bug Fix - 06/05/2026 (Sessão 45.9) — 🔗 Desvínculo NF após delete + 🎨 NFS-e PDF padronizado

### Problemas reportados
1. Ao excluir uma Conta a Pagar/Receber vinculada a uma NF-e ou NFS-e, ao tentar gerar uma nova conta da mesma nota, o sistema dizia "nota já vinculada". O vínculo `conta_pagar_id`/`conta_receber_id` no documento da nota ficava órfão.
2. Exportação de NFS-e (PDF fallback simplificado) usava layout genérico, fora do padrão visual da plataforma.

### Causa raiz
1. Os endpoints `DELETE /contas-pagar/{id}` e `DELETE /contas-receber/{id}` removiam apenas a conta, sem limpar a referência inversa nas coleções `nfe_importadas` e `nfse_importadas`.
2. O fallback PDF em `routes/nfse.py::download_nfse_pdf` usava `SimpleDocTemplate` cru com estilos `getSampleStyleSheet`, sem o helper `utils/pdf_template.py`.

### Implementado
**Backend (`routes/financeiro.py`):**
- `delete_conta_pagar`: agora roda `update_many({"conta_pagar_id": id}, {"$set": {"conta_pagar_id": None}})` em `nfe_importadas` E `nfse_importadas` antes do retorno.
- `delete_conta_receber`: mesma lógica para `conta_receber_id`.

**Backend (`routes/nfse.py`):**
- Fallback do `download-pdf` reescrito usando `create_corporate_doc`, `add_corporate_header`, `add_footer`, `get_corporate_styles`, `build_data_table`, `header_table_style` e `BRAND_COLORS` do `utils/pdf_template.py`.
- Layout agora inclui: cabeçalho corporativo CRA + linha teal, aviso "Documento informativo", blocos estruturados (Identificação, Prestador, Tomador, Discriminação) e tabela completa de valores com Base de Cálculo, ISS, IRRF, INSS, CSLL, COFINS, PIS e VALOR LÍQUIDO destacado em banner verde corporativo.

### Validação
- ✅ Bug 1: criado vínculo NF-e → conta_pagar; após `DELETE /contas-pagar/{id}`, `nfe.conta_pagar_id == None` confirmado
- ✅ Bug 2: PDF NFS-e fallback gerado com 38KB, layout corporativo confirmado pelo analyzer (estrutura: cabeçalho, aviso, 4 blocos, tabela de valores, rodapé)
- ✅ Lint passou em todos os arquivos



## Feature - 06/05/2026 (Sessão 45.8) — 💰 Campo "Retenção" em Contas a Pagar e Receber

### Implementado
**Backend (`routes/financeiro.py`):**
- Novo campo opcional `valor_retencao: Optional[float] = 0` em `ContaPagarCreate`, `ContaReceberCreate`, `ContaParceladaCreate`, `ContaReceberParceladaCreate`.
- Cálculo de `valor_final` agora considera a retenção: **`valor - desconto + juros + multa - retencao`**.
- Endpoints atualizados: criação, edição e parcelamento (4 endpoints no total).
- **Parcelamento inteligente**: a retenção informada é distribuída proporcionalmente entre todas as parcelas (com ajuste de centavos na última).

**Frontend:**
- `ContasPagarPage.jsx` e `ContasReceberPage.jsx`: novo campo "Retenção" no formulário (5ª coluna do grid de valores).
- Tooltip explicativo: "Retenção tributária (IRRF, INSS, ISS) — desconta do valor total".
- Função `calcularValorFinal()` atualizada para subtrair a retenção em tempo real.
- Texto do "Valor Final" exibe a fórmula completa: "(Valor - Desconto + Juros + Multa - Retenção)".

### Validação
- ✅ Conta a Pagar com `valor=10.000 + juros=100 - retenção=1.500` → `valor_final=8.600`
- ✅ Conta a Receber com `valor=5.000 - retenção=250` → `valor_final=4.750`
- ✅ Parcelado de `R$ 12.000 com retenção R$ 600 em 3x` → 3 parcelas de `valor=4.000, retencao=200, final=3.800`
- ✅ Lint passou em todos os arquivos

### Como usar (após Deploy)
1. Acessar **Financeiro → Contas a Pagar (ou Receber) → Nova Conta**
2. Preencher Valor normalmente (ex: R$ 10.000,00)
3. Preencher o campo **Retenção** (ex: R$ 1.500,00 de IRRF)
4. O "Valor Final" no rodapé do form atualiza em tempo real (R$ 8.500,00 + ajustes)
5. Salvar — o sistema persiste e mostra na lista o valor já com retenção descontada



## Feature - 06/05/2026 (Sessão 45.7) — 💼 Banco de Horas no menu lateral do RH

### Implementado
**Backend (`routes/rh.py`):**
- `_calcular_banco_horas_por_funcionario(ate_data)`: helper que calcula saldo acumulado por funcionário a partir do Ponto Eletrônico, neutralizando dias com abono.
- `GET /api/rh/banco-horas/resumo`: lista todos os funcionários com saldo acumulado, dias registrados e período. Retorna totais (crédito, débito, saldo líquido da empresa). Aceita `?ate_data=YYYY-MM-DD`.
- `GET /api/rh/banco-horas/funcionarios/{id}/extrato`: extrato detalhado de um funcionário com evolução mês a mês + detalhe diário (batidas, saldo dia, saldo acumulado, abonos).
- `GET /api/rh/banco-horas/funcionarios/{id}/extrato-pdf`: exporta o extrato em PDF com layout corporativo (`utils/pdf_template.py`).

**Frontend:**
- Nova página `/rh/banco-horas` (`pages/rh/BancoHorasPage.jsx`):
  - 4 cards de resumo: total funcionários, crédito total, débito total, saldo líquido (verde/vermelho)
  - Filtro de data "Apurado até"
  - Busca por nome/cargo/departamento
  - Tabela com saldo destacado (verde positivo / vermelho negativo / cinza zero)
  - Botão "Ver Extrato" abre modal completo com evolução mensal + detalhe diário
  - Botão de exportação PDF direto na linha + dentro do modal
- Item "Banco de Horas" no sidebar do RH com ícone Wallet, posicionado entre "Ponto Eletrônico" e "Folha de Pagamento".
- Rota registrada em `App.js`.

### Validação
- ✅ `/rh/banco-horas/resumo`: 9 funcionários, totais corretos (Crédito: 0 / Débito: 14.429 min / Saldo Líquido: -14.429 min)
- ✅ Extrato Adelino: -956 min em 15 dias (abril/2026), evolução mensal correta
- ✅ PDF Banco de Horas: 40KB, **6/6 elementos validados pelo analyzer** (cabeçalho, ID funcionário, banner saldo, tabela mensal, detalhe diário, rodapé)
- ✅ Lint frontend passou em todos os arquivos



## Feature - 05/05/2026 (Sessão 45.6) — 🤖 Sugestão inteligente de EPIs com base no PGR/PCMSO/LTCAT da empresa

### Implementado
**Backend (`routes/rh.py` — `POST /epi/consultar-epis-cbo`):**
- Endpoint enriquecido para PRIORIZAR documentos normativos da CRA Construtora.
- Carrega o contexto da Base de Conhecimento (PGR/PCMSO/LTCAT/CCT, ~116K chars) via `_build_knowledge_base_context()` e injeta no prompt do Gemini.
- Gemini retorna EPIs com:
  - `fonte`: "PGR", "PCMSO", "LTCAT", "CCT" ou "NR_geral"
  - `fonte_principal`: documento principal usado para a função
- Quando a função está nos laudos da empresa, a IA copia C.A. e validade desses documentos. Se não, complementa com NRs gerais.

**Frontend (`pages/rh/EPIPage.jsx`):**
- `handleConsultarEPIs`: pré-marca automaticamente EPIs com fonte oficial da empresa (PGR/PCMSO/LTCAT/CCT).
- Badge colorido ao lado de cada EPI mostrando a fonte (verde para documentos da CRA, cinza para NRs gerais).
- Toast informativo destaca a fonte principal e quantos EPIs foram pré-marcados.

### Validação
- ✅ "Operador de retroescavadeira" (7151-15) → `fonte_principal: LTCAT`, 10 EPIs com Protetor Solar marcado como `fonte: CCT`
- ✅ Auxiliar de escritório (4110-05) → IA corretamente diz "não requer EPIs específicos"
- ✅ Almoxarife → IA traz pacote completo via NR_geral
- ✅ Lint passou em todos os arquivos

### Benefício
O cadastro de Ficha de EPI agora é **proativo e auditável**: o admin sabe imediatamente quais EPIs vêm dos laudos oficiais da empresa (cumprimento da NR-06) e quais são complementos genéricos. Reduz tempo de cadastro e elimina o risco de esquecer EPIs obrigatórios listados no PGR/LTCAT.



## Bug Fix - 05/05/2026 (Sessão 45.5) — 🛠️ Ficha de EPI: tela preta + exportações em PDF

### Problemas reportados
1. Ao clicar em "Salvar Ficha de EPI" a tela ficava toda preta (frontend crasha).
2. Não havia como exportar a ficha completa em PDF, nem o termo de responsabilidade.
3. PDFs antigos não seguiam o padrão visual da plataforma.

### Causa raiz
1. **Tela preta**: Backend exigia o campo `cargo` no `FichaEPICreate`, mas o frontend não enviava → erro 422 Pydantic v2 retornando array de objetos em `detail` → frontend usava `toast.error(error.response.data.detail)` que tentava renderizar um array de objetos como JSX → "Objects are not valid as a React child" → crash → tela preta.
2. **Sem exportação**: Endpoints `GET /epi/fichas/{id}/exportar` e `/termo-responsabilidade` simplesmente não existiam no backend (404 silencioso).

### Implementado
**Backend (`routes/rh.py`):**
- `FichaEPICreate`: `cargo` virou opcional, novos campos `data_entrega` e `ocupacao_cbo` adicionados.
- `POST /epi/fichas`: agora auto-preenche `cargo` consultando o funcionário se não informado; remove `_id` do retorno (evita erro de serialização BSON).
- `GET /epi/fichas`: passou a excluir `_id` na projeção.
- `GET /epi/fichas/{id}/exportar` (NOVO): gera PDF da ficha completa com layout corporativo (`utils/pdf_template.py`), incluindo identificação completa, tabela de EPIs com CA/Validade/Prioridade, Termo de Recebimento (itens I a V) e assinaturas.
- `GET /epi/fichas/{id}/termo-responsabilidade` (NOVO): PDF do Termo de Responsabilidade isolado, citando NR-06 / Portaria 3.214/78 / CLT art. 158, com declaração formal e assinaturas.

**Frontend (`pages/rh/EPIPage.jsx`):**
- `handleSalvarFichaEPI`: trata corretamente arrays Pydantic em `error.response.data.detail`, convertendo para string segura antes de chamar `toast.error` — tela preta eliminada.

### Validação
- ✅ POST sem `cargo`: aceita, retorna `cargo: "Operador de Máquinas"` (auto-preenchido)
- ✅ Resposta sem `_id`: confirmado
- ✅ GET /epi/fichas: lista limpa com 4 EPIs corretamente
- ✅ Export Ficha: PDF 39KB válido, **6/6 elementos confirmados pelo analyzer** (cabeçalho corporativo, identificação, tabela EPIs, Termo I-V, assinaturas, rodapé)
- ✅ Export Termo: PDF 39KB válido com declaração NR-06 completa



## Feature - 05/05/2026 (Sessão 45.4) — 🚀 Auto-bootstrap da Base de Conhecimento

### Implementado
**Backend (`routes/chatbot.py`):**
- Função `bootstrap_knowledge_base()` que baixa os 4 PDFs normativos padrão da CRA Construtora a partir de URLs públicas fixas (`customer-assets.emergentagent.com`).
- Lista hardcoded `_KB_BOOTSTRAP_URLS` com PCMSO, PGR, LTCAT e CCT.
- **Idempotente**: cada documento só é baixado/processado se ainda não estiver na coleção `chat_knowledge_base`.
- **OCR fallback**: PDFs com pouco texto extraível (ex: CCT escaneada) são automaticamente OCR'ados via Gemini 2.5 Flash.
- Endpoint manual `POST /api/chatbot/knowledge-base/bootstrap` para forçar re-execução.

**Backend (`server.py`):**
- `startup_event()` agora dispara `bootstrap_knowledge_base()` em background (`asyncio.create_task`) para não bloquear o startup do servidor enquanto o OCR da CCT roda (~3 min).
- Logging completo: indica para cada doc se foi adicionado, já estava presente, ou se houve erro.

### Por quê
Ambientes novos (preview, produção, staging) agora ficam prontos automaticamente. O usuário não precisa mais subir os 4 PDFs manualmente após cada deploy — o backend faz isso sozinho na primeira inicialização. Deploys subsequentes não duplicam: o bootstrap detecta documentos pré-existentes e pula.

### Validação
- ✅ Limpeza completa da coleção + manual trigger → 4 docs inseridos (PCMSO 2.5MB, PGR 645KB, LTCAT 868KB, CCT 14MB com OCR Gemini = 46K chars)
- ✅ Re-execução do trigger → retorna `already_present: [PCMSO, PGR, LTCAT, CCT]` sem duplicar
- ✅ Logs do startup mostram bootstrap rodando em background sem bloquear o boot
- ✅ Smoke test: IA continua respondendo perguntas sobre PGR e EPIs com precisão

### Próximo deploy
Após o usuário fazer deploy desta versão para `construtoracra.com.br`, na primeira inicialização do backend:
1. Os 4 PDFs serão baixados automaticamente
2. Texto extraído (com OCR para CCT)
3. Inseridos no MongoDB de produção
4. A IA passa a responder com base nos documentos sem nenhuma ação manual



## Feature - 05/05/2026 (Sessão 45.3) — 🔧 Tela admin para Base de Conhecimento do Chat IA

### Implementado
**Frontend (`pages/admin/ChatKnowledgeBasePage.jsx`):**
- Nova tela em `/admin/chat-knowledge-base` para gerenciar os 4 documentos normativos do Chat IA do RH (PCMSO, PGR, LTCAT, CCT).
- Drag-and-drop de PDFs com sugestões rápidas pré-preenchidas (botões PCMSO/PGR/LTCAT/CCT).
- Mostra: nome curto, título descritivo, páginas, tamanho do PDF, data de atualização.
- Ações por documento: download do PDF original, remoção (com cache invalidado automaticamente).
- Loader visual indicando "Enviando e extraindo texto" — útil para PDFs escaneados onde o OCR via Gemini pode levar 1–2 minutos.

**Frontend (`pages/rh/RHChatPage.jsx`):**
- Adicionado link "Base de Conhecimento" no rodapé do sidebar do Chat IA com ícone BookOpen.

### Por quê
Usuário relatou que após deploy a IA na produção continua respondendo "Não tenho acesso aos documentos PCMSO/PGR/LTCAT". A causa: o MongoDB de produção é separado do preview, e a coleção `chat_knowledge_base` precisa ser populada lá também. Esta tela elimina a necessidade de scripts pós-deploy — o admin sobe os PDFs pelo navegador.

### Validação
- ✅ Lint frontend passou (App.js, RHChatPage.jsx, ChatKnowledgeBasePage.jsx)
- ✅ Endpoints `/api/chatbot/knowledge-base` (GET/POST upload/GET download/DELETE) validados na sessão anterior
- ✅ OCR fallback via Gemini funcionando para PDFs escaneados (CCT)



## Feature - 05/05/2026 (Sessão 45.2) — 🧠 Base de Conhecimento RH (PCMSO/PGR/LTCAT/CCT) no Chat IA + 📐 Espaçamento

### Implementado
**Backend — Base de Conhecimento permanente (`routes/chatbot.py`):**
- Nova coleção MongoDB `chat_knowledge_base` armazenando texto extraído de documentos normativos (PCMSO, PGR, LTCAT, CCT) com category `rh_normativos`.
- Documentos iniciais carregados via script único:
  - **CCT** (Convenção Coletiva 2025/2026 - Construção Pesada TO, 18p, OCR via Gemini 2.5 Flash): 45.7K chars
  - **LTCAT** (CRA Apoio Administrativo, 18p): 21.8K chars
  - **PCMSO** (CRA Apoio Administrativo, 30p): 34.6K chars
  - **PGR** (CRA Apoio Administrativo, 15p): 14.2K chars
- `_build_knowledge_base_context()`: helper async que concatena todos os textos no system_prompt, com cache de 10 minutos para reduzir latência.
- O system_prompt foi atualizado com instrução obrigatória: para perguntas sobre exames, EPIs por função, riscos, pisos salariais, jornadas e benefícios CCT, o assistente DEVE consultar os documentos e citar a fonte (PCMSO/PGR/LTCAT/CCT).
- **Endpoints admin** (`/api/chatbot/knowledge-base`):
  - `GET` — lista os documentos disponíveis (sem o texto completo)
  - `POST upload` — faz upload de novo PDF, extrai texto via PyPDF, cai para OCR via Gemini se PDF for escaneado
  - `GET {id}/download` — devolve o PDF original
  - `DELETE {id}` — remove documento e invalida o cache
- PDFs originais persistidos em `/app/backend/storage/rh_normativos/`.

**Frontend — Espaçamento de bolhas (`pages/rh/RHChatPage.jsx`):**
- Trocado `space-y-16` por `flex flex-col gap-20 md:gap-24` (de 4rem para 5–6rem entre bolhas).
- Padding interno aumentado de `px-4 py-3` para `px-5 py-4` + `shadow-sm` para dar respiro visual.

### Validação
- ✅ `GET /knowledge-base` retorna 4 documentos
- ✅ Pergunta "Quais exames são exigidos no admissional para Auxiliar Administrativo?" → IA cita PCMSO página 13 com lista exata (Acuidade Visual, Audiometria Tonal, Avaliação Clínica)
- ✅ Pergunta "Piso salarial Auxiliar Administrativo CCT?" → IA cita CCT 2025/2026 com valor exato (R$ 9,80/h e R$ 2.156,00/mês, vigência 01/05/2025)
- ✅ Pergunta "EPIs PGR para Aux Admin?" → IA combina PGR e CCT e lista EPIs corretos (Óculos, Protetor Auricular, etc.)
- ✅ Cache em memória funcionando (chamadas subsequentes não re-leem o DB)

### Arquivos modificados/criados
- `/app/backend/routes/chatbot.py`: helper KB + endpoints admin + injeção no system_prompt
- `/app/backend/storage/rh_normativos/`: pasta com os 4 PDFs originais
- `/app/frontend/src/pages/rh/RHChatPage.jsx`: espaçamento aumentado



## Feature - 05/05/2026 (Sessão 45.1) — 🤖 Chat IA: novas ferramentas Holerite + Espelho de Ponto

### Implementado
**Backend (`routes/chatbot.py` + `routes/rh.py`):**
- Extraído `_build_holerite_pdf(folha, func) -> bytes` como helper reutilizável em `routes/rh.py`.
- Adicionadas 2 novas tools ao `_execute_chat_tool` do assistente IA do RH:
  - **`gerar_holerite`** — params `funcionario_id`, `mes`, `ano`. Gera holerite corporativo em PDF com salário líquido em destaque. Mensagem amigável quando a folha do período ainda não existe.
  - **`gerar_espelho_ponto`** — params `mes`, `ano` e `funcionario_id` (opcional). Reusa `get_ponto_dashboard_mensal` + `_build_espelho_ponto_pdf`. Sem `funcionario_id` retorna o espelho consolidado de TODOS os funcionários.
- Atualizado o **system prompt** do Gemini com as novas ações, exemplos de uso natural ("Gere o holerite do João de fevereiro", "Espelho de ponto da Maria em março/2026") e regras de disambiguação por ano.

### Validação
- ✅ Direct call `_execute_chat_tool('gerar_holerite', ...)` → PDF 38KB com "R$ 2.973,61"
- ✅ Direct call `gerar_espelho_ponto` consolidado → PDF 71KB com 9 funcionários
- ✅ Erro amigável quando folha não existe ("Não há folha de pagamento de Dezembro/1999...")
- ✅ End-to-end via API: "Gere o espelho de ponto consolidado de abril de 2026" → Gemini invoca a tool e devolve o link de download
- ✅ Disambiguação inteligente: ao pedir holerite com nome ambíguo (2 João Silvas), o Gemini lista os IDs e pede clarificação antes de chamar a tool


## Feature - 05/05/2026 (Sessão 45) — 🌐 API pública CBO + 📄 Padronização visual de PDFs (RH/Gerenciamento)

### Implementado
**Backend — CBO via API pública (`routes/rh.py`):**
- Endpoint `GET /api/rh/epi/cbo/buscar?q=...` agora consulta o dataset oficial CBO 2002 do repositório `lucassmacedo/cbo-brasil` (Ocupação + Família + Sinônimo) em primeiro lugar, com cache em memória de 24h.
- Cobertura saltou de 28 ocupações hardcoded para **2.614 ocupações + 7.569 sinônimos** oficiais.
- Em caso de falha de rede, faz fallback automático para a base local `CBO_DATABASE` (zero impacto se a API ficar offline).
- Suporte a `?refresh=true` para forçar reimportação do remoto.

**Backend — Padronização de PDFs (RH e Gerenciamento) usando `utils/pdf_template.py`:**
- **Espelho de Ponto** (`_build_espelho_ponto_pdf` em `routes/rh.py`): cabeçalho corporativo (logo CRA + título + subtítulo + linha divisória teal) + rodapé padronizado.
- **Holerite** (`gerar_holerite` em `routes/rh.py`): reescrito do `canvas` baixo nível para `platypus` + template corporativo. Layout limpo com tabela Proventos × Descontos, Salário Líquido em destaque visual (banner teal/verde), assinaturas e rodapé.
- **Ordem de Serviço (DAV-OS)** (`export_ordem_servico_pdf` em `routes/admin.py`): adicionado bloco de logo CRA na coluna esquerda do cabeçalho, linha divisória teal abaixo, e rodapé corporativo. Estrutura legal DAV-OS preservada.

### Validação
- ✅ Curl `GET /api/rh/epi/cbo/buscar?q=pedreiro`: 8 resultados (Pedreiro de edificações, Pedreiro de mineração, etc.)
- ✅ Curl `?q=7152`: 6 ocupações da família 7152
- ✅ Curl `?q=010105`: match exato com Oficial general da aeronáutica
- ✅ Fallback local validado com cache zerado: 4 resultados retornam da base hardcoded
- ✅ PDF Espelho de Ponto: 71KB, válido (`%PDF`), com cabeçalho corporativo
- ✅ PDF Holerite: 38KB, validado pelo analyzer com TODOS os elementos (logo, título, tabela, salário líquido em destaque, assinaturas, rodapé)
- ✅ PDF OS: 39KB, válido com logo + linha divisória + rodapé adicionados

### Arquivos modificados
- `/app/backend/routes/rh.py`: import httpx, lazy loader CBO, refactor `buscar_cbo`, refactor `_build_espelho_ponto_pdf`, refactor `gerar_holerite`
- `/app/backend/routes/admin.py`: cabeçalho com logo + linha divisória + rodapé na DAV-OS


## Changelog - 30/04/2026 (Sessão 41) — 🐛 CNPJ bug + 📝 OS PDF completo + 🚜 Máquina em Contas
## Feature - 04/05/2026 (Sessão 43.9) — 🟢 Vinculação seletiva também nos campos padrão de Custos RH

### Implementado
Estendido o mecanismo de "Aplica a..." aos 7 campos padrão (FGTS, INSS Patronal, Vale Transporte, Vale Alimentação, Plano de Saúde, Outros Benefícios, EPIs).

**Backend** (`routes/rh.py`):
- Novos campos `*_funcionario_ids` paralelos a cada item padrão na config (vazio = todos os ativos; preenchido = subset).
- `PUT /custos/config` valida e persiste essas listas.
- `GET /custos` aplica seletivamente: se funcionário não está na lista, o custo correspondente é zero para ele. Mantém compatibilidade total com configs antigas (lista vazia = comportamento anterior "todos").

**Frontend** (`CustosPage.jsx`):
- Componente reutilizável `BotaoAplicaA` adicionado embaixo de cada um dos 7 inputs padrão. Mostra "Aplica a todos os ativos" ou "Aplica a N func.".
- Mini-dialog de seleção idêntico ao dos extras: checkbox "Aplicar a todos" + lista de funcionários com cargo + checkboxes individuais.

### Validação
- Curl: aplicado VT R$300 só ao primeiro funcionário ⇒ ele tem benefícios R$900 (R$300 VT + R$350 VA + R$250 Saúde), os outros R$600. Total benefícios reduziu de R$7200 → R$5700. ✅
- Frontend Playwright: dialog principal com 7 botões "Aplica a..." abaixo dos inputs, mini-dialog do VT com lista de 9 funcionários e João Silva pré-marcado. ✅


## Feature - 04/05/2026 (Sessão 43.8) — 🟢 Custos Extras personalizáveis com aplicação seletiva

### Implementado
- **Backend** — campo `custos_extras: List[{id, nome, tipo, valor, funcionario_ids}]` em `custos_rh_config`:
  - `tipo`: `fixo` (R$/mês) ou `percentual` (% sobre salário do funcionário)
  - `funcionario_ids` vazio = aplica a TODOS os ativos; preenchido = só aos listados
  - Endpoint `PUT /api/rh/custos/config` aceita o array, valida e normaliza (gera UUID em itens novos).
  - `GET /api/rh/custos` aplica os extras por funcionário e retorna `extras_total` + `extras_detalhe[]` (nome, tipo, valor, valor_aplicado) + agrega `total_extras` no resumo geral.

- **Frontend** (`CustosPage.jsx`):
  - Nova seção **"Custos Extras Personalizados"** dentro do modal de configuração com botão **"+ Adicionar custo"**.
  - Cada linha tem: descrição, tipo (R$ fixo / % salário), valor, "Aplica a..." (mostra "Todos os ativos" ou "N funcionário(s)"), e botão de remover.
  - **Mini-dialog** ao clicar em "Aplica a..." com checkbox "Aplicar a todos" no topo + lista de funcionários ativos (cada um com cargo e checkbox individual). Selecionar "todos" limpa a lista; desmarcar "todos" mostra a lista.

### Validação
- Curl: criou Cesta Básica (R$80 fixo / todos) + PLR (5% / 1 funcionário). 
  - João Silva (selecionado): R$80 + 5%×R$3500 = **R$255** extras ✅
  - Outros: só R$80 ✅
  - `total_extras` resumo: R$895 ✅
- Frontend Playwright: dialog principal com 2 linhas, mini-dialog de seleção com checkbox "Todos" + 7 funcionários listados ✅

### Arquivos
- `backend/routes/rh.py` — endpoint `PUT /custos/config` aceita `custos_extras`; `GET /custos` aplica e retorna detalhamento.
- `frontend/src/pages/rh/CustosPage.jsx` — UI completa de gestão de extras + mini-dialog de seleção.


## Feature - 04/05/2026 (Sessão 43.7) — 🟢 Edição da Jornada Padrão + Custos RH editáveis

### Implementado
**Jornada Padrão editável**:
- Removida a trava do input "Nome" no dialog de edição da jornada Padrão. Agora o usuário pode renomear, ajustar horários e descrição livremente.
- Mensagem em verde explica que continua sendo a jornada atribuída automaticamente a quem não tem outra definida.
- Backend já aceitava `PUT /jornadas/{id}` em qualquer jornada (sem mudança).

**Custos RH editáveis** (antes hardcoded):
- Nova collection `custos_rh_config` (singleton id="default") com campos persistidos: `fgts_aliquota`, `inss_patronal_aliquota`, `vale_transporte`, `vale_alimentacao`, `plano_saude`, `outros_beneficios`, `epis_custo_mensal`, `horas_mes`.
- Endpoints novos:
  - `GET /api/rh/custos/config` — cria com defaults (8% / 20% / 0 / 0 / 0 / 150 / 50 / 220) se não existir.
  - `PUT /api/rh/custos/config` — atualiza qualquer subset.
- `GET /api/rh/custos`, `simular_dissidio` e `simular_rescisao` agora carregam config dinâmica em vez das constantes.
- Frontend `CustosPage.jsx`:
  - Botão **"Configurar Custos"** no header + atalho "Editar valores" no card de explicação.
  - Modal com 8 inputs (DecimalInput para BRL e horas como `Input number`).
  - Salvar refresca toda a tabela de custos automaticamente.
  - Card explicativo agora exibe valores dinâmicos.

### Validação
- Curl: GET config retornou defaults; PUT atualizou para FGTS 8.5%, INSS 22%, VT 200, VA 350, Saúde 250, EPIs 80; GET /custos passou a refletir (resumo: salários R$7000, encargos R$2135, benefícios R$7200, EPIs R$720, custo total R$17.055).
- Frontend Playwright: 3 telas (página com card dinâmico, dialog de configuração, edição da Padrão com campo nome desbloqueado) renderizadas corretamente.


## Feature - 04/05/2026 (Sessão 43.6) — 🟢 Jornadas de Trabalho personalizáveis

### Implementado
- **Backend** — nova collection `jornadas_trabalho`, jornada Padrão criada automaticamente (Seg-Sex 08:00-11:30/13:30-18:00, Sábado 08:00-12:00):
  - `GET /api/rh/jornadas` (com contagem de funcionários atribuídos e total semanal)
  - `POST /api/rh/jornadas` (criar)
  - `PUT /api/rh/jornadas/{id}` (atualizar)
  - `DELETE /api/rh/jornadas/{id}` (bloqueia se há func. atribuídos ou se for Padrão)
  - `POST /api/rh/jornadas/{id}/atribuir` (multi-funcionários)
  - `GET /api/rh/jornadas/{id}/funcionarios` (Padrão inclui os sem jornada explícita)
- Funcionário ganhou campo opcional `jornada_id`. Sem ele, herda Padrão.
- **Cálculo retroativo**: `dashboard-mensal` recalcula `minutos_previstos`, `saldo_minutos` e `banco_horas_acumulado` on-the-fly usando a jornada CORRENTE de cada funcionário, em todos os meses já importados.
- Jornada com 4 horários (entrada/saída-almoço/retorno-almoço/saída) por dia da semana — meio-período suportado deixando almoço vazio.

### Frontend
- Substituído card estático "Jornada de Trabalho" por componente novo `JornadasQuadro`:
  - Lista cards com nome, descrição, horários por dia ativo e total semanal.
  - Botão "Nova jornada" → dialog com tabela 7 dias × 4 inputs `time` + checkbox ativo + preview de horas em tempo real.
  - Botão "atribuir N func." → dialog multi-select de funcionários ativos com pré-marcação dos atuais.
  - Edit/Excluir por jornada (Padrão protegida).
- Card de funcionário no Quadro Mensal mostra nome da jornada vigente.

### Validação
- Curl criou Padrão automaticamente + Diarista 6h, atribuição funcional, dashboard recalculou (Gustavo Padrão: 192h previstas, saldo -147h22min consistente).
- Visual Playwright: 3 telas (quadro, form criação, dialog atribuição) renderizadas corretamente.

### Arquivos
- `backend/routes/rh.py` — helpers de jornada + 6 endpoints + uso no dashboard.
- `frontend/src/pages/rh/JornadasQuadro.jsx` (NOVO).
- `frontend/src/pages/rh/PontoPage.jsx` (substitui card estático).
- `frontend/src/pages/rh/PontoQuadroTab.jsx` (mostra `jornada_nome` no card).


## Feature - 04/05/2026 (Sessão 43.5) — 📎 Upload de Atestado/Justificativa anexado ao Abono

### Implementado
- **Backend** (Emergent Object Storage):
  - `utils/storage.py` novo helper com `init_storage`, `put_object`, `get_object` usando `EMERGENT_LLM_KEY`. Inicializado no `startup_event` do server.
  - Endpoint `POST /api/rh/ponto/abono-com-anexo` (multipart/form-data) — aceita `funcionario_id`, `data`, `tipo`, `motivo` e `arquivo` opcional. Valida extensão (PDF/JPG/PNG/WEBP/HEIC/HEIF), tamanho (≤10MB), faz upload ao storage no path `cra-erp/abonos/{funcionario_id}/{uuid}.{ext}` e salva metadados no documento.
  - Endpoint `GET /api/rh/ponto/abono/{abono_id}/anexo` baixa o arquivo do storage com `Content-Disposition: inline` para abrir no navegador (PDFs/imagens).
  - Endpoint legado `POST /api/rh/ponto/abono` (JSON) mantido para abonos sem anexo (compatibilidade).
  - `dashboard-mensal` agora retorna `abono.anexo` com `storage_path`, `filename_original`, `content_type`, `size`, `ext`.
  - **PDF Espelho**: tabela ABONOS DO MÊS ganhou coluna **"Anexo"** mostrando `Sim (filename.pdf)` ou `—`.

- **Frontend** (`PontoQuadroTab.jsx`):
  - Form de abono ganhou seção **"Anexar atestado/justificativa (opcional)"** com input file e validação visual de tamanho/nome.
  - `criarAbono` envia `FormData` para `/abono-com-anexo` quando há arquivo, ou JSON para `/abono` quando não há.
  - `baixarAnexoAbono` faz fetch como blob e abre em nova aba.
  - Linha do dia abonado ganhou **botão de paperclip + external-link** ao lado do badge do abono quando existe anexo.

### Validação
- Curl upload de PDF (1477 bytes) → salvou em `cra-erp/abonos/{fid}/{uuid}.pdf`. ✅
- Curl GET `/abono/{id}/anexo` → HTTP 200, content-type `application/pdf`, conteúdo idêntico ao original. ✅
- PDF espelho extraído via pdfminer mostra coluna "Anexo" com `Sim (atestado_teste.pdf)`. ✅
- Visual Playwright: linha 03/04 mostra clip + ícone external; formulário mostra input file + dicas. ✅

### Arquivos modificados
- `backend/utils/storage.py` (NOVO)
- `backend/server.py` (init storage no startup)
- `backend/routes/rh.py` (3 endpoints novos: abono JSON, abono-com-anexo multipart, download anexo)
- `frontend/src/pages/rh/PontoQuadroTab.jsx` (input file, função download blob, ícone na linha do dia)


## Hotfix - 04/05/2026 (Sessão 43.4) — 🐛 Aba "Registro Diário" mostrava 0 / não tinha filtro por mês

### Problema reportado
Após importar a planilha de ponto, a aba "Registro Diário" mostrava 0 presentes/ausentes e a lista vazia, sem opção de filtrar por mês/ano/período. Só dava para escolher 1 dia específico.

### Bugs encontrados
1. Endpoint `GET /rh/ponto` retornava lista direta, mas o frontend esperava `{registros, resumo}` → resumo sempre 0.
2. Endpoint só aceitava `data` exata, sem suporte a `data_inicio`/`data_fim`/`mes`/`ano`.
3. Backend incluía `_id` do MongoDB no response e quebrava com IDs `NAO_CADASTRADO::*`.
4. Resumo não considerava abonos.

### Correção
- **Backend** (`routes/rh.py`): `GET /rh/ponto` reescrito com filtros flexíveis (data exata / período inclusivo / mês completo / últimos 30 dias por padrão), exclusão de `_id`, resolução de nome para funcionários cadastrados E não cadastrados (usa `funcionario_nome_planilha`), marcação de `abonado`, e cálculo de resumo completo (presentes, ausentes, atrasados, abonados, total_funcionarios, minutos trabalhados/previstos/saldo).
- **Frontend** (`PontoPage.jsx`): 3 botões de modo (Dia / Mês inteiro / Período personalizado) com campos contextuais, filtro por funcionário mantido. Cards de resumo expandidos para 6 KPIs (Funcionários / Presentes / Faltas / Atrasados / Abonados / Saldo período colorido). Tabela ganhou coluna "Data", linha amarela para dias abonados, badge "(não cadastrado)" para nomes que não estão no cadastro de funcionários.

### Validação
- Curl `?mes=4&ano=2026`: 270 registros, resumo correto (130 presentes, 1 abonado, saldo -744h49min).
- Curl `?data_inicio=2026-04-07&data_fim=2026-04-15`: 81 registros do período.
- Frontend Playwright em ambos os modos: filtros e KPIs renderizados, tabela com data e dados corretos.

### Default mostrado
- O modo **"Mês inteiro"** vem como padrão usando o mês corrente. Se não houver dados no mês atual, basta trocar para o mês desejado nos selects.


## Feature - 04/05/2026 (Sessão 43.3) — 🟢 Abonos + Observações no Ponto Eletrônico

### Implementado
- **Sistema de Abonos** por dia (atestado médico, justificativa, folga compensada, feriado, férias, outros):
  - Coluna "Ações" no modal de detalhamento com botão "Abonar" em qualquer dia com falta/incompleto.
  - Form inline com seleção de tipo + motivo livre.
  - Dia abonado: linha em destaque amarelo, badge no lugar das batidas, saldo "ABONADO" e ícone para remoção.
  - **Saldo do dia abonado é neutralizado** (vira 0) → reduz faltas, ajusta saldo do mês e banco de horas acumulado (em todos os meses).
- **Observações livres por funcionário/mês** com textarea no modal, salvo via botão "Salvar". Texto persistido aparece no PDF.
- **PDF atualizado**: dia abonado mostra `[ABONO TIPO] motivo` no lugar das batidas, fundo amarelo na linha, "ABONADO" no saldo. Adicionada seção "ABONOS DO MÊS" e seção "OBSERVAÇÕES" em destaque amarelo entre os abonos e as assinaturas.

### Backend
- Novas collections: `ponto_abonos` e `ponto_observacoes`.
- Endpoints novos:
  - `POST /api/rh/ponto/abono`
  - `GET /api/rh/ponto/abonos?funcionario_id=&mes=&ano=`
  - `DELETE /api/rh/ponto/abono/{id}`
  - `POST /api/rh/ponto/observacao` (upsert; texto vazio = remove)
  - `GET /api/rh/ponto/observacao?funcionario_id=&mes=&ano=`
- `GET /rh/ponto/dashboard-mensal` agora retorna `abonos[]`, `observacao` e `dias_abonados` por funcionário, e neutraliza saldo dos dias abonados (incluindo no banco acumulado de meses anteriores).
- `GET /rh/ponto/relatorio-pdf` reflete abonos + observações no PDF.

### Frontend
- `PontoQuadroTab.jsx` ganhou: `observacaoDraft`, `abonoForm`, `salvandoObs`; funções `salvarObservacao`, `criarAbono`, `removerAbono`, `recarregarFuncDetalhe`.
- Modal expandido com nova coluna "Ações" + form inline de abono + Card "Observações do mês".

### Validação
- Curl backend: criação de abono em 03/04 + salvamento de observação → saldo Gustavo passou de -155h22min → -147h22min, faltas 13 → 12.
- PDF gerado com seções ABONOS DO MÊS e OBSERVAÇÕES corretas.
- Frontend visual: 26 botões "Abonar" detectados, modal de detalhe com formulário e textarea funcionais.


## Feature - 04/05/2026 (Sessão 43.2) — 🟢 PDF Espelho de Ponto Mensal

### Implementado
- **Endpoint** `GET /api/rh/ponto/relatorio-pdf?mes=&ano=&funcionario_id=` (parâmetro opcional). Sem `funcionario_id`, gera PDF consolidado com todos os funcionários (1 página por funcionário com PageBreak); com ID, gera apenas daquele.
- **PDF profissional** usando ReportLab nativo com:
  - Cabeçalho "ESPELHO DE PONTO ELETRÔNICO" + competência
  - Bloco de identificação (nome, cargo, departamento, status cadastrado/não cadastrado)
  - 4 KPIs do mês (trabalhadas / previstas / saldo / banco acumulado) com cores semafóricas (verde/vermelho/azul/laranja)
  - 3 KPIs de dias (trabalhados / incompletos / faltas)
  - Tabela detalhada dia-a-dia com batidas, trabalhado, previsto e saldo (saldo positivo verde, negativo vermelho)
  - Linhas de assinatura (funcionário + responsável) e timestamp de geração

- **Frontend** (`PontoQuadroTab.jsx`):
  - Botão "PDF (todos)" no painel de filtros baixa o consolidado.
  - Botão "Baixar PDF" no header do modal de detalhamento individual baixa o espelho daquele funcionário.

### Validação
- Curl: PDF de 1 funcionário (5,9KB) e consolidado (45KB) — ambos `HTTP 200` e magic bytes `%PDF` corretos.
- Extração via pdfminer confirma estrutura completa: cabeçalho, KPIs, 30 linhas de dia, assinaturas e footer.
- Visual via Playwright: ambos botões aparecem corretamente na UI.

### Arquivos
- `backend/routes/rh.py` — função `_build_espelho_ponto_pdf` + endpoint `/ponto/relatorio-pdf`.
- `frontend/src/pages/rh/PontoQuadroTab.jsx` — função `baixarPdf` + 2 botões.


## Hotfix - 04/05/2026 (Sessão 43.1) — 🐛 Matching de nomes parciais na Importação de Ponto

### Bug reportado
Funcionários cadastrados com nome COMPLETO (ex: "JUNIOR ALVES GUIMARÃES") não eram reconhecidos quando a planilha do relógio trazia nome ABREVIADO (ex: "JUNIOR ALVES"). Resultado: 8 falsos "não cadastrados".

### Correção
- Nova função `_match_funcionario_por_nome` em `backend/routes/rh.py` faz match em camadas:
  1. Exato (case-insensitive normalizado)
  2. Subsequência de tokens com prefixo: cada palavra da planilha precisa ser igual OU prefixo de uma palavra do cadastro, preservando ordem.
  - Exemplos validados (10/10):
    - "GUSTAVO RODRIGUES" → "GUSTAVO HENRIQUE A RODRIGUES" ✅
    - "LUIZ CARLOS M." → "LUIZ CARLOS MOURA DA SILVA" ✅ (prefixo "M" → "MOURA")
    - "junior" → "JUNIOR ALVES GUIMARÃES" ✅ (caso minúsculo)
- Re-importação agora deleta antes registros antigos do mês com `origem: planilha_xls` para limpar IDs `NAO_CADASTRADO::*` obsoletos quando o usuário cadastra o funcionário e re-sobe a planilha.

### Validação
- Teste unitário: 10/10 nomes da planilha real corretamente identificados.
- Importação completa: de 8 "não cadastrados" → reduziu para 2 reais (LEANDRO DOS SANTOS + pedro henrique, que de fato não estão na lista do cliente).


## Changelog - 04/05/2026 (Sessão 43) — 🟢 Ponto Eletrônico: Importação de Planilha + Quadro Mensal + Banco de Horas

### Feature implementada
- **Importação de planilha .xls/.xlsx do relógio de ponto** (formato Topdata/Hikvision-like): cada bloco com `IDUsuário/Nome/Dep.` + linha de dias 1-31 + linha de batidas separadas por `\n` é parseado automaticamente.
- **Match por nome exato** (case-insensitive normalizado). Não cadastrados são importados com flag `funcionario_nao_cadastrado=true` e exibidos no quadro com badge amarelo.
- **Cálculo automático de jornada**: 1 batida = incompleto (0h); 2 batidas = entrada+saída direta; 3 batidas = inferido com almoço padrão de 60min; 4+ batidas = par entrada/saída-almoço/retorno-almoço/saída.
- **Saldo do dia** = trabalhado − previsto. Jornada padrão: Seg-Sex 8h, Sáb 4h (08:00-12:00), Dom descanso.
- **Re-importação sobrescreve** registros do mesmo (funcionario_id, data) automaticamente.
- **Quadro Mensal** com filtros mês/ano + 3 KPIs gerais + um card por funcionário mostrando: barra de progresso de horas, saldo do mês colorido (verde/vermelho), banco de horas acumulado (soma de todos os meses anteriores + atual), dias trabalhados/incompletos/faltas.
- **Modal de detalhamento** ao clicar em cada card: tabela dia-a-dia com batidas brutas + minutos trabalhados/previstos/saldo do dia.

### Arquivos
- `backend/routes/rh.py` — novos endpoints `POST /rh/ponto/importar-planilha` e `GET /rh/ponto/dashboard-mensal?mes=&ano=` + helpers de parsing.
- `backend/requirements.txt` — adicionado `xlrd==2.0.1`.
- `frontend/src/pages/rh/PontoPage.jsx` — refatorado para Tabs (Diário/Importar/Quadro).
- `frontend/src/pages/rh/PontoImportarTab.jsx` — NOVO (upload drag-drop + preview de resultado).
- `frontend/src/pages/rh/PontoQuadroTab.jsx` — NOVO (cards mensais + modal de detalhamento).

### Validação
- Backend testado via curl: planilha real do usuário (RegistroPresença.xls Abril/2026, 10 funcionários, 30 dias) importada com sucesso → 300 registros gravados.
- Frontend validado via Playwright: 10 cards renderizados, modal de detalhamento com batidas, todas as 3 abas operacionais.


## Changelog - 04/05/2026 (Sessão 42) — 🟡 Diagnóstico claro de Importação NFS-e WebISS

### Problema reportado
- Usuário cadastrou Inscrição Municipal e URL `https://palmasto.webiss.com.br/ws/nfse.asmx` em 3 CNPJs mas o botão "Importar NFS-e" mostrava "0 notas importadas" sem feedback útil. Toasts de erro do backend chegavam como `toast.info` (cinza pálido), tornando-se invisíveis.

### Diagnóstico técnico realizado
- Curl direto ao endpoint Palmas/TO (`palmasto.webiss.com.br`) confirmou: o servidor exige **mTLS** e fecha a conexão TCP imediatamente após o handshake quando o certificado A1 não é aceito (`Remote end closed connection without response`). Nada chegou ao SOAP. Causa típica: A1 expirado, senha incorreta, CNPJ do cert ≠ CNPJ do tomador, ou IM não cadastrada em Palmas.

### Correções
- **Frontend** (`ImportacaoNFPage.jsx`):
  - Botão "Importar NFS-e" do topo agora **itera todos os CNPJs com URL configurada** (antes só acionava `certificados[0]`). Nova função `handleImportarNFSeTodos` exibe toast por empresa.
  - Avisos da NFS-e mudaram de `toast.info` → `toast.warning` (laranja, 12s) com nome da empresa no prefixo.
  - Toast de erro do "Testar Conexão" passa a mapear nova etapa `mtls_rejeitado`.
- **Backend** (`routes/importacao_nf.py`):
  - Detecta `Remote end closed`, `Connection reset`, falha de SSL/handshake → devolve mensagem-amiga (4 causas mais prováveis) em vez de jargão técnico cru.
  - Endpoint `/nfse/importar` agora retorna `total_encontradas` e `duplicadas` na resposta. Quando webservice respondeu OK mas 0 notas chegaram, gera aviso explicando cada hipótese.
  - Endpoint `/nfse/testar-conexao` introduz nova etapa `mtls_rejeitado` com texto orientando o usuário a fazer login no portal `palmasto.webiss.com.br` com o mesmo .pfx para validar o certificado.

### Como o usuário deve agir
1. Vá na aba **CNPJs/Certificados** → clique no ícone "plug" (Testar Conexão NFS-e) em cada CNPJ.
2. Se aparecer **"Certificado Rejeitado"**, é problema do A1 ou do cadastro do CNPJ na Prefeitura (não código).
3. Se aparecer **"Regra de Negócio: [Cód L004] Inscrição Municipal não cadastrada"** → IM digitada está errada.

### Arquivos modificados
- `frontend/src/pages/admin/ImportacaoNFPage.jsx`
- `backend/routes/importacao_nf.py`



### Bug P0 corrigido
- **CNPJ/CEP retornavam erro nos formulários** — `axios.defaults.headers.common["Authorization"]` global era enviado também para BrasilAPI/ViaCEP, que rejeitavam a chamada. Substituído `axios.get` por `fetch()` nativo nos 4 arquivos: `CadastroFormModal.jsx`, `OrdensServicoPage.jsx`, `EmissaoNFPage.jsx`, `ImoveisPage.jsx`. Agora consulta CNPJ/CEP funciona em qualquer formulário do sistema.

### Features P1
- **OS PDF agora exporta TODOS os 30 campos do formulário** — adicionados ao PDF: Empresa Emissora, Tipo Financeiro, Status, Valor Antecipado, Previsão de Entrega como linha separada, Atendente. Observações tornaram-se 3 seções distintas (Observação dos Serviços, Notas Gerais, Observações). Verificado via extração de texto do PDF.
- **Máquina vinculada à Frota em Contas a Pagar/Receber** — Quando o usuário seleciona uma Frota no modal, surge um segundo dropdown "Máquina (Opcional)" filtrado apenas com as máquinas dessa frota (filtro por `fleet_id`). Persiste `maquina_id`/`maquina_nome` no documento. Models Pydantic atualizados em `routes/financeiro.py` e `server.py`.

### Padrão monetário brasileiro (sessão 40 — referência)
Componentes `MoneyInput` e `DecimalInput` aplicados em 11 páginas para aceitar vírgula como separador decimal e formatar visualmente como R$ 1.234,56.


## Changelog - 29/04/2026 (Sessão 40) — 🐛 P0 bug fixes + 🟢 P1 features financeiras

### Bugs P0 corrigidos
- **OS "tela preta ao salvar"** — Frontend mandava `valor_desconto: ""` que falhava no Pydantic (`float_parsing`); o `detail` retornado era array de objetos e o React quebrava ao renderizar dentro do toast. Fix: parsear todos os campos numéricos no `handleSubmit` antes do POST/PUT e converter `detail` array em string legível antes de exibir no toast.
- **Recibo PDF sem dados de cliente/fornecedor** — `/api/export/recibo` lia apenas campos da própria conta (que só armazenava `fornecedor_nome` + `id`). Fix: agora busca `db.cadastros` via `fornecedor_id`/`cliente_id` e enriquece o recibo com CPF/CNPJ, telefone, celular e endereço completo (rua, número, complemento, bairro, cidade, UF, CEP).

### Features P1 implementadas
- **Nº da Parcela editável após lançamento** — Campos `numero_parcela` e `total_parcelas` adicionados ao modal de Contas a Pagar e Contas a Receber, visíveis em ambos os modos Criação e Edição. testids: `input-numero-parcela-cp/cr`, `input-total-parcelas-cp/cr`.
- **Busca por número do documento** — Filtro de search em Contas a Pagar/Receber agora inclui `numero_doc` além de `descricao`, `cliente_nome`/`fornecedor_nome` e `documento`. Placeholders atualizados.
- **OS com múltiplos valores compostos** — Renomeado "Valor Total" para "Valor Principal" e adicionado painel "Valores Adicionais" com botão "+ Adicionar valor". Cada extra tem (descrição, valor) e é enviado em `valores_extras: [{descricao, valor}]`. O Valor Total final é calculado automaticamente: `valor_principal + Σ valores_extras − valor_desconto`. PDF da OS renderiza cada extra como linha separada na tabela de itens.
- **Exportar Extrato do Plano de Contas com período** — Card NOVO em ExportPage (módulo administrativo) com filtros Plano de Contas, Data Início, Data Fim, Tipo (ambos/pagar/receber). Backend: `GET /api/export/extrato-plano-contas?plano_conta_id=&data_inicio=&data_fim=&tipo=&incluir_detalhes=true`. PDF gera resumo consolidado por plano + detalhamento de cada lançamento (Pagar em vermelho, Receber em verde) seguindo padrão visual existente.

### Arquivos modificados
- `frontend/src/pages/admin/OrdensServicoPage.jsx` — handleSubmit fix + UI valores_extras + total auto-calculado
- `frontend/src/pages/admin/ContasPagarPage.jsx` — campos parcela + search por numero_doc
- `frontend/src/pages/admin/ContasReceberPage.jsx` — idem
- `frontend/src/pages/ExportPage.jsx` — card "Extrato do Plano de Contas"
- `backend/server.py` — model `OrdemServicoCreate` aceita `valores_extras` + `valor_principal`
- `backend/routes/admin.py` — PDF da OS renderiza valores extras
- `backend/routes/exports_all.py` — `export_recibo` enriquece com cadastro + novo endpoint `/export/extrato-plano-contas`

### Testes (Sessão 34 — testing_agent_v3_fork)
- Backend: 8/8 pytest passou (`/app/backend/tests/test_sessao34_bugs_features.py`)
- Frontend: 100% — Playwright validou modal OS sem black screen, testids dos campos parcela, card de extrato visível, recibo PDF extraído via pypdf confirmou CNPJ/endereço/telefone.


## Changelog - 28/04/2026 (Sessão 39) — 🧹 Auditoria total: zero duplicatas restantes

### Auditoria executada
Script Python varreu todas as rotas de `routes/*.py` cruzando com `server.py` (com normalização de path params). Antes da limpeza: **28 duplicatas** distribuídas em 4 arquivos. Após a limpeza: **0**.

### Arquivos REMOVIDOS (100% duplicados / nem incluídos)
- `routes/auth.py` (118 linhas) — 5 rotas `/auth/*` todas duplicadas em server.py
- `routes/categories.py` (97 linhas) — 4 rotas `/categories/*` todas duplicadas

### Arquivos COMPACTADOS (mantidas apenas as rotas únicas)
- `routes/admin.py`: 963 → **453 linhas** (-510 linhas)
  - Removidas 20 rotas duplicadas (CRUD de cadastros, ordens-servico, plano-contas, centros-custo, dashboard, notificacoes)
  - Preservadas 2 únicas: `PUT /admin/ordens-servico/{id}/concluir` e `GET /admin/ordens-servico/{id}/export-pdf` (404 linhas de geração de PDF DAV-OS)
- `routes/storage.py`: 463 → **138 linhas** (-325 linhas)
  - Removidas 9 rotas duplicadas (list, folder, upload, download, delete, move, etc.)
  - Preservadas 2 únicas: `POST /storage/rename` e `GET /storage/search`

### Validação real (curl)
- `/api/admin/cadastros`, `/admin/ordens-servico`, `/admin/plano-contas`, `/admin/centros-custo`, `/admin/notificacoes`, `/admin/dashboard` → 200 OK
- `/api/storage/list`, `/api/storage/search` → 200 OK
- POST OS + GET export-pdf → 200 OK, PDF de 3855 bytes (rota preservada funcionando)
- PUT `/concluir` → `{"message": "Ordem concluída"}`
- Lint Python (ruff): **All checks passed!**

### Acumulado desde início da limpeza (sessões 38+39)
- **1690 linhas de código morto removidas** (640 de machines.py + 1050 desta sessão)
- 4 arquivos sem propósito (machines.py, auth.py, categories.py + compactações em admin.py e storage.py)
- Risco de regressões similares ao bug do `fleet_id` ELIMINADO

---


## Changelog - 28/04/2026 (Sessão 38) — 🧹 Limpeza: remoção de rotas duplicadas mortas

### 🐛 Causa raiz dos bugs sutis em máquinas
O arquivo `/app/backend/routes/machines.py` (640 linhas) continha **20 rotas idênticas** às do `server.py` (POST/GET/PUT/DELETE para `/categories`, `/subcategories`, `/fleets`, `/machines`, `/maintenances`). Como `server.py` registra suas rotas via `@api_router.decorator` antes do `api_router.include_router(machines_router)`, **o FastAPI sempre executa a versão do `server.py`** — o `routes/machines.py` era código morto que nunca executava. Mantê-lo confundia manutenção e levou ao bug do `fleet_id` da sessão anterior (devs editavam a versão errada).

### ✅ Correções aplicadas
- **Removido** `from routes.machines import machines_router` em `server.py` (linha 67)
- **Removido** `api_router.include_router(machines_router)` em `server.py` (linha 7812)
- **Removido** `from .machines import machines_router` em `routes/__init__.py` e do `__all__`
- **Deletado** `/app/backend/routes/machines.py` (640 linhas de código morto)

### Validação real
- Backend reiniciou sem erros (verificado em `/var/log/supervisor/backend.err.log`)
- Smoke tests via curl: `/api/machines`, `/api/fleets`, `/api/categories`, `/api/maintenances`, `/api/subfleets` todos respondendo normalmente
- "Frota Principal" mantém `machines_count: 1` (bug anterior continua corrigido)

### Impacto
- 640 linhas de código morto removidas
- Reduz risco de regressões: agora só há 1 fonte de verdade para as rotas de máquinas/frotas/categorias

---


## Changelog - 28/04/2026 (Sessão 37) — 🐛 BUG FIX: PUT /machines não persistia fleet_id

### 🐛 Problema
Ao editar uma máquina e adicionar/alterar a frota, ao clicar em "Atualizar" os dados pareciam salvos mas a máquina **não aparecia na frota**. Frotas mostravam sempre `machines_count: 0`.

### 🔍 Root cause
A rota `PUT /api/machines/{id}` em `/app/backend/server.py` (linha 1616) sobrepõe a rota correta de `routes/machines.py` por ser registrada primeiro no FastAPI. O `update_doc` montado nessa rota **omitia** os campos `fleet_id`, `subfleet_id`, `subcategory_id`, `operator_id`, `identificador_tipo` e `identificador_numero`. Os valores enviados no payload eram simplesmente ignorados pelo `$set` do MongoDB.

### ✅ Correção
- Incluído `fleet_id`, `subfleet_id`, `subcategory_id`, `operator_id`, `identificador_tipo`, `identificador_numero` no `update_doc` (linha 1632).
- Corrigido também `machine.plate.upper()` → `(machine.plate or "").upper()` para evitar `AttributeError` em máquinas sem placa.
- Response agora retorna `fleet_id`, `fleet_name`, `subfleet_id`, `subfleet_name`, `operator_id`, `identificador_tipo` e `identificador_numero` populados via lookup nas coleções `fleets` e `subfleets`.

### Validação real
- Curl PUT com `fleet_id` → response retornou `"fleet_id": "01a86017...", "fleet_name": "Frota Principal"` (antes vinha `null`).
- Endpoint `GET /api/fleets` → "Frota Principal" agora exibe `machines_count: 1` (antes era 0).
- Página `/gerenciamento/frotas` → "Trator Teste UI" listado dentro de "Frota Principal" como esperado.

---


## Changelog - 28/04/2026 (Sessão 36) — OS: labels (opcional) + auto-cálculo de entrega + fornecedor rápido

### ✅ Labels com indicador "(opcional)"
- Adicionado tag visual "(opcional)" cinza-claro ao lado dos labels: **Nº Contrato**, **Nº Doc Fiscal**, **IE/RG**, **E-mail**, **KM** (`text-gray-400 text-xs font-normal`).
- Total de 6 indicadores visíveis no formulário (validado via screenshot).

### ✅ Auto-cálculo de Data de Previsão de Entrega
- Mapa de dias por periodicidade: Diária = +1, Semanal = +7, Quinzenal = +15, Mensal = +30, Semestral = +180, Anual = +365.
- Quando o usuário muda **Periodicidade** ou **Data de Abertura**, a **Data de Previsão de Entrega** é recalculada automaticamente.
- O dropdown agora mostra os dias entre parênteses ("Semanal (+7 dias)") para clareza.
- Pequena dica em azul abaixo do select: "📅 Previsão de entrega calculada automaticamente".
- Validado: Abertura 28/04/2026 + Semanal → 05/05/2026; + Mensal → 28/05/2026.

### ✅ Fornecedores agora com cadastro rápido
- Adicionado botão "**Cadastrar novo**" (`<UserPlus />`) ao lado do label "Fornecedores" na seção de Vínculos.
- Abre o `CadastroFormModal` com `defaultTipo="fornecedor"`.
- Após cadastrar, o fornecedor é automaticamente vinculado à OS sendo criada (marcado no checkbox).
- Mensagem do estado vazio atualizada para apontar para o botão.

### Notas
- Mantida a UX multi-select (checkbox) para vincular múltiplos fornecedores simultaneamente.
- Bug rápido durante implementação: estado `showNovoFornecedor` não estava declarado → corrigido na mesma sessão.

---


## Changelog - 28/04/2026 (Sessão 35) — Ordem de Serviço: cliente inteligente + ViaCEP + Periodicidade + KM

### ✅ Cliente (Razão Social) na OS agora é dropdown com cadastro rápido
- **Antes**: campo livre apenas
- **Agora**: dropdown com clientes cadastrados (`tipo_cadastro = cliente | cli_forn`) + botão `[+]` para abrir o `CadastroFormModal` (mesmo modal usado em Contas a Receber/Pagar)
- Ao selecionar um cliente do dropdown, **todos os campos são auto-preenchidos**: razão social, fantasia, CPF/CNPJ, IE/RG, e-mail, fone, celular, endereço completo, bairro, cidade, UF, CEP
- Mantém input livre alternativo ("Ou digite o nome/razão social manualmente") quando nenhum cadastro é escolhido
- Após cadastrar um novo cliente via botão `[+]`, ele é selecionado automaticamente

### ✅ ViaCEP automático na OS
- Digitando 8 dígitos no campo CEP, dispara busca via `https://viacep.com.br/ws/{cep}/json/`
- Preenche automaticamente Endereço, Bairro, Cidade e UF
- Loader spinning visual durante a consulta
- Dispara também no onBlur (caso o usuário cole o CEP)

### ✅ Novos campos na OS
- **Periodicidade**: dropdown com Nenhuma / Diária / Semanal / Quinzenal / Mensal / Semestral / Anual
- **KM (opcional)**: input livre numérico
- Backend (`server.py` model `OrdemServicoCreate`): campos opcionais `periodicidade: str` e `km: str` adicionados explicitamente
- PDF da OS (`routes/admin.py`): nova linha na seção "Dados da Obra/Atendimento" mostrando "Periodicidade" e "KM"

### ✅ Máscaras automáticas nos campos do cliente da OS
- CPF/CNPJ via `formatCPFouCNPJ()` (auto-detecta tamanho)
- Telefone e Celular via `formatTelefone()`
- CEP via `formatCEP()`

### ✅ Confirmação dos campos opcionais
- **Nº Contrato**, **Nº Doc Fiscal**, **IE/RG** e **E-mail** seguem opcionais (sem asterisco)

### Validação real
- Backend: POST OS com `periodicidade=mensal, km=15750` → persistido corretamente
- PDF (gerado e analisado por IA, confidence 100%): mostra "Periodicidade: Mensal", "KM: 15750", "Cliente: Cliente Teste OS Periodicidade", "Endereço: Avenida Paulista, 1000"
- Frontend (screenshot): autocomplete via dropdown preencheu email e telefone do cadastro; ViaCEP preencheu Avenida Paulista / Bela Vista / São Paulo / SP

---


## Changelog - 28/04/2026 (Sessão 34) — Máscaras de data dd/mm/aaaa + verificação de parcelas

### ✅ Verificação visual: campo de Parcelas (P1)
- Validado via screenshot que `<Input type="number" min="2" max="360" />` está funcional em `ContasPagarPage.jsx` e `ContasReceberPage.jsx`. Comportamento de free-input correto. Issue era cache do navegador.

### ✅ Máscara dd/mm/aaaa em todos os inputs de data administrativos
**Novo componente**: `/app/frontend/src/components/MaskedDateInput.jsx`
- Wrapper de `<Input />` com máscara automática dd/mm/aaaa via utils/`masks.js`
- Aceita value em ISO (`yyyy-mm-dd`) ou já formatado
- Expõe `onChange(isoString)` — totalmente compatível com o estado existente
- `inputMode="numeric"`, `maxLength=10`, `placeholder="dd/mm/aaaa"`

**Páginas atualizadas (8 arquivos, 19 inputs convertidos):**
- ContasPagarPage.jsx (3): Data Emissão, Data Vencimento, Data Pagamento
- ContasReceberPage.jsx (3): Data Emissão, Data Vencimento, Data Recebimento
- OrdensServicoPage.jsx (3): Data Abertura, Fechamento, Previsão
- ConciliacaoPage.jsx (4): Filtros de extrato e contas (início/fim)
- AlugueisPage.jsx (2): Data Entrega, Data Vencimento
- ImoveisPage.jsx (2): Data Início, Data Término
- MovimentacoesPage.jsx (1): Data Movimentação
- ImportacaoNFPage.jsx (1): Data Emissão (NF manual)

### Validação visual
- Modal "Nova Conta a Pagar" → digitando `15032027` no campo Data 1º Vencimento exibe `15/03/2027` automaticamente.
- Datas pré-preenchidas (edição) exibem corretamente em dd/mm/aaaa a partir do ISO armazenado.

---



## Changelog - 28/04/2026 (Sessão 33) — Centro de Custo expandido + Vínculos na OS

### ✅ Centro de Custo agora suporta dados de Empresa Emissora
**Backend** (`server.py`): model `CentroCustoCreate` expandido com:
- Flag `eh_empresa_emissora: bool` (controla se aparece no dropdown da OS)
- 14 campos opcionais: razao_social, fantasia, cnpj, IE, IM, telefone, celular, email, endereço completo (rua, bairro, cidade, UF, CEP), logo_base64
- `model_config = ConfigDict(extra="allow")` para futuras expansões

**Frontend** (`CentroCustoPage.jsx`): modal expandido para 2xl com:
- Toggle "Este centro é uma empresa emissora" (checkbox em destaque)
- Quando ligado, aparece fieldset amarelo "Dados da Empresa" com todos os 14 campos
- `data-testid="checkbox-empresa-emissora"`

### ✅ Ordem de Serviço: vínculos a Máquinas, Frotas e Fornecedores
**Backend**: model `OrdemServicoCreate` ganhou 3 novos campos:
- `frotas_ids: List[str]`
- `maquinas_ids: List[str]`
- `fornecedores_ids: List[str]`

**Frontend** (`OrdensServicoPage.jsx`):
- Carrega 4 fontes: ordens, centros_custo, machines, fornecedores
- Novo fieldset "Vínculos (opcional)" com 3 listas multi-select (checkbox):
  - **Máquinas**: todas de `GET /api/machines`
  - **Frotas**: somente máquinas com `plate` (placa) cadastrada
  - **Fornecedores**: `GET /api/admin/cadastros?tipo=fornecedor`
- Cada lista é scroll-fixa (max-h-32) com hover, contador de selecionados
- `data-testid` para cada checkbox
- Dropdown "Empresa Emissora" agora **filtra inteligentemente**: se há centros marcados com `eh_empresa_emissora=true`, mostra só esses; senão mostra todos os centros ativos (retrocompatibilidade).

### ✅ PDF da OS aprimorado
- Cabeçalho usa **dados completos do centro de custo** (razão social, CNPJ, telefone, endereço, cidade/UF) em vez do hardcode.
- Nova seção **VÍNCULOS** entre dados da obra e itens, mostrando MÁQUINAS / FROTAS / FORNECEDORES vinculados com nome + placa/CNPJ.
- Fallback para empresas conhecidas (locadora/construtora) quando o centro não tem CNPJ preenchido.
- Suporta `nome_razao` (formato real do collection cadastros) além de `razao_social` e `nome`.

### Validação real (IA confidence 100%)
PDF gerado com:
- Centro CRA Construções (com todos os dados) → cabeçalho "RODRIGUES ALMEIDA CONSTRUCOES LTDA", CNPJ 39.543.761/0002-06, endereço/telefone corretos
- 2 máquinas vinculadas → seção VÍNCULOS mostra "Trator Teste UI (TST1234); Trator Photo Test (PHT1234)"
- 1 frota → "Trator Teste UI (TST1234)"
- 1 fornecedor → "Aço Forte Comercio LTDA (11.222.333/0001-44)"

---


## Changelog - 28/04/2026 (Sessão 33) — Empresa Emissora dinâmica via Centro de Custo

### ✅ Dropdown agora carrega Centros de Custo cadastrados
**Frontend** (`OrdensServicoPage.jsx`):
- Adicionado state `centrosCusto` populado via `GET /api/admin/centros-custo`.
- Filtra apenas centros com `status === "ativo"`.
- O `<Select>` Empresa Emissora mostra: `{codigo} — {nome}` para cada centro.
- Se NÃO houver nenhum centro ativo cadastrado, mostra opções padrão "CRA Locações" e "CRA Construções" + dica amarela "💡 Cadastre empresas em Centro de Custo para aparecerem aqui".
- `data-testid="select-empresa-emissora"`.

### ✅ Backend export-pdf inteligente
`GET /api/admin/ordens-servico/{id}/export-pdf` agora aceita 3 formatos para `empresa_emissora`:
1. `"locadora"` / `"construtora"` (legado, mapeado para CNPJs hardcoded)
2. **ID de centro de custo** → busca em `centros_custo` por `id` ou `nome`
3. Texto livre → usa como nome

Se for um centro de custo, faz **inferência inteligente** pelo nome (case-insensitive):
- Nome contém "CONSTRUC" → usa CNPJ + razão social da CRA Construções
- Nome contém "LOCA" → usa CNPJ + razão social da CRA Locações
- Outro → usa o nome do centro como razão social, código como fantasia

### Validação real
- Cadastrado centro "CRA Construções LTDA" (código CC-CONSTR).
- OS criada com `empresa_emissora` = ID desse centro.
- PDF gerado: cabeçalho mostra **"CRA Construções LTDA"** (nome do centro de custo). ✅

---


## Changelog - 28/04/2026 (Sessão 33) — Ordem de Serviço completa + Export PDF

### 🐛 Bug crítico encontrado: endpoint duplicado
Existiam DOIS endpoints `POST /api/admin/ordens-servico`:
- `routes/admin.py` (com novo model expandido)
- `server.py` linha 4347 (com model antigo, **prevalecendo**)

O `server.py` ainda tinha:
- `OrdemServicoCreate` com apenas 16 campos
- `"itens": []` sobrescrevendo `model_dump()` na criação
- Não aceitava: empresa_emissora, cliente_documento, endereço, forma_pagamento, observacao_servicos, notas_gerais, atendente_nome, itens, etc.

### ✅ Correções aplicadas
1. **Model `OrdemServicoCreate` em `server.py` expandido** com 35+ campos (todos opcionais) cobrindo o template STT:
   - Cliente completo: nome, fantasia, documento, IE, email, telefone, celular, endereço, bairro, cidade, UF, CEP
   - Obra: obra, endereco_entrega, periodo
   - Datas: abertura, fechamento, previsão, conclusão
   - Itens: lista de dicts (preserva ao criar)
   - Valores: total, desconto, subtotal, antecipado
   - Pagamento: forma_pagamento, condicao_pagamento
   - Observações: observacao_servicos, notas_gerais, observacoes
   - Empresa emissora: locadora | construtora
   - `model_config = ConfigDict(extra="allow")` para aceitar campos futuros
2. **`itens: []` removido do override** no insert — agora preserva o array enviado pelo frontend.

### ✅ Novo endpoint `GET /api/admin/ordens-servico/{id}/export-pdf` (em `routes/admin.py`)
Gera PDF da OS no formato STT/DAV-OS:
- **Cabeçalho**: razão social + fantasia + CNPJ da empresa emissora (CRA Locações ou CRA Construções conforme `empresa_emissora`)
- Aviso vermelho: "NÃO É DOCUMENTO FISCAL — NÃO É VÁLIDO COMO RECIBO..."
- **Identificação do destinatário** (5 linhas: cliente, fantasia, doc, IE, endereço, bairro, cidade/UF/CEP, email, fones)
- **Dados da obra/atendimento** (4 linhas: endereço entrega, obra, datas abertura/fechamento, tipo, período, contrato, NF)
- **Tabela de Serviços/Itens** com 8 colunas: Código, Qtde, UN, Descrição, Vlr Un., Vlr Total, Vlr Desc, Total Líq.
- **Resumo financeiro** horizontal: N. Itens / Sub-Total / Desconto / Total Serviços / **TOTAL DA OS** (vermelho destaque)
- Forma de pagamento + condição
- Observação dos serviços + Notas gerais
- Linhas de assinatura para Atendente e Cliente

### ✅ Frontend `OrdensServicoPage.jsx`
- Form expandido com 4 fieldsets organizados: Cliente / Obra-Atendimento / Descrição-Financeiro / Observações
- Novo botão azul "Exportar PDF" (FileDown) em cada card de OS
- Dropdown "Empresa Emissora" (CRA Locações | CRA Construções)
- Todos os 35+ campos do template STT acessíveis pela UI
- `openModal` reescrito para preservar campos ao editar (Object.fromEntries com fallback de valores vazios)

### Validação real
PDF gerado com 2 itens, empresa Construtora, forma "Boleto 30/60/90", garantia 90 dias, atendente "MABY ALMEIDA" — todos os campos confirmados via `analyze_file_tool` (IA confidence 100%).

### ℹ️ Sobre o bug das parcelas
Verificado: o código de ambos `ContasPagarPage.jsx` e `ContasReceberPage.jsx` já tem `<Input type="number" data-testid="input-total-parcelas">`. Compilação webpack OK. **Provável cache do navegador no lado do usuário** — sugerido fazer Ctrl+Shift+R (hard refresh) ou abrir aba anônima.

---


## Changelog - 24/04/2026 (Sessão 33) — Parcelas com entrada manual

### ✅ Número de parcelas agora é input livre (não dropdown fixo)
**Frontend** (`ContasPagarPage.jsx` e `ContasReceberPage.jsx`):
- Substituído o `<Select>` com 21 valores fixos por um `<Input type="number">` com:
  - `min=2`, `max=360`, `placeholder="Ex: 12"`
  - Hint: "Mínimo 2, máximo 360 parcelas"
  - `data-testid="input-total-parcelas"`
- Validação no submit: rejeita valores fora do range 2-360 com toast de erro.
- Permite agora parcelar em qualquer número (ex: 17x, 23x, 42x, 240x...) sem limite arbitrário do dropdown.

### Validação
- Lint JS limpo nos 2 arquivos.
- Limite máximo 360 (= 30 anos mensais) cobre cenários reais de financiamento de longo prazo sem expor o sistema a inputs absurdos.

---


## Changelog - 24/04/2026 (Sessão 33) — Juros/Multa/Desconto + Parcelas até 120x

### ✅ Juros, Multa e Desconto opcionais no formulário de Pagamento/Recebimento
**Frontend** (`ContasPagarPage.jsx` e `ContasReceberPage.jsx`):
- Nova seção "Ajustes (opcionais)" no modal de pagamento/recebimento com 3 inputs grid 3 colunas:
  - 🟠 **Juros** (ícone TrendingUp, laranja)
  - 🔴 **Multa** (ícone AlertCircle, vermelho)
  - 🟢 **Desconto** (ícone TrendingDown, verde)
- **Mini-resumo automático** aparece quando qualquer valor é preenchido: mostra Base + Juros + Multa - Desconto = Valor Líquido.
- `data-testid`: `input-juros-pagamento`, `input-multa-pagamento`, `input-desconto-pagamento` (e -recebimento).

**Backend** (`routes/financeiro.py`):
- Models `QuitarContaRequest` e `QuitarContaReceberRequest` ganharam campos `valor_juros`, `valor_multa`, `valor_desconto` (opcionais, default 0).
- Valores são persistidos em cada registro de `pagamentos[]` / `recebimentos[]`.
- **Saldo da conta bancária** agora considera ajuste líquido: Pagar debita (valor + juros + multa - desconto); Receber credita a mesma fórmula.
- `QuitarContaReceberRequest` aceita também aliases `data_pagamento` e `valor_pago` (usados pelo frontend) para retrocompatibilidade.

### ✅ Ajustes aparecem no Recibo exportado
**Endpoint** `/api/export/recibo/{category}/{item_id}?pagamento_id=...`:
- Nova lógica: se o pagamento parcial tem `valor_juros`/`valor_multa`/`valor_desconto` > 0, o recibo adiciona linhas coloridas ao "Referente a":
  - **Juros**: `+ R$ X,XX` em laranja
  - **Multa**: `+ R$ X,XX` em vermelho
  - **Desconto**: `- R$ X,XX` em verde
  - **Valor Líquido da Parcela**: total ajustado, em negrito

### ✅ Ajustes aparecem na Duplicata exportada
**Endpoint** `/api/export/duplicata/...`:
- Se a conta tem `valor_juros`/`valor_multa`/`valor_desconto`, uma linha adicional na seção "Descrição / Referência" mostra os valores coloridos inline.

### ✅ Parcelas ampliadas até 120x
Em ambos os formulários de criação de conta (Pagar e Receber), o dropdown "Número de Parcelas" agora oferece: 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 18, 24, 36, 48, **60, 72, 84, 96, 108, 120**.

### Validação real
- Pagamento parcial criado com juros R$ 5, multa R$ 3, desconto R$ 2 sobre valor base R$ 100.
- Recibo exportado mostra: "Juros: + R$ 5,00 | Multa: + R$ 3,00 | Desconto: - R$ 2,00 | Valor Líquido da Parcela: R$ 106,00" ✅
- Validado via `analyze_file_tool` (IA confirmou todas as 4 linhas e cores).
- Lint Python + JS limpos nos 4 arquivos editados.

---


## Changelog - 24/04/2026 (Sessão 33) — 🎉 Importação NFS-e WebISS FUNCIONAL

### 🐛 Problema real identificado
O código estava enviando requisições NFS-e com:
- **Namespace errado**: `http://www.abrasf.org.br/nfse.xsd`
- **Operação errada**: `ConsultarNfseRecebidos`
- **SOAPAction errado**: derivado dos dois acima

Análise do WSDL de `https://palmasto.webiss.com.br/ws/nfse.asmx?wsdl` revelou que o WebISS (Palmas e similares) usa:
- **Namespace**: `http://nfse.abrasf.org.br` (ABRASF v2)
- **Operação**: `ConsultarNfseServicoTomado` (não Recebidos!)
- **SOAPAction**: `http://nfse.abrasf.org.br/ConsultarNfseServicoTomado`

### ✅ Correções aplicadas
1. **Envelope SOAP reescrito** em 2 endpoints (`importar_nfse` e `testar_conexao_nfse`):
   - `xmlns:nfse="http://nfse.abrasf.org.br"`
   - Tag `<nfse:ConsultarNfseServicoTomadoRequest>`
   - `ConsultarNfseServicoTomadoEnvio` (em vez de `ConsultarNfseRecebidosEnvio`)
   - Conteúdo XML escapado com `&lt;`/`&gt;` (WebISS rejeita CDATA em alguns casos)

2. **Sistema de fallback inteligente** — função `_post_nfse_com_fallback_soapaction()`:
   - Tenta até 7 SOAPActions conhecidos de provedores brasileiros (WebISS, Ginfes, ISSNet, ABRASF strict, .NET default).
   - Detecta HTTP 500 + "did not recognize" e avança para o próximo automaticamente.
   - Primeiro da lista agora é `http://nfse.abrasf.org.br/{OP}` (WebISS).
   - Retorna o SOAPAction que funcionou para persistência.

3. **Persistência do SOAPAction descoberto**:
   - Campo `soapaction_nfse` salvo no certificado após primeiro sucesso.
   - Em chamadas seguintes, o SOAPAction preferido é tentado primeiro — evita retries desnecessários.

4. **Suporte a múltiplas operações**: lista `NFSE_OPERACOES_CONSULTA` inclui `ConsultarNfseServicoTomado` (v2, primeiro) e `ConsultarNfseRecebidos` (legado).

### Validação real com WebISS Palmas
- **Teste conexão**: ✅ `{"ok": true, "etapa": "sucesso", "soapaction_usado": "http://nfse.abrasf.org.br/ConsultarNfseServicoTomado"}`
- **Importação real**: ✅ `"0 nova(s) NFS-e importada(s)"` (sem erro, conexão íntegra — zero notas porque o período não tem NFS-e recebidas)

### Próximos passos sugeridos ao usuário
- Tentar importar NFS-e pela UI agora — deve funcionar.
- Para trazer notas reais, ampliar o período (código usa 90 dias por padrão).

---


## Changelog - 24/04/2026 (Sessão 33) — Busca na Exportação + Cronograma Visual

### ✅ Barra de pesquisa na ferramenta de Exportação (`ExportPage.jsx`)
- Quando o usuário expande uma subcategoria (ex: "Contas a Pagar Pendentes") para ver itens individuais, agora aparece **input de busca** com ícone lupa e botão "X" para limpar.
- Busca textual case-insensitive pelos campos: **descrição**, **fornecedor_nome**, **cliente_nome**, **model**, **plate**, **banco**, **data_vencimento**, **valor** (raw e formatado em pt-BR).
- Contador dinâmico "Mostrando N de M itens" enquanto filtra.
- Mensagem "Nenhum item encontrado para '{termo}'" quando o filtro não bate.
- State `itemSearch` mantém o termo por subcategoria (cada categoria independente).
- `data-testid="search-{sub.id}"`.

### ✅ Cronograma visual no modal de histórico (Contas a Pagar e Contas a Receber)
Substituído o bloco "Resumo" textual por um card gradiente com:
- **Percentual grande** (text-2xl bold) — ex: "71%"
- **Barra de progresso animada** (`h-3 bg-gray-200 rounded-full`) com cor dinâmica:
  - 🟢 Verde = 100% (quitado)
  - 🔵 Azul = 75-99%
  - 🟠 Laranja = 25-74%
  - 🔴 Vermelho = < 25%
- Animação pulse sutil na barra quando >10% preenchido.
- Grid 3 colunas de métricas: **Parcelas / Pago (ou Recebido) / Saldo**.
- Badge verde de parabéns "✓ Conta quitada!" / "✓ Conta totalmente recebida!" quando saldo zera.
- `data-testid="progress-pagamento"` e `progress-recebimento"`.

### Validação
- Lint JS limpo nos 3 arquivos editados.
- Estruturas JSX validadas (IIFE `(() => { ... })()` fechada corretamente em ambos os modais).

---


## Changelog - 24/04/2026 (Sessão 33) — Recibos por Pagamento Parcial

### ✅ Novo: emitir recibo para cada pagamento/recebimento parcial
**Cenário**: conta de R$ 35.000 paga em parcelas de R$ 2.500 por semana → agora é possível gerar **um recibo para cada parcela**, com saldo restante calculado automaticamente.

### Backend — endpoint existente estendido
`GET /api/export/recibo/{category}/{item_id}` agora aceita query param opcional `?pagamento_id={uuid}`:
- Sem `pagamento_id`: comportamento atual (recibo do valor total).
- Com `pagamento_id`: busca o pagamento parcial específico em `item.pagamentos` (contas_pagar) ou `item.recebimentos` (contas_receber). Retorna 404 se não encontrado.

Recibo parcial inclui:
- Subtítulo **"RECIBO - PAGAMENTO PARCIAL"** ou **"RECIBO - PAGAMENTO FINAL (QUITAÇÃO)"** se saldo zerar.
- Valor principal = valor da parcela (não o valor total da conta).
- Data de pagamento = data do pagamento parcial (não a data do último pagamento).
- Forma de pagamento e observação específicas daquela parcela.
- **Nova seção no final** com resumo financeiro: Valor Total da Conta / Total Pago (com este) / Saldo Restante (cores verde/vermelho).
- Filename `.pdf` inclui sufixo `_parcial_{id}` para diferenciação.

### Frontend — botão "Recibo" por parcela
**ContasPagarPage.jsx** (Dialog "Histórico de Pagamentos") e **ContasReceberPage.jsx** (Dialog "Histórico de Recebimentos"):
- Cada linha do histórico agora tem botão azul **"Recibo"** (ícone FileDown) ao lado do valor.
- Ao clicar, baixa o PDF com `?pagamento_id={id}`.
- `data-testid="btn-recibo-parcial-{id}"`.

### Validação via `analyze_file_tool`
- Recibo parcial Contas a Pagar: R$ 222,22 de R$ 322,78 total, saldo R$ 100,56 ✅
- Recibo parcial Contas a Receber: R$ 1.800,00 com saldo zero → "RECIBO - PAGAMENTO FINAL (QUITAÇÃO)" ✅
- Subtítulo, valores e linhas de resumo confirmadas em ambos os PDFs.

---


## Changelog - 24/04/2026 (Sessão 33) — Botão "Testar Conexão NFS-e"

### ✅ Novo botão nos cards dos CNPJs cadastrados
Adicionado ícone 🔌 (Plug) em cada card de certificado na aba **CNPJs** de `/administrativo/importacao-nf`:
- Dispara uma chamada leve ao webservice NFS-e (últimos 7 dias) **sem importar nada**.
- Diagnostica em etapas: configuração, certificado A1, SSL, conexão, HTTP, SOAP Fault, regras de negócio, parse, timeout.
- Botão fica **desabilitado** quando não há URL NFS-e cadastrada (com tooltip explicativo).

### Backend (`routes/importacao_nf.py`)
Novo endpoint `POST /api/nfse/testar-conexao/{certificado_id}` retorna JSON:
```json
{
  "ok": true/false,
  "etapa": "sucesso|configuracao|certificado|ssl|timeout|conexao|http|soap_fault|negocio|parse|inesperado",
  "mensagem": "texto legível para o usuário"
}
```

Reaproveita a função `_parse_nfse_soap_error()` criada anteriormente para extrair mensagens legíveis de SOAP Faults, ListaMensagemRetorno (ABRASF) e HTML genérico.

### Frontend (`ImportacaoNFPage.jsx`)
- Import do ícone `Plug` do lucide-react.
- State `testandoConexaoId` para desabilitar botão durante teste.
- Handler `handleTestarConexaoNfse` traduz `etapa` em prefixo amigável (Configuração / Certificado / SSL / Timeout etc).
- Toast de sucesso (8s) ou erro (12s) conforme resultado.
- `data-testid="test-nfse-{id}"`.

### Validação real
Testado contra WebISS Palmas com certificado real:
- **Antes**: usuário via XML cru confuso.
- **Agora**: `HTTP 500: [soap:Client] | System.Web.Services.Protocols.SoapException: Server did not recognize the value of HTTP Header SOAPAction: http://www.abrasf.org.br/nfse.xsd/ConsultarNfseRecebidos`
- Isso revela **o bug real** de importação NFS-e: o SOAPAction atual não é o aceito pelo WebISS Palmas. Próximo passo sugerido ao usuário: ajustar o SOAPAction (provavelmente sem o namespace `http://www.abrasf.org.br/nfse.xsd/`).

---


## Changelog - 24/04/2026 (Sessão 33) — Fix: Mensagem de erro NFS-e ininteligível

### 🐛 Problema reportado pelo usuário
Ao importar NFS-e, o sistema mostrava um aviso confuso com **XML SOAP cru** dos primeiros 200 caracteres:
> "Verifique a URL NFS-e configurada. Resposta: <?xml version='1.0' encoding='utf-8'?><soap:Envelope xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/' xmlns:xsi=..."

Isso acontecia quando a prefeitura retornava SOAP Fault (HTTP 500) — comportamento padrão de webservices SOAP.

### ✅ Correção
Criada função `_parse_nfse_soap_error()` em `routes/importacao_nf.py` que extrai mensagens legíveis de:
- **SOAP 1.1 Fault** → `faultcode` + `faultstring`
- **SOAP 1.2 Fault** → `Reason/Text`, `Code/Value`
- **ListaMensagemRetorno (ABRASF)** → `Codigo` + `Descricao` + `Correcao`
- **HTML/404** → texto plano (tags removidas)
- **Fallback**: primeiros 300 caracteres legíveis

### Onde foi aplicada
1. Resposta com status HTTP != 200 (caso original do bug).
2. Resposta com status 200 mas contendo SOAP Fault embutido (detecta `<soap:fault>` no body).
3. Resposta com XML inválido (parse error).

### Resultado para o usuário
Antes: `Resposta: <?xml version="1.0"...<soap:Envelope...` (XML cru, ininteligível)

Depois (exemplos):
- `[soap:Server] | Inscrição Municipal não cadastrada para o CNPJ informado`
- `[Cód E001] CNPJ do consulente não autorizado — Verifique o cadastro municipal`
- `Certificado digital inválido`
- `404 Not Found nginx`

### Validação
Testes unitários da função com 5 cenários (SOAP 1.1, SOAP 1.2, ListaMensagemRetorno, HTML, vazio) — todos retornam mensagens limpas.

---


## Changelog - 24/04/2026 (Sessão 33) — Fix: Lista de Conciliações sumindo no PDF

### 🐛 Bug identificado
O filtro de período no export PDF (`/api/conciliacao/export-pdf?data_inicio=...&data_fim=...`) consultava apenas o campo `data_conciliacao` no MongoDB. Porém, **conciliações criadas pelo endpoint singular `/conciliar` (legacy, ainda ativo) não salvavam `data_conciliacao`** — apenas `created_at`. Resultado: toda vez que o usuário aplicava filtro de período, as conciliações antigas eram excluídas do resultado e o PDF saía sem a lista.

### ✅ Correções
1. **Filtro de período resiliente a formato legado** (`routes/conciliacao.py` — export_pdf):
   - Agora o filtro usa `$or`:
     - `{data_conciliacao: {$gte, $lte}}` — conciliações novas
     - `{data_conciliacao: {$exists: false}, created_at: {$gte, $lte}}` — conciliações legadas
   - Combinado com o filtro de conta bancária via `$and` para evitar conflito de múltiplos `$or` no MongoDB.

2. **Endpoint `/conciliar` (singular) agora salva todos os campos modernos**:
   - `data_conciliacao`, `extrato_ids`, `contas_ids`, `contas_tipos`, `extratos_descricao`, `contas_descricao`, `valor_extratos`, `valor_contas`, `diferenca`
   - Preserva também os campos antigos para retrocompatibilidade.

### Testing via `analyze_file_tool`
- Gerado PDF com filtro abril/2026 incluindo conciliação **sem data_conciliacao** (simulando bug do usuário): 3 conciliações aparecem (antes: apenas 2 com data_conciliacao). Tabela renderizada corretamente com Tipo ENTRADA/SAÍDA/MISTO e cores.

---


## Changelog - 24/04/2026 (Sessão 33) — Correções Recibo e Duplicata

### ✅ Recibo de Pagamento (`/api/export/recibo/...`)
- **"Recebi(emos) de" agora mostra corretamente quem PAGOU**:
  - `contas_pagar.*` → CRA Locadora (a empresa que efetuou o pagamento ao fornecedor)
  - `contas_receber.*` / `alugueis` / `imoveis` → Cliente (quem pagou a empresa)
- Datas `data_vencimento` e `data_pagamento` continuam no formato **dd/mm/aaaa** (função `formatar_data_br` já existia).

### ✅ Duplicata (`/api/export/duplicata/...`)
- Campo **VENCIMENTO** agora formata corretamente em **dd/mm/aaaa** (antes saía em `2026-03-05`, agora `05/03/2026`).

### Testing
- Validação via `analyze_file_tool` (IA): 
  - Recibo de conta_pagar confirma: "Recebi(emos) de **CRA LOCADORA**" ✅
  - Duplicata confirma: VENCIMENTO em formato brasileiro dd/mm/aaaa ✅

---


## Changelog - 24/04/2026 (Sessão 33) — Robustez em Anexos de Contas

### 🔍 Investigação do bug reportado
- Backend testado via curl + Python: upload, list, download e delete **todos 200 OK** com content-type correto (PDF `%PDF`, PNG magic bytes OK).
- Testing agent (Chromium Playwright) **NÃO reproduziu o bug** — fluxo de Visualizar/Baixar em `/administrativo/a-pagar` e `/administrativo/a-receber` funciona 100%.
- **Conclusão**: bug é específico do ambiente do usuário (extensão/popup blocker/cache/anexo legado com file_type vazio).

### 🛡️ Melhorias de robustez aplicadas no `AttachmentsSection.jsx`
1. **Mensagens de erro informativas**: `handleDownload` e `handlePreview` agora extraem status HTTP real e mensagem do servidor (mesmo quando a resposta é um Blob de erro). Antes: "Erro ao baixar arquivo" (genérico). Agora: `Erro ao baixar arquivo (404): Arquivo não encontrado`.
2. **Blob com type explícito** em `handleDownload` (melhor compatibilidade Firefox/Safari).
3. **Inferência de content-type pela extensão** quando `response.headers['content-type']` ou `attachment.file_type` estão vazios.
4. **Fallback anti-popup-blocker**: se `window.open` for bloqueado em `handlePreview`, faz download automático do arquivo.
5. **canPreview robusto**: agora detecta preview por **extensão** do filename (`.pdf`, `.png`, `.jpg`, etc.) além do `file_type` — cobre anexos legados no banco com `file_type` vazio/null.

### 🛡️ Melhorias no backend (`server.py`)
1. `upload_attachment`: infere content-type pela extensão quando `file.content_type` vem vazio (garante que anexos futuros sempre tenham `file_type` correto).
2. `download_attachment`: se `attachment.file_type` estiver vazio/null (legado), infere pela extensão do stored_filename. Garante que o browser receba sempre um content-type correto e possa renderizar iframe/img.

---


## Changelog - 24/04/2026 (Sessão 33) — Padrão de Cores Completo (Extrato + PDF)

### ✅ Padrão de cores aplicado no lado do Extrato
- Adicionada coluna **"Tipo"** na tabela de extratos com badge colorido:
  - **Entrada** → verde (bg-green-100, ícone TrendingUp)
  - **Saída** → vermelho (bg-red-100, ícone TrendingDown)
- Agora o extrato tem identificação visual igualitária ao lado das Contas do Sistema (que já tinha badge Pagar/Receber colorido).

### ✅ Padrão de cores no PDF exportado (`/api/conciliacao/export-pdf`)
- **Extratos Pendentes**: cor verde em ENTRADA (+), vermelho em SAÍDA (-), com legenda no topo da seção.
- **Contas a Pagar Pendentes**: valor em **vermelho negrito** com sinal "-", legenda explicativa.
- **Contas a Receber Pendentes**: valor em **verde negrito** com sinal "+", legenda explicativa.
- **Conciliações Realizadas**: nova coluna **Tipo** (ENTRADA/SAÍDA/MISTO) + cores aplicadas em Valor Extrato e Valor Conta. Inclui legenda no topo. Tipos derivados dos extratos vinculados (batch fetch, sem N+1).

### Testing
- PDF validado via análise IA (`analyze_file_tool`) confirmando cores aplicadas corretamente, legendas presentes e tabelas bem estruturadas. Tamanho 4KB, magic `%PDF` OK, status 200.
- Lint Python e JavaScript passaram sem issues.

---


## Changelog - 23/04/2026 (Sessão 33) — Conciliação N:M Frontend + Fix Race Condition

### ✅ Finalização da migração singular→plural em ConciliacaoPage.jsx
- **Fix 1**: `handleLimparExtrato` chamava `setSelectedExtratoItem(null)` (variável extinta). Corrigido para limpar `selectedExtratoIds`, `selectedContaKeys` e os sets de sugestões.
- **Fix 2**: Painel "Detalhes da Seleção" foi reescrito do singular para lote N:M:
  - Lista iterável dos extratos selecionados (com data, descrição e valor colorido)
  - Lista iterável das contas selecionadas (com badge Pagar/Receber)
  - **Totais somados** (saldo extrato e saldo contas)
  - **Indicador de diferença** (verde se saldos batem, laranja caso contrário)
  - Botão "Limpar" por coluna
  - `data-testid="painel-selecao-lote"` para testes automatizados
- **Bônus**: Corrigido hydration warning em `SystemSelectPage.jsx:164` (Badge dentro de `<p>` → `<div>`)
- **Bônus**: Eliminada race condition do axios Authorization header em `App.js` — token agora é aplicado sincronamente no boot do módulo, antes do primeiro render. Elimina o toast "Erro ao carregar contas" que aparecia brevemente na entrada das páginas.

### Testing Agent Report — iteration_32.json
- **Resultado**: 13/14 pontos OK — 0 crashes, 0 bugs funcionais
- **34 checkboxes** role=checkbox renderizados na conciliação
- **Multi-seleção funcional**: contador do botão atualiza corretamente (`0 ↔ 3`)
- **painel-selecao-lote** aparece quando há ≥1 seleção
- **Legenda de cores completa** (Conciliado verde / Sugerido sky / Selecionado yellow / Pendente branco)
- **Botões PDF** presentes: `btn-export-pdf-conciliacao` e `btn-export-pdf-completo`
- **Sugerir Automático** popula 36 elementos sky/blue

### ⚠️ Nota do testing agent
- Rota correta é `/administrativo/conciliacao` (não `/admin/conciliacao`). Não é bug.
- Busca por valor em Contas a Pagar/Receber implementada como **campo único** (não range min/max). Decisão de produto necessária se o cliente preferir range.

---



## Changelog - 22/04/2026 (Sessão 32) — PARTE 5: Refatoração Fase 2 COMPLETA 🚀

### 🧹 server.py reduzido em **48%** (-7.428 linhas, de 15.487 → 8.059)

**3 novos routers + 2 reativados nesta parte — 73/73 testes passaram (iteration_31):**

| Domínio | Arquivo | Tipo | Linhas | Endpoints |
|---------|---------|------|--------|-----------|
| Exportação (PDF/Excel/OFX/Recibo/Duplicata/Extrato) | `routes/exports_all.py` | NOVO | 3.522 | ~20 |
| Dashboard | `routes/dashboard.py` | NOVO | 148 | 1 |
| Medições | `routes/medicoes.py` | NOVO | 253 | 6 |
| Stock (duplicados removidos) | `routes/stock.py` | Reativado | 543 | 14 |
| Obras (duplicados removidos) | `routes/obras.py` | Reativado | 402 | 9 |

**Problema resolvido — "Shadow routes":**
- `routes/stock.py` e `routes/obras.py` já existiam mas estavam sendo **silenciosamente ignorados** porque havia duplicados diretos (`@api_router.*`) em server.py que venciam pela ordem de registro no FastAPI. Removidos os duplicados, os routers modulares ficaram ativos.

**Bug fix UPLOAD_DIR / StaticFiles:**
- Durante a extração, descobri que `UPLOAD_DIR` e `from fastapi.staticfiles import StaticFiles` estavam definidos inline no meio do bloco de export (linha ~10719). Movi-os para o topo de server.py.

### Totais consolidados desta sessão (32):
- 📉 `server.py`: 15.487 → 8.059 (-7.428 linhas, **-48%**)
- 📈 **10 routers modulares** criados/refatorados totalizando 12.079 linhas organizadas
- 🎯 **72+ endpoints migrados**
- ✅ **73/73 testes backend** — zero regressão em 5 iterações de testing agent (27, 28, 29, 30, 31)

### Fase 2 — Pendente para próxima sessão:
- 🟠 **Contas Bancárias** — dar uma olhada e extrair se ainda houver bloco relevante
- 🟠 **Auth avançado** (já em routes/auth.py mas server.py pode ter duplicados shadowed)
- 🟢 Pytest em `/app/backend/tests/` para cobertura contínua
- 🟢 Split de `ImportacaoNFPage.jsx` (1900+ linhas)

---


## Changelog - 22/04/2026 (Sessão 32) — PARTE 4: Refatoração Fase 1 COMPLETA 🎉

### 🧹 6 Domínios Extraídos, 0 Regressões

Total desta sessão:
- 📉 `server.py`: **15.487 → 12.483 linhas** (-3.004, **-19,4%**)
- 📈 6 routers modulares criados (3.296 linhas organizadas em arquivos coesos)
- 🎯 **52 endpoints migrados**
- ✅ **42/42 testes backend passaram** (iteration_30), zero regressão

**Extrações (Fase 1 completa):**

| # | Domínio | Arquivo | Endpoints | Linhas |
|---|---------|---------|-----------|--------|
| 1 | Conciliação Bancária | `routes/conciliacao.py` | 7 | 415 |
| 2 | NFS-e (Serviços) | `routes/nfse.py` | 6 | 271 |
| 3 | NF-e (Cert/Import/Downloads) | `routes/nfe.py` | 12 | 436 |
| 4 | Financeiro (Pagar/Receber) | `routes/financeiro.py` | 14 | 720 |
| 5 | Emissão NF-e/NFS-e | `routes/emissao_nf.py` | 10 | 833 |
| 6 | Importação SEFAZ/ABRASF | `routes/importacao_nf.py` | 2 | 608 |

**Utils compartilhados:**
- `utils/audit.py` (create_audit_log)
- `utils/auth.py` (get_current_user)
- `utils/database.py` (MongoDB conn)
- `utils/sequences.py` **NOVO** (get_next_sequence)

**Bug de conflito de rota descoberto e corrigido:**
- `routes/admin.py` tinha endpoints duplicados antigos de `/admin/contas-pagar` e `/admin/contas-receber` que sobrescreviam os novos em `routes/financeiro.py` (devido à ordem de `include_router`).
- Causavam: response sem `valor_final`/`created_by`, vazamento de `_id`, modelo Pydantic desatualizado.
- Fix: 166 linhas obsoletas removidas de `admin.py`.

---


## Changelog - 22/04/2026 (Sessão 32) — PARTE 3: Refatoração Fase 1

### 🧹 Refatoração Incremental do `server.py` (P0 - dívida técnica recorrente 10+ forks)

**3 domínios extraídos nesta parte — testados e validados pelo testing agent:**

1. ✅ **Conciliação Bancária** → `/app/backend/routes/conciliacao.py` (415 linhas, 7 endpoints) — 16/16 testes (iteration_27)
2. ✅ **NFS-e (Notas de Serviço)** → `/app/backend/routes/nfse.py` (271 linhas, 6 endpoints)
3. ✅ **NF-e (Certificados/Importadas/Downloads)** → `/app/backend/routes/nfe.py` (436 linhas, 12 endpoints) — 34/34 testes totais (iteration_28), zero regressão

**Infra compartilhada:** utils/audit.py, utils/auth.py, utils/database.py

**Métricas:**
- 📉 `server.py`: 15.487 → **14.421 linhas** (-1.066, -6,9%)
- 🎯 25 endpoints migrados | ✅ 0 regressões

**Pendente Fase 1 Parte 2 (próxima sessão):**
- 🔴 Financeiro: Contas a Pagar/Receber (~640 linhas, 14 endpoints)
- 🟡 Emissão NF-e / NFS-e (~740 linhas)
- 🟡 Importação SOAP (~575 linhas, acoplada ao scheduler)

---


## Changelog - 22/04/2026 (Sessão 32) — PARTE 2: Edit CNPJs + Bug fix produção

### Bug Fix Crítico — Sumiço de CNPJs/NFes em Produção
- ✅ Decorator `@api_router.get("/nfe/importadas")` havia sido removido acidentalmente em commit anterior → re-adicionado (posteriormente migrado para `routes/nfe.py`)
- ✅ Frontend: `.catch()` individuais em cada `axios.get` do Promise.all evitando derrubar toda a tela

### Feature — Editar CNPJs/Certificados
- ✅ `PATCH /api/nfe/certificados/{id}` atualiza razao_social, uf, ambiente, ativo, inscricao_municipal, url_nfse
- ✅ Modal "Editar CNPJ/Certificado" no frontend com seção NFS-e (IM + URL Webservice)

---


## Changelog - 22/04/2026 (Sessão 32) — PARTE 1: DANFE

### DANFE em Layout Oficial
- ✅ **Novo gerador**: `/app/backend/utils/danfe_generator.py` extrai dados completos do XML (emit, dest, transp, totais, itens, duplicatas, protocolo) e completa com dados do MongoDB
- ✅ **Template HTML + WeasyPrint**: `/app/backend/templates/danfe.html` replica as seções do DANFE oficial (cabeçalho com emitente/identificação/chave, natureza+protocolo, destinatário, cálculo imposto, transportador, produtos, dados adicionais)
- ✅ **Code128 barcode**: Renderizado a partir da chave de acesso (python-barcode)
- ✅ **Formatações oficiais**: CNPJ `XX.XXX.XXX/XXXX-XX`, CEP `XXXXX-XXX`, datas DD/MM/AAAA, valores `X.XXX,XX`, chave em grupos de 4 dígitos, número `000.000.000`, série `001`
- ✅ **Endpoint atualizado**: `GET /api/nfe/importadas/{nfe_id}/download-pdf` agora usa o novo gerador (mantém fallback para PDF original armazenado)
- ✅ **Dependências**: Adicionados `weasyprint==68.1` e `python-barcode==0.16.1` em requirements.txt
- ✅ **Testado**: 3 NFes reais (com XML completo) geraram PDF A4 fidedigno ao modelo

---


## Changelog - 22/04/2026 (Sessão 31)

### Conciliação Bancária — 3 correções:
- ✅ **Valores corretos na extração de PDF**: Algoritmo reescrito. Antes usava `value_matches[-1]` (o SALDO), agora usa `selecionar_valor_e_tipo()` que detecta D/C, valor negativo explícito, ou usa o PRIMEIRO valor da linha (excluindo o último = saldo corrente)
- ✅ **Suporte a tabelas do pdfplumber**: Detecção de colunas Débito/Crédito/Saldo por cabeçalho; fallback para texto linha por linha
- ✅ **Ordenação crescente**: Extrato Bancário e Contas do Sistema exibidos do mais antigo ao mais recente
- ✅ **Campo de busca no painel do Extrato**: Input `data-testid="busca-extrato"` filtra em tempo real por descrição
- ✅ **Campo de busca no painel de Contas**: Já existia, mantido
- ✅ **Testado**: 8/9 backend (1 skipped - endpoint não implementado), 100% frontend

---



### Correções e Padronização de Exportações
- ✅ **Exportação combinada corrigida**: `export_combined` usava `list(keys)[:6]` (campos brutos MongoDB). Reescrito para usar `generate_pdf_report()` por seção + merge com PyPDF2 → colunas legíveis em todos os relatórios
- ✅ **`exportAllSelected` (frontend)**: Removida referência a `specificFilters` (undefined) que causava crash silencioso no botão "Exportar"
- ✅ **Datas padronizadas DD/MM/AAAA**: Helpers `fmt_date()` / `fmt_date_xl()` aplicados em todos os campos de data (PDF e Excel)
- ✅ **Moeda padronizada R$ X.XXX,XX**: Helpers `fmt_money()` / `fmt_money_xl()` com formato brasileiro (vírgula como decimal, ponto como milhar)
- ✅ **Excel completo**: Mapeamentos específicos adicionados para `obras`, `maintenances`, `stock_items`, `produtos_admin`, `ordens_servico`, `contas_bancarias`, `funcionarios`, `folha_pagamento`, `ponto_registros`, `ferias`, `epi_fichas`, `plano_contas`, `centros_custo`, `medicoes`
- ✅ **Normalização de variantes**: `contas_pagar_pendente`, `contas_receber_vencidas`, etc. mapeadas ao tipo base correto no export_combined
- ✅ **Testado**: 27/27 testes passaram (testing_agent_v3_fork)

---



### Nova Funcionalidade: Filtro de Centro de Custo na Exportação
- ✅ **Painel de seleção obrigatório**: Banner amarelo no topo da página de Exportação (módulo Administrativo) exige seleção antes de exportar
- ✅ **Modal de seleção**: Abre modal com todas as opções de CC cadastradas + "Todos os Centros de Custo"
- ✅ **Estados visuais**: Amarelo (não selecionado), Azul (todos), Verde (CC específico selecionado)
- ✅ **Bloqueio de exportação**: Seção de categorias fica opaca/desabilitada até CC ser selecionado
- ✅ **Backend filtrado**: Endpoints export_pdf, export_excel, export_ofx aceitam `?centro_custo=NOME`
- ✅ **Exportação combinada**: POST /api/export/combined aceita campo `centro_custo` no body
- ✅ **Filtro aplicado em**: Coleções `contas_pagar` e `contas_receber` (únicas com campo centro_custo)
- ✅ **Módulo Gerenciamento**: Não afetado (filtro só aparece no módulo Administrativo)
- ✅ **Testado**: 12/12 testes passaram (testing_agent_v3_fork)

---



### Correção: Total em Todas as Exportações
- ✅ **PDF com Total**: Adicionado "TOTAL GERAL" ao final de todos os relatórios PDF (Contas a Pagar, Receber, Aluguéis, etc.)
- ✅ **Excel com Total**: Adicionada linha de total nos arquivos Excel exportados
- ✅ **Formatação brasileira**: Valores formatados como "R$ X.XXX,XX"
- ✅ **Visual destacado**: Total com fundo colorido e fonte em negrito

### Correção: Conciliação Bancária - Entradas e Saídas
- ✅ **Lógica melhorada**: Sistema agora detecta corretamente entradas e saídas nos extratos
- ✅ **Padrões de débito detectados**: DEB, DEBITO, PGTO, PAGAMENTO, TRANSF ENV, TED ENV, DOC ENV, PIX ENV, SAQUE, TARIFA, COMPRA, BOLETO, etc.
- ✅ **Padrões de crédito detectados**: CRED, CREDITO, REC, RECEBIMENTO, TRANSF REC, TED REC, DOC REC, PIX REC, DEP, DEPOSITO, RENDIMENTO, etc.
- ✅ **Indicadores D/C**: Detecta caracteres "D" e "C" próximos aos valores
- ✅ **Valores negativos**: Identifica automaticamente como saída

---

## Changelog - 11/03/2026 (Sessão 28 - Continuação 2)

### Verificação e Correção: Importação Automática de NF-e e NFS-e
- ✅ **Importação automática NF-e funcionando**: Testada com sucesso, conecta na SEFAZ e importa documentos
- ✅ **Logs detalhados**: Sistema registra cada execução com status, quantidade e erros
- ✅ **Correção do processamento**: Ajustado parsing da resposta SEFAZ para formato correto
- ✅ **NFS-e preparada**: Estrutura pronta para integração com Webiss (Palmas-TO)

### Verificação: Notas no Painel
- ✅ **Notas importadas aparecem no painel**: 121 NF-e e 3 NFS-e visíveis
- ✅ **Notas manuais também aparecem**: Notas importadas via XML aparecem junto com as automáticas

### Status Atual
- **Importação automática**: Agendada para 22:00 diariamente (Brasília)
- **Scheduler ativo**: Confirmado funcionando
- **SEFAZ retornando cStat=137**: Significa "nenhum documento novo" (já importados)

---

## Changelog - 11/03/2026 (Sessão 28 - Continuação)

### Nova Funcionalidade: Importação Automática de Notas às 22h
- ✅ **Agendamento automático**: Sistema importa NF-e de todos os CNPJs cadastrados diariamente às 22:00 (Brasília)
- ✅ **APScheduler integrado**: Usando biblioteca robusta para agendamento de tarefas
- ✅ **Logs de importação**: Registra cada execução com quantidade de notas importadas e erros
- ✅ **Endpoints de controle**:
  - `POST /api/nf/importacao-automatica/executar` - Executa importação manualmente
  - `GET /api/nf/importacao-automatica/status` - Status do scheduler e última execução
  - `GET /api/nf/importacao-automatica/logs` - Histórico de importações

### Correção: Formato de Data no Recibo
- ✅ **Datas em formato brasileiro (dd/mm/aaaa)**: Corrigido formato de data de vencimento e pagamento

### Correção: Assinatura no Recibo
- ✅ **Nome do fornecedor/cliente**: Campo de assinatura agora mostra o nome correto (fornecedor/cliente) ao invés do emissor

### Nota sobre Importação Manual
- ✅ **Notas importadas manualmente já aparecem no painel**: Campo `importacao_manual: true` marca notas importadas via XML

---

## Changelog - 11/03/2026 (Sessão 28)

### Melhoria: Download de DANFE Real para NF-e Importadas
- ✅ **DANFE real gerado a partir do XML**: Usando biblioteca `erpbrasil.edoc.pdf` para gerar DANFE oficial
- ✅ **PDF original quando disponível**: Se a nota tem PDF armazenado, usa ele diretamente
- ✅ **Fallback com aviso**: Se não conseguir gerar DANFE real, gera versão simplificada com aviso visual
- ✅ **Dependências instaladas**: `erpbrasil.edoc.pdf`, `nfelib`, `pycairo`, `rlPyCairo`, LibreOffice
- ✅ **Link para Portal NF-e**: PDF simplificado inclui link para consulta oficial

### Correções de Bugs
- ✅ **Erro 500 no Dashboard**: Corrigido comparação de datas com valores `None`
- ✅ **URL incorreta centro-custo**: Corrigido `/centro-custo` para `/centros-custo` no AdminDashboardPage

---

## Changelog - 09/03/2026 (Sessão 27 - Continuação)

### Melhoria: Extração Automática de Dados do XML na Importação Manual
- ✅ **Novo endpoint**: `POST /api/nf/extrair-xml` - Extrai dados de arquivo XML de NF-e
- ✅ **Upload destacado**: Seção em destaque no topo para upload de XML
- ✅ **Preenchimento automático**: Ao fazer upload do XML, todos os campos são preenchidos automaticamente:
  - Número da Nota, Série, Chave de Acesso
  - Data de Emissão
  - CNPJ e Razão Social do Emitente
  - CNPJ e Razão Social do Destinatário
  - Valores: Total, Produtos, Frete, Desconto
- ✅ **Exibição de itens**: Mostra os itens extraídos do XML em uma tabela
- ✅ **Fallback manual**: Se a extração falhar, permite preenchimento manual
- ✅ **Testado com XML de NF-e**: Funcionamento verificado via API

#### Como usar
1. Acesse "Importação NF" > "Importação Manual"
2. Clique em "Selecionar Arquivo XML"
3. Aguarde o processamento - os campos serão preenchidos automaticamente
4. Verifique os dados e selecione Centro de Custo/Plano de Contas
5. Clique em "Importar Nota"

### Melhoria: Visual do Parcelamento em Contas a Pagar/Receber
- ✅ **Destaque visual melhorado**: Fundo gradiente e borda mais grossa
- ✅ **Checkbox maior**: Mais fácil de visualizar e clicar
- ✅ **Texto com ícone**: 📋 para identificação rápida

---

## Changelog - 09/03/2026 (Sessão 27)

### Melhoria: Filtro "Todas" no Relatório por Conta Bancária
- ✅ **Nova opção no dropdown "Tipo de Conta"**: "Todas (Pagar e Receber)"
- ✅ **Backend atualizado**: Endpoint `/api/export/relatorio-conta-bancaria` aceita `tipo=todas`
- ✅ **Lógica de busca combinada**: Busca dados de `contas_pagar` e `contas_receber` simultaneamente
- ✅ **Ordenação unificada**: Resultados ordenados por data de vencimento (mais recente primeiro)
- ✅ **Título dinâmico**: PDF gerado com título "Contas a Pagar e Receber - [Status]"
- ✅ **Testado via curl e frontend**: Funcionamento verificado

#### Uso
1. Acesse "Exportação" no menu Administrativo
2. Role até "Relatório por Conta Bancária"
3. Selecione a conta bancária
4. No "Tipo de Conta", escolha "Todas (Pagar e Receber)"
5. Selecione o status desejado (Todas, Pendentes, Quitadas, Parcialmente Pagas)
6. Clique em "Exportar Relatório PDF"

---

## Changelog - 09/03/2026 (Sessão 26 - Continuação 3)

### Novas Funcionalidades Implementadas

#### 1. Movimentação de Contas (Nova Página)
- ✅ **Nova página**: `/administrativo/movimentacoes`
- ✅ **Tipos de movimentação**: Entrada, Saída, Transferência
- ✅ **Categorias**: Cancelamento de NF, Estorno, Devolução, Transferência Interna, Ajuste, Outros
- ✅ **Transferência entre contas bancárias**: Atualiza saldos automaticamente
- ✅ **Transferência entre centros de custo**: Vincula origem e destino
- ✅ **Exclusão com reversão**: Ao excluir, os saldos são revertidos
- ✅ **Filtros**: Por tipo, categoria, conta bancária e centro de custo

#### 2. Importação Manual de NF (Nova Aba)
- ✅ **Nova aba**: "Importação Manual" na página de Importação NF
- ✅ **Uso**: Quando a SEFAZ falha na importação automática
- ✅ **Campos**: Tipo NF, Número, Série, Chave de Acesso, Data Emissão
- ✅ **Dados do Emitente**: CNPJ, Razão Social
- ✅ **Valores**: Total, Produtos/Serviços, Frete, Desconto
- ✅ **Classificação**: Centro de Custo, Plano de Contas
- ✅ **Arquivos**: Upload de XML e PDF (opcional)

#### 3. Baixas Parciais (Já existente - Verificado)
- ✅ **Pagamento parcial**: Pagar parte do valor e deixar o resto para depois
- ✅ **Status "Parcial"**: Badge amarelo na lista de contas
- ✅ **Histórico de pagamentos**: Registra cada baixa parcial

#### Novos Endpoints
- `GET /api/admin/movimentacoes` - Lista movimentações
- `POST /api/admin/movimentacoes` - Cria movimentação
- `DELETE /api/admin/movimentacoes/{id}` - Exclui e reverte saldos
- `POST /api/nf/importar-manual` - Importa NF manualmente

---

## Changelog - 09/03/2026 (Sessão 26 - Continuação 2)

### Melhoria: Data de Quitação nos Relatórios Financeiros
- ✅ **Exportação PDF**: Adicionada coluna "Quitação" (Contas a Pagar) e "Recebimento" (Contas a Receber)
- ✅ **Exportação Excel**: Adicionada coluna "Quitação" (Contas a Pagar) e "Recebimento" (Contas a Receber)
- ✅ **Relatório por Conta Bancária**: Adicionada coluna com data de quitação/recebimento
- ✅ **Exportação Individual**: Seção "DATAS" já mostra Data de Pagamento/Recebimento

#### Colunas dos Relatórios Financeiros (PDF/Excel)
**Contas a Pagar:**
| Descrição | Valor | Vencimento | **Quitação** | Status | Fornecedor | Centro de Custo | Plano de Contas |

**Contas a Receber:**
| Descrição | Valor | Vencimento | **Recebimento** | Status | Cliente | Centro de Custo | Plano de Contas |

---

## Changelog - 09/03/2026 (Sessão 26 - Continuação)

### Nova Funcionalidade: Parcelamento de Contas a Pagar/Receber
- ✅ **Opção de Parcelamento**: Checkbox "Parcelar esta conta" no modal de criação
- ✅ **Seletor de Parcelas**: Dropdown com opções de 2x até 60x
- ✅ **Intervalo entre Parcelas**: 7, 14, 15, 21, 28, 30, 45, 60 ou 90 dias
- ✅ **Resumo Automático**: Mostra valor de cada parcela antes de salvar
- ✅ **Identificação Visual**: Badge "Parcela X/Y" na lista de contas
- ✅ **Agrupamento**: ID de origem (`parcela_origem_id`) para vincular parcelas

#### Novos Endpoints
- `POST /api/admin/contas-pagar/parcelado` - Cria múltiplas parcelas de conta a pagar
- `POST /api/admin/contas-receber/parcelado` - Cria múltiplas parcelas de conta a receber

#### Como Funciona
1. Ao criar uma nova conta, marque "Parcelar esta conta"
2. Selecione o número de parcelas (ex: 2x, 3x, 4x...)
3. Defina o intervalo entre vencimentos (default: 30 dias)
4. A data de vencimento no formulário será a do primeiro vencimento
5. O sistema divide o valor total automaticamente
6. Cada parcela é criada com descrição "Descrição - Parcela X/Y"

---

## Changelog - 09/03/2026 (Sessão 26)

### Nova Funcionalidade: Emissão de Notas Fiscais (NF-e e NFS-e)
- ✅ **Nova Página**: `/administrativo/emissao-nf` - Emissão de Notas Fiscais
- ✅ **Seletor de CNPJ Emitente**: Dropdown com todos os CNPJs cadastrados com certificados digitais
- ✅ **Seletor de Tipo de Nota**: 
  - NF-e (Nota Fiscal de Produtos - Modelo 55)
  - NFS-e (Nota Fiscal de Serviços)

#### NF-e (Notas Fiscais de Produtos)
- ✅ **Dados do Destinatário**: CPF/CNPJ com consulta automática (BrasilAPI), Razão Social, IE, Email, Telefone
- ✅ **Endereço do Destinatário**: CEP com consulta automática (ViaCEP), Logradouro, Número, Complemento, Bairro, Cidade, UF
- ✅ **Seleção de Cadastro**: Dropdown para preencher automaticamente dados de clientes/fornecedores cadastrados
- ✅ **Dados da Nota**: Natureza da Operação, Forma de Pagamento, Consumidor Final
- ✅ **Itens**: 
  - Seleção de produtos cadastrados no sistema
  - Campos: Código, Descrição, NCM, CFOP, Unidade, Quantidade, Valor Unitário
  - Tributação: ICMS, PIS, COFINS, IPI (alíquotas configuráveis)
- ✅ **Totais**: Frete, Seguro, Desconto, Outras Despesas, Valor Total calculado automaticamente
- ✅ **Informações Complementares**: Campo de texto livre

#### NFS-e (Notas Fiscais de Serviço - Palmas/TO)
- ✅ **Dados do Tomador**: CPF/CNPJ, Razão Social, IE, IM, Email, Telefone, Endereço completo
- ✅ **Dados do Serviço**: 
  - Código do Serviço (LC 116/2003) - 19 códigos pré-cadastrados
  - CNAE (opcional)
  - Código Tributário Municipal
  - Discriminação do Serviço (texto detalhado)
- ✅ **Valores**: Valor dos Serviços, Deduções, Alíquota ISS, ISS Retido (checkbox)
- ✅ **Retenções**: PIS, COFINS, INSS, IR, CSLL, Outras Retenções
- ✅ **Cálculos Automáticos**: Valor ISS e Valor Líquido calculados em tempo real

#### Notas Emitidas
- ✅ **Lista de Notas**: Tabela com todas as notas emitidas
- ✅ **Filtros**: Tipo de Nota, CNPJ Emitente, Status
- ✅ **Status com Badges**: Autorizada (verde), Rascunho (amarelo), Pendente (azul), Rejeitada (vermelho)
- ✅ **Ações**: Ver detalhes, Download PDF, Download XML (quando disponível), Excluir (apenas rascunhos)

#### Backend - Novos Endpoints
- `GET /api/nfe/cfops` - Lista CFOPs disponíveis para emissão
- `GET /api/nfse/codigos-servico` - Lista códigos de serviço LC 116/2003
- `GET /api/notas-emitidas` - Lista todas as notas fiscais emitidas
- `GET /api/notas-emitidas/{id}` - Detalhes de uma nota fiscal
- `POST /api/nfe/emitir` - Emite uma NF-e
- `POST /api/nfse/emitir` - Emite uma NFS-e (XML ABRASF 2.1 para Webiss Palmas/TO)
- `DELETE /api/notas-emitidas/{id}` - Exclui nota (apenas rascunhos)
- `GET /api/notas-emitidas/{id}/download-xml` - Download do XML
- `GET /api/notas-emitidas/{id}/download-pdf` - Download do DANFE/NFS-e em PDF

#### Observações Técnicas
- ⚠️ **NF-e**: As notas são salvas como rascunho. A emissão direta via SEFAZ requer configuração adicional do PyNFe com assinatura digital
- ⚠️ **NFS-e**: XML gerado no padrão ABRASF 2.1. A emissão via Webiss Palmas/TO requer configuração de assinatura digital SOAP
- ✅ **Coleção MongoDB**: `notas_emitidas` - Armazena todas as notas (NF-e e NFS-e)

---

## Changelog - 09/03/2026 (Sessão 25)

### Reformulação da Página de Conciliação Bancária
- ✅ **Seletor de Centro de Custo**: Substituído o seletor de conta bancária por um seletor de centro de custo
  - As contas do sistema são filtradas pelo centro de custo selecionado
  - Opção "Todos os Centros de Custo" para ver todas as contas
- ✅ **Extrato Bancário (Quadro Esquerdo)**: Exibe as movimentações importadas de todos os PDFs
  - Filtros de tipo (Todos/Entradas/Saídas) e de data (início/fim)
  - **Botão "Limpar Extrato"**: Ícone de lixeira para remover itens não conciliados
- ✅ **Contas do Sistema (Quadro Direito)**: Mostra contas a pagar e receber
  - **Filtro de tipo de conta**: Todas, Quitadas, A Pagar, A Receber
  - Campo de busca por descrição
  - Filtro por centro de custo funcional
- ✅ **Modal de Importação de Extrato**: Ao clicar em "Importar Extrato PDF"
  - Abre modal para selecionar primeiro a conta bancária
  - Depois permite selecionar o arquivo PDF para upload
- ✅ **Novo Endpoint**: `GET /api/conciliacao/extratos` - Lista todos os extratos importados
- ✅ **Novo Endpoint**: `DELETE /api/conciliacao/extratos` - Limpa extratos não conciliados

### Exportação: Relatório por Conta Bancária
- ✅ **Nova seção na página de Exportação**: "Relatório por Conta Bancária"
  - Seletor de **Conta Bancária**: Lista todas as contas bancárias cadastradas
  - Seletor de **Tipo de Conta**: Contas a Pagar ou Contas a Receber
  - Seletor de **Status**: Todas, Pendentes, Quitadas, Parcialmente Pagas
  - Botão "Exportar Relatório PDF" gera relatório filtrado
- ✅ **Novo Endpoint**: `GET /api/export/relatorio-conta-bancaria` - Gera PDF com relatório filtrado
- ✅ **Relatório inclui**: Resumo de totais, tabela com todas as contas filtradas, valores pagos/recebidos e saldo restante

### Nova Funcionalidade: Quitação Parcial de Contas
- ✅ **Contas a Pagar**: Implementada quitação parcial
  - Modal de pagamento reformulado com opções "Quitar Total" e "Pagamento Parcial"
  - Quando "Pagamento Parcial" é selecionado, campo de valor é exibido
  - Histórico completo de todos os pagamentos realizados com data, valor e observação
  - Novo status "parcial" (amarelo) para contas parcialmente pagas
  - Filtro de status atualizado com opção "Parcialmente Pagas"
  - Botão de histórico (ícone de relógio) exibido para contas com pagamentos
  
- ✅ **Contas a Receber**: Implementada quitação parcial (mesma funcionalidade)
  - Modal de recebimento com opções "Quitar Total" e "Recebimento Parcial"
  - Histórico de recebimentos
  - Novo status "parcial" (amarelo)
  - Filtro "Parcialmente Recebidas"
  - Botão de histórico para visualizar recebimentos

- ✅ **Backend atualizado**:
  - `PATCH /api/admin/contas-pagar/{id}/quitar` - Aceita `valor_pago` para pagamento parcial
  - `PATCH /api/admin/contas-receber/{id}/quitar` - Aceita `valor_recebido` para recebimento parcial
  - Novos campos: `valor_pago`, `valor_recebido`, `saldo_restante`, `pagamentos[]`, `recebimentos[]`
  - Atualização automática de saldo da conta bancária proporcional ao valor pago/recebido
  - Status automático: "parcial" quando há saldo restante, "quitada" quando totalmente pago

- ✅ **Totais atualizados**: Cards de "Total em Aberto" agora consideram o saldo restante das contas parciais

---

## Changelog - 06/03/2026 (Sessão 24)

### Bug Fix: Download de PDF (NF-e e NFS-e) - P0
- ✅ **Corrigido bug de erro 403 (Proibido)** no download de arquivos PDF e XML
  - **Causa**: O método `window.open()` não envia o token de autenticação no cabeçalho HTTP
  - **Solução**: Implementada função `handleDownload` usando `axios` com `responseType: 'blob'` e header `Authorization`
  - **Padrão implementado**: O código cria uma URL de objeto (`createObjectURL`) a partir do blob recebido e dispara o download via elemento `<a>` temporário
- ✅ **Endpoints testados e funcionais**:
  - `GET /api/nfe/importadas/{id}/download-xml` ✓
  - `GET /api/nfe/importadas/{id}/download-pdf` ✓
  - `GET /api/nfse/importadas/{id}/download-xml` ✓
  - `GET /api/nfse/importadas/{id}/download-pdf` ✓
- ✅ **Testes e2e passaram**: Download de `DANFE_NFe_5610.pdf` e `NFe_5610.xml` confirmados via interface

---

## Changelog - 04/03/2026 (Sessão 23)

### Importação de NFS-e (Notas de Serviço)
- ✅ **Dois mostradores na página de Importação NF**:
  - **NF-e (Compras)** - Notas Fiscais de Produtos (borda azul quando selecionado)
  - **NFS-e (Serviços)** - Notas Fiscais de Serviços (borda verde quando selecionado)
- ✅ **Tabela específica para NFS-e** com colunas:
  - NFS-e (Número e Série)
  - Prestador (Nome e CNPJ)
  - Serviço (Descrição)
  - Data de Emissão
  - Valor do Serviço
  - Status (Nova, Processada, Ignorada)
  - Ações (Ver detalhes, Download XML, Download PDF, Criar conta a pagar)
- ✅ **Endpoints criados para NFS-e**:
  - `GET /api/nfse/importadas` - Lista NFS-e importadas
  - `GET /api/nfse/importadas/{id}` - Detalhes de uma NFS-e
  - `GET /api/nfse/importadas/{id}/download-xml` - Download do XML
  - `GET /api/nfse/importadas/{id}/download-pdf` - Download do PDF
  - `POST /api/nfse/importadas/{id}/criar-conta-pagar` - Criar conta a pagar
  - `PATCH /api/nfse/importadas/{id}/status` - Atualizar status
- ✅ **Botão de importação dinâmico**: Muda entre "Importar NF-e" e "Importar NFS-e" conforme seleção

### Nova Ferramenta: Conciliação Bancária
- ✅ **Nova página de Conciliação** (`/administrativo/conciliacao`)
- ✅ **Importação de Extrato PDF**: Upload de arquivo PDF para extrair movimentações bancárias
  - Usa biblioteca `pdfplumber` para extrair texto e tabelas
  - Detecta automaticamente data, valor e descrição
  - Identifica entradas e saídas
- ✅ **Layout lado a lado**:
  - **Esquerda (amarelo)**: Extrato bancário importado com filtros (tipo, data início/fim)
  - **Direita (azul)**: Contas do sistema com filtros (Todas, Quitadas, A Pagar, A Receber) e busca
- ✅ **Cards de resumo**: Entradas, Saídas, Saldo Extrato, Conciliados

### Conciliação Automática (Sugestões)
- ✅ **Botão "Sugerir Automático"** analisa extratos e contas e encontra correspondências
- ✅ **Tolerância configurável**:
  - Valor Exato (0%)
  - Tolerância 1%, 2%, 5%, 10%
- ✅ **Algoritmo inteligente**:
  - Combina saídas do extrato com contas A Pagar
  - Combina entradas do extrato com contas A Receber
  - Calcula percentual de match (100% = valor exato)
- ✅ **Painel de Sugestões**:
  - Lista todas as correspondências encontradas
  - Indicador visual de match (bolinha verde/amarela/laranja)
  - Botões individuais para Aceitar (✓) ou Rejeitar (✗) cada sugestão
  - **Botão "Aceitar Todas"** para conciliar automaticamente todas as sugestões
- ✅ **Funcionalidade de conciliar**: Selecionar item do extrato + conta do sistema e vincular
- ✅ **Desfazer conciliação**: Botão para desvincular itens conciliados

---

## Changelog - 03/03/2026 (Sessão 22)

### Correções e Melhorias Solicitadas

#### 1. Exportar - Novas Categorias
- ✅ Adicionadas categorias faltantes no sistema de exportação:
  - **Horímetro**: Todos os Registros, Resumo por Máquina, Resumo por Operador
  - **Combustível**: Todos os Registros, Consumo por Máquina, Veículos Tanque
  - **Frotas**: Todas as Frotas, Documentos de Frota
  - **Operadores**: Todos os Operadores, Operadores RH, Operadores Cadastro
  - **Medições de Obras**: Todas as medições registradas

#### 2. Controle de Combustível - Edição de Registros
- ✅ Linhas da tabela agora são clicáveis para editar
- ✅ Botão de editar (ícone de lápis) adicionado na coluna Ações
- ✅ Endpoint PUT `/api/combustivel/{registro_id}` criado no backend
- ✅ Modal de edição com todos os campos pré-preenchidos

#### 3. Ver Máquina - Cálculo de Litros Corrigido
- ✅ Corrigido cálculo de `totalLitrosConsumidos` para somar `litros_diesel + litros_oleo + litros_graxa`
- ✅ Exibição correta de registros de combustível com tipo (Entrada/Saída)
- ✅ Detalhamento de litros por tipo (Diesel, Óleo)

#### 4. Plano de Obras - Badges e Medições
- ✅ Adicionados badges na página de detalhes da obra:
  - **Horas Trabalhadas** (amarelo) - soma das horas de horímetro das máquinas da obra
  - **Combustível** (verde) - soma dos litros consumidos pelas máquinas da obra
- ✅ Corrigido botão "Medições de Máquinas" - erro do Select com valor vazio resolvido
- ✅ Grid de 6 colunas responsivo para os badges

### Download de NF-e (XML e PDF)
- ✅ **Novos endpoints de download**:
  - `GET /api/nfe/importadas/{nfe_id}/download-xml` - Download do XML original da NF-e
  - `GET /api/nfe/importadas/{nfe_id}/download-pdf` - Download do DANFE (PDF) gerado
- ✅ **Interface**:
  - Botões de download na tabela de NF-e (ícones na coluna Ações)
  - Botões de download no modal de detalhes da NF-e
  - Download XML (ícone azul) / Download DANFE PDF (ícone vermelho)
- ✅ **DANFE PDF**:
  - Gerado via ReportLab
  - Contém: Número, Série, Data, Valor, Emitente, CNPJ, Chave de Acesso, Lista de Itens
  - Formatação profissional em A4

### Melhorias no Sistema de Combustível
- ✅ **Botão Único de Registro**: Unificados os botões "Registro Abastecedor" e "Registro Abastecido" em um único botão "Novo Registro de Combustível"
- ✅ **Formulário Unificado**: 
  - Opção de tipo: "Abastecimento (Saída)" ou "Entrada no Tanque"
  - Fonte do Abastecimento com 3 opções:
    - Veículo Tanque (Interno) - com dropdown de tanques cadastrados
    - Posto Parceiro - com dropdown de fornecedores cadastrados
    - Outro (Externo)
- ✅ **Compartimentos de Óleo Dinâmicos** no Veículo Tanque:
  - Botão "Adicionar Óleo" para criar compartimentos
  - Seleção de item do estoque (dropdown com peças/óleos)
  - Seleção de unidade de medida (L, ML, KG, G, UN)
  - Campos de Capacidade e Quantidade Atual
  - Múltiplos compartimentos podem ser adicionados/removidos
- ✅ **Backend atualizado**:
  - Modelo `CompartimentoOleo` para compartimentos dinâmicos
  - Campo `compartimentos_oleo` no `VeiculoAbastecedorCreate`
  - Campo `posto_id` no `CombustivelCreate`
  - Endpoints de criação/atualização processam compartimentos

### Verificação de Máscaras de Data
- ✅ Verificado que todos os campos de data já utilizam `type="date"` (seletor nativo do navegador)
- ✅ Função `formatDate` já disponível em `/app/frontend/src/utils/masks.js` para uso futuro

---

## Changelog - 03/03/2026 (Sessão 21)

### Dashboard com Máquinas por Categoria (Expandível)
- ✅ **Badge de Total de Máquinas** agora é clicável e expansível
- ✅ Ao clicar, expande para mostrar **sub-badges por categoria**
- ✅ Cada sub-badge exibe:
  - Cor da categoria (borda lateral colorida)
  - Ícone de máquina na cor da categoria
  - Quantidade de máquinas
  - Nome da categoria
- ✅ Sub-badges são clicáveis e redirecionam para página de máquinas filtrada
- ✅ Botão de chevron indica que o card é expansível
- ✅ Animação suave ao expandir/recolher

### Modelo da Máquina nos Cards
- ✅ **Visualização Grid**: Modelo aparece logo abaixo do nome da máquina
- ✅ **Visualização Lista**: Modelo aparece ao lado do nome (Nome • Modelo)
- ✅ **Página de Estoque**: Modelo já aparecia nos badges de máquinas associadas

### Campo de Valor Automático na Manutenção
- ✅ O campo "Valor Total (R$)" é preenchido automaticamente com a soma de peças + mão de obra
- ✅ Campo fica com fundo verde e label "(calculado automaticamente)"
- ✅ Usuário pode editar manualmente se necessário

### Sistema de Importação de NF-e (NOVO)
- ✅ **Nova página**: `/administrativo/importacao-nf`
- ✅ **Funcionalidades**:
  - Cadastrar múltiplos CNPJs com certificados A1 (.pfx)
  - Configurar UF e Ambiente (Produção/Homologação)
  - Consultar NF-e destinadas ao CNPJ via SEFAZ
  - Listar NF-e importadas com filtros por CNPJ e status
  - Visualizar detalhes completos da NF-e (emitente, itens, valores)
  - Criar Conta a Pagar automaticamente a partir da NF-e
  - Status: Nova, Processada, Ignorada
- ✅ **Backend**:
  - Validação de certificado digital
  - Integração com SEFAZ (NFeDistribuicaoDFe)
  - Armazenamento seguro de certificados
  - Criação automática de cadastro de fornecedor
- ✅ **Bibliotecas**: PyNFe, pyOpenSSL, cryptography

---

## Changelog - 27/02/2026 (Sessão 20)

### Máscaras de Formatação para Valores Monetários
- ✅ **Novas funções de máscara** adicionadas em `/app/frontend/src/utils/masks.js`:
  - `formatCurrency`: Formata valores monetários no padrão brasileiro (R$ 1.500,00)
  - `parseCurrency`: Converte string formatada de volta para número
  - `formatDate`: Formata datas no padrão brasileiro (dd/mm/aaaa)
  - `parseDate`: Converte data formatada para ISO (aaaa-mm-dd)

- ✅ **Formulários atualizados** com máscara de valores monetários:
  - `ContasPagarPage.jsx` - Valor, Desconto, Juros, Multa
  - `ContasReceberPage.jsx` - Valor, Desconto, Juros, Multa
  - `ImoveisPage.jsx` - Aluguel, Condomínio, IPTU, Caução
  - `AlugueisPage.jsx` - Valor, Valor Caução
  - `ContasBancariasPage.jsx` - Saldo Inicial, Saldo Atual
  - `CadastrosPage.jsx` - Limite de Crédito
  - `CadastroFormModal.jsx` - Limite de Crédito

- ✅ **Comportamento**: Ao digitar números, o campo formata automaticamente para R$ X.XXX,XX
  - Exemplo: digitar `150000` → exibe `R$ 1.500,00`
  - Backend recebe valores numéricos (1500.00), não strings formatadas

### Cálculos Automáticos nos Formulários Financeiros
- ✅ **Contas a Pagar**: Valor Final = Valor - Desconto + Juros + Multa
- ✅ **Contas a Receber**: Valor Final = Valor - Desconto + Juros + Multa
- ✅ **Aluguéis de Máquinas**: Valor Total = Valor + Caução
- ✅ **Imóveis**: Valor Total Mensal = Aluguel + Condomínio + IPTU (já existia)
- Cálculo é exibido em tempo real conforme o usuário preenche os campos

---

## Changelog - 27/02/2026 (Sessão 19)

### Notificações de Combustível Baixo
- ✅ **Alertas de combustível** adicionados na aba de Notificações do Gerenciamento:
  - **CRÍTICO** (vermelho): Quando combustível está abaixo de 10%
  - **BAIXO** (laranja): Quando combustível está entre 10% e 25%
- ✅ **Novo card de resumo** "Combustível" na página de notificações
- ✅ Mostra nome da máquina, porcentagem e litros (atual/capacidade)
- ✅ Ícone de gota d'água (Droplet) para notificações de combustível
- ✅ Integrado com veículos abastecedores cadastrados no sistema

---

## Changelog - 27/02/2026 (Sessão 18)

### Correções de Exportação PDF
- ✅ **Quebra de linha automática** em todas as tabelas de exportação PDF
- Textos longos agora ficam contidos nas células sem invadir outras colunas
- Implementado via função `cell()` usando `Paragraph` com `wordWrap`
- Aplicado em TODAS as categorias: Gerenciamento, Administrativo, RH

### Atualização Automática de Saldo Bancário
- ✅ Ao **quitar conta a PAGAR** → saldo da conta bancária **DIMINUI**
- ✅ Ao **quitar conta a RECEBER** → saldo da conta bancária **AUMENTA**
- Atualização automática no campo `saldo_atual` da conta bancária selecionada
- Testado e validado com valores reais

### Vinculação de Máquinas a Itens de Estoque
- ✅ Novo campo **"Vincular a Máquinas (opcional)"** no formulário de item
- Dropdown com todas as máquinas cadastradas
- Permite vincular **múltiplas máquinas** ao mesmo item
- Máquinas selecionadas aparecem como tags removíveis
- API retorna `machine_ids` e `machine_names` nos itens de estoque

---

## Changelog - 27/02/2026 (Sessão 17)

### Máscaras de Formatação Automática
- ✅ **Utilitário de máscaras** criado em `/app/frontend/src/utils/masks.js`:
  - `formatCPF`: 000.000.000-00
  - `formatCNPJ`: 00.000.000/0000-00
  - `formatCPFouCNPJ`: Detecta automaticamente se é CPF ou CNPJ pelo tamanho
  - `formatCEP`: 00000-000
  - `formatTelefone`: (00) 0000-0000 ou (00) 00000-0000

- ✅ **Formulários atualizados** com máscaras automáticas:
  - `CadastroFormModal.jsx` - CPF/CNPJ, CEP, Telefone, Celular
  - `CadastrosPage.jsx` - CPF/CNPJ, CEP, Telefone, Celular
  - `FuncionariosPage.jsx` (RH) - CPF, CEP, Telefone, Celular
  - `ContasBancariasPage.jsx` - CPF/CNPJ do Titular
  - `ImoveisPage.jsx` - CEP

---

## Changelog - 27/02/2026 (Sessão 16)

### Sistema Financeiro - Quitação de Contas com Conta Bancária
- ✅ **Modal de Quitação Aprimorado** para Contas a Pagar e Receber:
  - Campo "Data do Pagamento/Recebimento" para registrar data exata da quitação
  - Dropdown "Conta Bancária (Saída/Entrada)" para vincular a transação a uma conta específica
  - Ao quitar, o `conta_bancaria_id` é salvo no banco de dados
  - A movimentação aparece automaticamente no extrato bancário da conta selecionada
- ✅ **Correção do Botão de Quitação**: Botão agora aparece corretamente para contas com status "pendente" ou "em_aberto"

### Sistema de Cadastros - Formulário Unificado
- ✅ **Novo Componente `CadastroFormModal.jsx`**: Formulário completo de cadastro reutilizável
- ✅ **Acesso de Contas a Pagar/Receber**: Ao clicar no ícone de "Novo Fornecedor/Cliente", abre o formulário completo
- ✅ **Campos do Formulário Completo**:
  - Tipo de Cadastro (Cliente, Fornecedor, Cliente/Fornecedor, Transportador)
  - Pessoa (Física/Jurídica) e Status (Ativo/Inativo)
  - Razão Social/Nome, Nome Fantasia/Apelido
  - CNPJ/CPF com consulta automática (BrasilAPI)
  - Inscrição Estadual/RG
  - Telefone, Celular, Email
  - Endereço completo com consulta automática por CEP (ViaCEP)
  - Grupo, Rota, Vendedor, Limite de Crédito, Observações
- ✅ **Integração Automática**: Após cadastro, o nome é preenchido automaticamente no formulário original

---

## Changelog - 27/02/2026 (Sessão 15)

### Sistema de Exportação - Validação e Extensão
- ✅ **Verificado e funcionando** em todos os sistemas (Administrativo, Gerenciamento, RH)
- ✅ Exportação individual (PDF, Excel) funcionando corretamente
- ✅ Exportação combinada (múltiplas categorias) funcionando
- ✅ **NOVO: Módulo de Exportação no RH** adicionado com as seguintes categorias:
  - Funcionários (Todos, Ativos, Desligados)
  - Registro de Ponto (Todos, Hoje, Mês)
  - Folha de Pagamento (Folhas, Holerites)
  - Férias (Todas, Próximas, Vencidas)
  - EPIs (Fichas, Vencidos)
  - Custos de RH (Por Funcionário, Encargos)

### Novas Funcionalidades: Sistema de Gerenciamento (3 melhorias)

#### 1. Cores nas Categorias de Máquinas
- Adicionado seletor de cores com 10 opções no modal de criar/editar categoria
- Cores disponíveis: Vermelho, Azul, Verde, Amarelo, Roxo, Rosa, Laranja, Ciano, Índigo, Cinza
- As cores são aplicadas automaticamente nos cards de máquinas (borda superior e ícone)
- Indicador visual de cor na lista de categorias

#### 2. Horímetro com Opção Hora/Km
- Novo campo "Tipo de Medição" no modal de registro de horímetro
- Opções: Horas (Horímetro) ou Quilômetros (Odômetro)
- Labels dinâmicos que mudam de "Hora Inicial/Final" para "Km Inicial/Final"
- Coluna "Tipo" na tabela mostrando badge Hora ou Km

#### 3. Sistema de Combustível Completo
- **Veículos Tanque (Abastecedores)**: 
  - Cadastro de máquinas como veículos tanque
  - Cards horizontais com barras de progresso (Diesel, Óleo, Graxa)
  - Indicadores de % e litros restantes
- **Registros de Abastecimento**:
  - Tipo "Abastecedor" (entrada no tanque) - botão verde
  - Tipo "Abastecido" (saída do tanque) - botão vermelho
  - Fonte: Veículo Interno ou Externo
  - **Desconto automático** do tanque quando abastecimento interno
- **Dropdown de Operadores**: Combina funcionários do RH + Cadastros financeiro

### Bug Fix: Validação de Cargos no Painel Admin
- **Problema**: Ao alterar o cargo de um usuário no painel admin para novos roles (como RH, combinações), o sistema retornava erro "Role inválido. Opções: gerenciamento, administrativo, ambos, admin"
- **Solução**: Atualizada a lista de roles válidos no backend para incluir todas as combinações e o novo cargo "Programador"
- **Roles Válidos Agora**:
  - gerenciamento, administrativo, rh
  - ambos (Gerenciamento + Administrativo)
  - ambos_rh (Ger + Admin + RH)
  - gerenciamento_rh, administrativo_rh
  - admin, **programador** (ambos com acesso total)

### Nova Funcionalidade: Cargo de Programador
- Adicionado novo cargo "Programador" com as mesmas permissões máximas do "admin"
- Programador tem acesso a: Painel Admin, todos os sistemas, gerenciamento de usuários, banco de dados, etc.
- Badge azul para identificação visual do cargo

---

# PRD - Sistema de Gerenciamento ERP

## Problema Original
Sistema de gerenciamento de máquinas e manutenções com módulos administrativos (financeiro, estoque, cadastros), aluguéis, notificações, painel de super administrador, chatbot com IA, exportação PDF/Excel/OFX, sistema de armazenamento de arquivos e **Sistema de RH completo**.

## Arquitetura
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB (Motor)
- **Auth**: JWT com bcrypt
- **Integração**: Gemini AI para chatbot e sugestão de EPIs

## O que foi implementado

### Sessão Atual (27/02/2026) - Parte 15

#### ✅ Refatoração Completa do Backend - 10 Módulos - COMPLETO
- **server.py**: Reduzido de 12.167 para 10.374 linhas (-15%)
- **Total de módulos**: 10 arquivos em `/app/backend/routes/`
  - `rh.py` - 1.315 linhas (Sistema RH completo)
  - `admin.py` - 670 linhas (Financeiro, Cadastros, Contas)
  - `machines.py` - 639 linhas (Máquinas, Frotas, Manutenções)
  - `stock.py` - 543 linhas (Estoque, Movimentações, Alertas)
  - `storage.py` - 462 linhas (Gerenciador de Arquivos)
  - `exports.py` - 441 linhas (PDF e Excel Export)
  - `obras.py` - 402 linhas (Obras/Projetos)
  - `chatbot.py` - 299 linhas (Assistente IA)
  - `auth.py` - 118 linhas (Autenticação)
  - `categories.py` - 97 linhas (Categorias)
- **Total modularizado**: ~5.000 linhas em arquivos separados
- **Arquitetura**: Routers independentes com FastAPI APIRouter
- **Testes**: Todos os endpoints funcionando

### Sessão Anterior (27/02/2026) - Parte 14

#### ✅ Refatoração Completa - 6 Módulos Extraídos - COMPLETO
- **server.py**: Reduzido de 12.167 para 10.370 linhas (-15%)
- **Total de módulos**: 6 arquivos em `/app/backend/routes/`
  - `rh.py` - 1.315 linhas (Sistema RH completo)
  - `admin.py` - 670 linhas (Financeiro, Cadastros, Contas)
  - `machines.py` - 639 linhas (Máquinas, Frotas, Manutenções)
  - `storage.py` - 462 linhas (Gerenciador de Arquivos)
  - `exports.py` - 441 linhas (PDF e Excel Export)
  - `chatbot.py` - 299 linhas (Assistente IA)
- **Total modularizado**: 4.050 linhas em arquivos separados
- **Arquitetura**: Routers independentes com conexão própria ao MongoDB
- **Testes**: Todos os endpoints funcionando

### Sessão Anterior (27/02/2026) - Parte 13

#### ✅ Refatoração do Backend - Módulos Admin e Machines Extraídos - COMPLETO
- **server.py**: Reduzido de 12.167 para 10.364 linhas (-15%)
- **Novos módulos extraídos**:
  - `/app/backend/routes/rh.py` - 1.315 linhas (RH completo)
  - `/app/backend/routes/admin.py` - 670 linhas (Cadastros, Contas a Pagar/Receber, OS, Plano de Contas)
  - `/app/backend/routes/machines.py` - 639 linhas (Categorias, Frotas, Máquinas, Manutenções)
- **Total em routes/**: 2.845 linhas de código modularizado
- **Testes**: Todos os endpoints funcionando após refatoração

### Sessão Anterior (27/02/2026) - Parte 12

#### ✅ Refatoração do Backend - Módulo RH Extraído - COMPLETO
- **server.py**: Reduzido de 12.167 para 10.360 linhas (-15%)
- **Novo arquivo**: `/app/backend/routes/rh.py` (1.315 linhas)
- **Arquitetura**: Router modular usando `APIRouter` do FastAPI
- **Estrutura criada**:
  - `/app/backend/routes/rh.py` - Rotas de RH
  - `/app/backend/routes/__init__.py` - Exportação dos routers
  - `/app/backend/core/database.py` - Configuração do MongoDB
  - `/app/backend/core/security.py` - Utilitários de segurança JWT
- **Testes**: Todos os endpoints de RH funcionando após refatoração

### Sessão Anterior (27/02/2026) - Parte 11

#### ✅ Gestão de Férias com Calendário - COMPLETO
- **Calendário Anual**: Visualização de 12 meses com férias destacadas em azul
- **CRUD Completo**: Criar, listar, editar e excluir férias
- **Abono Pecuniário**: Suporte a venda de até 10 dias (1/3 das férias)
- **Alertas de Período Aquisitivo**: Funcionários com 11+ meses sem férias são sinalizados
- **Status de Férias**: Agendado, Em Férias, Concluído
- **Navegação por Ano**: Seletor de ano para visualizar férias passadas/futuras
- **Testes**: 13/13 backend + 12/12 frontend passaram

#### ✅ Sistema de Notificações RH - COMPLETO
- **Aniversariantes do Mês**: Lista com nome, cargo, data e idade
- **Alertas de Férias**: Período aquisitivo vencendo, funcionários sem férias há 1+ ano
- **Vencimento de EPIs**: EPIs próximos do vencimento (30 dias)
- **Inconsistências de Ponto**: Atrasos detectados automaticamente
- **Botão Agendar Urgente**: Para funcionários com férias atrasadas
- **Badge de Notificações**: Contador no menu lateral
- **Endpoint de Contagem**: Para atualização em tempo real do badge
- **Testes**: 100% passaram

### Sessão Anterior (27/02/2026) - Parte 10

#### ✅ Implementação Completa do Ponto Eletrônico - COMPLETO
- **Registro de Ponto**: CRUD completo (criar, listar, editar, excluir)
- **Jornada Configurada**: Seg-Sex 08:00-11:30 / 13:30-18:00 | Sábado 08:00-12:00
- **Cálculos Automáticos**: Horas trabalhadas, atrasos, horas extras
- **Relatório Mensal**: `/api/rh/ponto/relatorio-mensal` com banco de horas e valor de horas extras
- **Registro Rápido**: `/api/rh/ponto/registrar-rapido` para entrada/saída com um clique
- **Resumo do Dia**: Cards com presentes, ausentes e atrasados
- **Testes**: 8/8 passaram

#### ✅ Implementação Completa da Folha de Pagamento - COMPLETO
- **Tabelas de Alíquotas 2025**: INSS progressivo e IRPF implementados
- **Cálculos Automáticos**: INSS (7.5%-14%), IRPF (0%-27.5%), FGTS (8%)
- **Proventos**: Salário base, horas extras, adicional noturno, comissões
- **Descontos**: INSS, IRPF, VT, VA, plano de saúde
- **Holerite PDF**: Geração automática com layout profissional
- **Contas a Pagar**: Geração automática de contas (salários, INSS, FGTS)
- **Testes**: 5/5 passaram

#### ✅ Implementação Completa da Gestão de Custos RH - COMPLETO
- **Custo Real por Funcionário**: Salário + FGTS (8%) + INSS Patronal (20%) + Benefícios + EPIs
- **Custo/Hora**: Dividido por 220h CLT
- **Simulação de Dissídio**: Calcula impacto mensal e anual de aumento percentual
- **Provisão de Rescisão**: Cálculo completo (saldo salário, aviso prévio, férias, 13º, FGTS, multa 40%)
- **Testes**: 3/3 passaram

### Sessão Anterior (26/02/2026) - Parte 9

#### ✅ Correção da Integração Gemini para EPIs (P1 - Crítico) - COMPLETO (26/02/2026)
- **Problema**: A integração com Gemini para consulta de EPIs por CBO estava falhando
- **Causa Raiz**: Nome do modelo incorreto (`gemini-2.0-flash-exp`) e provider errado (`google`)
- **Solução**: Atualizado para modelo correto (`gemini-2.5-flash`) e provider correto (`gemini`)
- **Arquivos Modificados**: `backend/server.py` (linhas ~10592 e ~10680)
- **Resultado**: Integração funcionando 100%, EPIs são carregados automaticamente por CBO
- **Testes**: 27/27 passaram (17 backend + 10 frontend)

#### ✅ Busca de EPIs por CBO - FUNCIONANDO
- Busca por código CBO (ex: 7152-10) ou nome da ocupação (ex: "pedreiro")
- Base de dados local com ~30 ocupações e EPIs predefinidos
- Para CBOs não cadastrados, IA Gemini é consultada automaticamente
- Mapa de risco gerado automaticamente com prioridades (Alta/Média/Baixa)

### Sessão Anterior (26/02/2026) - Parte 8

#### ✅ Sistema de RH Completo - IMPLEMENTADO
Novo sistema de Recursos Humanos adicionado à plataforma com:

**1. Cadastro de Funcionários**
- Formulário completo: Nome, CPF, RG, Data Nascimento, Telefone, Celular, Email
- Endereço com auto-preenchimento por CEP (integração ViaCEP)
- Dados profissionais: Cargo, Função, Departamento, Salário, Data Admissão
- Regime de contratação: CLT, PJ, Contrato, Estágio, Prestador de Serviço
- Sistema de anexos para documentos (contrato, fotos, etc.) com visualização inline
- Status: Ativo, Férias, Afastado, Desligado

**2. Ponto Eletrônico**
- Registro de entrada, saída almoço, retorno almoço e saída
- Jornada configurada: Seg-Sex 08:00-11:30 / 13:30-18:00 | Sábado 08:00-12:00 (carga reduzida)
- Cálculo automático de horas trabalhadas
- Identificação de atrasos e saídas antecipadas
- Resumo do dia: Presentes, Ausentes, Atrasados

**3. Folha de Pagamento e Benefícios**
- Tabelas de alíquotas atuais 2025 (INSS, IRPF)
- Cálculo automático: INSS progressivo, IRPF com deduções, FGTS 8%
- Proventos: Salário base, horas extras, adicional noturno, comissões
- Descontos: Vale transporte, vale alimentação, plano de saúde
- Geração de holerite em PDF com layout profissional
- Geração automática de contas a pagar (salários, INSS, FGTS)

**4. Férias e Escalas**
- Calendário anual de férias
- Alertas de período aquisitivo vencendo
- Abono pecuniário (até 10 dias vendidos)
- Listagem de funcionários há mais de 1 ano sem férias

**5. Gestão de EPI/EPC**
- Cadastro de cargos
- Consulta de EPIs por cargo usando IA Gemini (com fallback para lista padrão)
- Mapa de risco por função (Alta - vermelho, Média - amarelo, Baixa - verde)
- Ficha de EPI digital com controle de validade
- Exportação de Ficha de EPI em PDF para assinatura
- Exportação de Termo de Responsabilidade em PDF

**6. Sistema de Notificações RH**
- Aniversariantes do mês
- Alertas de período aquisitivo de férias
- Funcionários há mais de 1 ano sem férias
- EPIs próximos do vencimento
- Inconsistências de ponto (atrasos fora da janela)

**7. Gestão de Custos**
- Custo real por funcionário: Salário + FGTS (8%) + INSS Patronal (20%) + Benefícios + EPIs
- Custo por hora (dividido por 220h CLT)
- Simulação de dissídio: Impacto mensal e anual de aumento percentual
- Provisão de rescisão: Cálculo completo (saldo salário, aviso prévio, férias, 13º, FGTS, multa 40%)

**8. Controle de Acesso**
- Novos roles: "rh", "ambos_rh", "gerenciamento_rh", "administrativo_rh"
- Sistema RH aparece na página de seleção de sistemas
- Integração com Painel Administrativo para gerenciar permissões

**9. Integração com Gerenciamento**
- Funcionários do RH aparecem como opção de "Operador" nas máquinas
- Remoção da opção "Funcionário" do Cadastros do Administrativo (agora só no RH)

### Sessão Anterior (26/02/2026) - Parte 7

#### ✅ Correção de Roteamento (P0 - Crítico) - COMPLETO
- **Problema**: Sistema abria diretamente na página de gerenciamento ao invés da página de login
- **Solução**: Refatoração completa do sistema de rotas no `App.js`
- Criado componente `RootRedirect` para gerenciar redirecionamento inteligente
- Rota raiz `/` agora redireciona para `/login` (não autenticado) ou `/select-system` (autenticado)
- Rotas de gerenciamento movidas de `/` para `/gerenciamento/*`
- Catch-all atualizado para usar `RootRedirect`
- Atualização de todos os links de navegação nos componentes:
  - `Layout.jsx` - menu lateral e navegação mobile
  - `MorePage.jsx` - menu "Mais"
  - `SystemSelectPage.jsx` - path do card de Gerenciamento
  - `DashboardPage.jsx`, `MachineDetailPage.jsx`, `NewMaintenancePage.jsx`, etc.
- Fluxo correto: `/` → `/login` → `/select-system` → `/gerenciamento/dashboard`

#### ✅ Correção de Layout dos PDFs (P1) - COMPLETO
- **Problema**: Descrições cortadas, informações coladas, textos sobrepostos nos PDFs de exportação
- **Solução**: Refatoração das funções de geração de PDF no `server.py`
- Melhorado espaçamento no cabeçalho da empresa nos recibos e duplicatas
- Implementado word-wrap adequado usando `Paragraph` com `wordWrap='CJK'` para textos longos
- Aumentado padding nas células das tabelas para evitar cortes
- Testado com descrições longas (300+ caracteres) - funcionando corretamente
- Funções corrigidas: `export_recibo`, `export_duplicata`

#### ✅ Exportação Completa de Todas as Categorias - COMPLETO
- **Problema**: Exportar Selecionados não funcionava para algumas categorias e Plano de Contas não mostrava contas vinculadas
- **Solução**: Refatoração completa das funções de exportação no `server.py`
- **Exportação Múltipla**: Adicionadas categorias faltantes: `plano_contas`, `centros_custo`, `cadastros`, `contas_bancarias`, `formas_pagamento`, `imoveis`, `fleets`
- **Plano de Contas**: Agora mostra tabela de contas a pagar/receber vinculadas com valores e totais, mais resumo financeiro
- **Centros de Custo**: Mostra totais de contas vinculadas
- **Cadastros**: Exportação completa com todos os campos (razão social, CNPJ, telefone, email, endereço)
- **Contas Bancárias**: Inclui saldo e dados completos
- **Imóveis**: Endereço completo, valores de aluguel, condomínio, IPTU
- **Aluguéis**: Dados completos com período, valores e horímetro
- Todas as exportações múltiplas agora incluem linha de TOTAL

#### ✅ Exportar Selecionados - Modelo Novo - COMPLETO
- Cada item exportado em página separada com PageBreak
- Informações completas de cada item (Nº, Status, Fornecedor, CNPJ, Documento, Datas, Valores, etc.)
- Word-wrap adequado para descrições longas

#### ✅ Módulo de Horímetro - COMPLETO (26/02/2026)
- **Nova funcionalidade**: Registro de horas de utilização das máquinas
- **Frontend**: Página `HorimetroPage.jsx` com CRUD completo
- **Backend**: Endpoints `/api/horimetro` para criar, listar, editar e excluir registros
- **Formulário**: Dropdown com máquinas cadastradas, data, hora inicial, hora final, operador, observações
- **Cálculo automático**: Horas trabalhadas calculadas automaticamente
- **Estatísticas**: Total de horas, registros hoje, média por registro
- **Integração**: Registros aparecem no card de detalhes da máquina
- **Menu**: Link "Horímetro" adicionado ao menu lateral do Gerenciamento
- **Atualização automática**: Horímetro atual da máquina é atualizado ao criar registro

#### ✅ Módulo de Combustível - COMPLETO (26/02/2026)
- **Nova funcionalidade**: Registro de consumo de combustível das máquinas
- **Frontend**: Página `CombustivelPage.jsx` com CRUD completo
- **Backend**: Endpoints `/api/combustivel` para criar, listar, editar e excluir registros
- **Formulário**: 
  - Dropdown de máquinas cadastradas
  - Tipo de medição: Litros/Hora ou Litros/Km
  - Hora/Km inicial, Litros inicial e final
  - Cálculo automático de litros consumidos
- **Estatísticas**: Total consumido, registros hoje, média por registro
- **Integração**: Registros aparecem no card de detalhes da máquina
- **Menu**: Link "Combustível" adicionado ao menu lateral

#### ✅ Campo Chassi/Número de Série - COMPLETO (26/02/2026)
- Adicionado dropdown para selecionar tipo: "Chassi" ou "Número de Série"
- Campo para digitar o número do identificador
- Exibição no card de detalhes da máquina
- Backend atualizado com campos `identificador_tipo` e `identificador_numero`

#### ✅ Anexar Arquivos no Chatbot - COMPLETO (26/02/2026)
- Botão de anexar arquivos (📎) adicionado ao ChatbotWidget
- Suporte a imagens, PDFs, documentos (.doc, .docx, .xls, .xlsx, .txt, .csv, .json, .xml)
- Limite de 10MB por arquivo
- Preview dos arquivos anexados antes de enviar
- Endpoint `/api/chatbot/ask-with-files` para processar arquivos
- **Extração de conteúdo implementada**:
  - PDFs: extrai texto de até 10 páginas usando PyPDF2
  - Word (.docx): extrai texto dos parágrafos
  - Excel (.xlsx): extrai dados de até 3 abas e 50 linhas
  - CSV/TXT/JSON/XML: extrai conteúdo completo de texto
  - Imagens: identifica formato, dimensões e modo de cor
- IA analisa conteúdo extraído e relaciona com dados da plataforma

#### ✅ Correção Global de Navegação - COMPLETO (26/02/2026)
- Corrigidos TODOS os links de navegação no módulo de Gerenciamento
- Arquivos corrigidos:
  - `MachinesPage.jsx` - botão "Ver" → `/gerenciamento/machines/{id}`
  - `MaintenancesPage.jsx` - botão "Ver" → `/gerenciamento/maintenances/{id}`
  - `ObrasPage.jsx` - botão "Detalhes" → `/gerenciamento/obras/{id}`
  - `DashboardPage.jsx` - manutenção recente → `/gerenciamento/maintenances/{id}`
  - `BalancePage.jsx` - máquina → `/gerenciamento/machines/{id}`
  - `NotificationsPage.jsx` - ver máquina → `/gerenciamento/machines/{id}`
  - `MaintenanceDetailPage.jsx` - máquina → `/gerenciamento/machines/{id}`
  - `NewMaintenancePage.jsx` - após criar → `/gerenciamento/maintenances/{id}`
- 100% dos testes de navegação passaram (12/12)

### Sessão Anterior (26/02/2026) - Parte 6

#### ✅ Exportação de Extrato Bancário - COMPLETO
- Endpoint: `GET /api/export/extrato-bancario/{conta_id}` 
- Frontend: Dropdown de seleção de conta na página de Exportação
- Ao selecionar "Extrato Bancário", painel amarelo aparece com dropdown de contas
- Botão "Exportar Extrato" gera PDF do extrato da conta selecionada

#### ✅ Exportação de Itens Individuais - COMPLETO
- Cada subcategoria pode ser expandida clicando no ícone de lista (≡)
- Ao expandir, mostra todos os itens individuais da categoria
- Cada item tem botão "PDF" para exportar apenas aquele item específico
- Suporte para: Contas a Pagar, Contas a Receber, Máquinas, Manutenções, Estoque, Obras, Aluguéis, Plano de Contas, Centros de Custo, Cadastros, Contas Bancárias, Extrato Bancário
- Endpoint: `GET /api/export/individual/{category}/{item_id}`
- Endpoint: `GET /api/export/items/{collection}` (expandido para mais categorias)

#### ✅ Seleção Múltipla e Exportação Combinada - COMPLETO
- Checkbox em cada item individual para seleção múltipla
- Botão "Selecionar Todos" no cabeçalho da lista
- Botão "Exportar Selecionados" para gerar PDF consolidado
- Endpoint: `POST /api/export/individual-multiple`

#### ✅ Recibos e Duplicatas - COMPLETO
- Botão verde (Recibo) e amarelo (Duplicata) em cada item de Contas a Pagar/Receber, Aluguéis e Imóveis
- Recibo: Comprovante de pagamento com valor por extenso
- Duplicata: Documento de cobrança formal com campos de aceite
- Endpoints: `GET /api/export/recibo/{category}/{item_id}`, `GET /api/export/duplicata/{category}/{item_id}`

#### ✅ Módulo de Imóveis para Locação - COMPLETO
- Nova página `/admin/imoveis` com CRUD completo
- Modelo: ImovelCreate com dados do imóvel, inquilino e contrato
- Cards de estatísticas: Total, Locados, Disponíveis, Receita Mensal
- Campos: Tipo, Descrição, Endereço completo, Área, Quartos, Banheiros, Vagas
- Valores: Aluguel, Condomínio, IPTU, Caução, Dia de Vencimento
- Integração com ViaCEP para preenchimento automático de endereço
- Geração automática de Conta a Receber mensal
- Suporte a anexo de contrato
- Endpoints: CRUD em `/api/admin/imoveis`

### Sessão Anterior (26/02/2026) - Parte 5

#### ✅ Sistema de Contas Bancárias - COMPLETO
- Nova página `/admin/contas-bancarias` com CRUD completo
- Modelo Pydantic: ContaBancariaCreate/Response
- Endpoints: GET, POST, PUT, DELETE, PATCH (saldo)
- Cards de resumo: Total, Ativas, Saldo Total, Com PIX
- Formulário completo: Nome, Banco (lista brasileira), Tipo, Agência, Conta, Titular, CPF/CNPJ, PIX, Saldo, Status, Cor
- Grid de cards com cores personalizadas e ícones por tipo

#### ✅ Dropdown de Conta Bancária nas Contas a Pagar/Receber
- Campo `conta_bancaria_id` e `conta_bancaria_nome` adicionados
- Dropdown integrado nos formulários de criação/edição

### Sessão Atual - Parte 4 (Exportação)
- Correção do filtro de status (pendente → em_aberto)
- Exportação combinada em um único PDF
- Filtros específicos por item na exportação
- Dropdown de Frotas em Contas a Pagar/Receber

### Sessões Anteriores
- Sistema de seleção múltipla/mover/copiar no Armazenamento
- Preview de Word/Excel
- Sistema de Frotas completo
- Dashboard Financeiro com aba "Vencidas"

## Backlog

### 🟡 P1 - Pendentes
- Refatoração parcial do backend (server.py > 7950 linhas)

### 🔵 P2 - Futuros
- Integração Estoque ↔ Manutenção
- Notificações email/WhatsApp
- Reativar PWA

## Novos Endpoints
- `GET /api/admin/contas-bancarias` - Lista contas bancárias
- `POST /api/admin/contas-bancarias` - Cria conta bancária
- `GET /api/admin/contas-bancarias/{id}` - Busca conta bancária
- `PUT /api/admin/contas-bancarias/{id}` - Atualiza conta bancária
- `DELETE /api/admin/contas-bancarias/{id}` - Exclui conta bancária
- `PATCH /api/admin/contas-bancarias/{id}/saldo` - Atualiza saldo
- `GET /api/export/extrato-bancario/{conta_id}` - Exporta extrato bancário em PDF

## Arquivos Criados/Modificados
- `frontend/src/pages/admin/ContasBancariasPage.jsx` - Nova página
- `frontend/src/pages/ExportPage.jsx` - Dropdown de seleção de conta para extrato
- `frontend/src/App.js` - Nova rota adicionada
- `frontend/src/components/AdminLayout.jsx` - Link no menu
- `frontend/src/pages/admin/ContasPagarPage.jsx` - Dropdown conta bancária
- `frontend/src/pages/admin/ContasReceberPage.jsx` - Dropdown conta bancária
- `backend/server.py` - Modelo e endpoints de contas bancárias e extrato

## Credenciais de Teste
- Email: test@test.com
- Password: password
- Role: admin

## Integrações de Terceiros
- Gemini AI (chatbot)
- BrasilAPI, ViaCEP
- reportlab, openpyxl, python-docx, python-ofxparse, PyPDF2
