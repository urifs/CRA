# CRA Construtora - Sistema de Gestão Empresarial (ERP)


## Changelog - 11/03/2026 (Sessão 28 - Continuação 3)

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
