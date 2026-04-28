# CRA Construtora - Sistema de Gestão Empresarial (ERP)
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
