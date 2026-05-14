# Backup Completo do Banco de Dados — CRA Construtora

**Gerado em:** 2026-05-14T18:38:24.645414+00:00
**Banco origem:** test_database (MongoDB)
**Total de collections:** 65
**Total de documentos:** 1340

## 📦 Arquivos deste pacote

| Arquivo | Descrição |
|---------|-----------|
| `dump.json` | Dump COMPLETO de todas as collections — todos os campos, todos os documentos. Tipos não-JSON estão envelopados (`{"$date": ...}` e `{"$oid": ...}`). |
| `schema.json` | Schema inferido a partir do dump (tipos detectados + % de presença por campo). |
| `migrate_to_supabase.sql` | DDL Postgres com `CREATE TABLE IF NOT EXISTS` para cada collection (esqueleto). |
| `MANIFEST.md` | Este arquivo. |

## 🧭 Como o Claude Code (ou você) deve ler `dump.json`

```json
{
  "_meta": { "database": "...", "exported_at": "...", "collection_count": 65, "total_documents": 1340 },
  "collections": {
    "funcionarios": [ { "id": "...", "nome": "...", ... }, ... ],
    "contas_pagar": [ ... ],
    "nfe_importadas": [ ... ]
  }
}
```

### Convenções de tipos

- **Datas**: strings ISO 8601 normais (`"2026-02-25T19:41:25.665067+00:00"`) ou envelopes `{"$date": "..."}` para `datetime` nativo do BSON.
- **ObjectId**: objetos `{"$oid": "507f1f77bcf86cd799439011"}`. NA MAIORIA das collections o `_id` foi removido e usamos a chave `id` (UUID v4 em string) — Supabase pode usar `id` como PK.
- **Binary**: `{"$binary": "<base64>"}` (raro, só em alguns artefatos).
- **Arrays / objetos aninhados**: preservados como JSON puro → mapear para `jsonb` no Postgres.

## 🚀 Instruções para o Claude Code converter para Supabase

**Prompt sugerido para colar no Claude Code:**

> Você é um especialista em migração MongoDB → Supabase Postgres.
> Em anexo está o `dump.json` com 65 collections (~1340 docs) do nosso ERP CRA
> Construtora. Use `MANIFEST.md` e `schema.json` como referência de tipos.
>
> Faça:
> 1. Crie as tabelas no Supabase (use `migrate_to_supabase.sql` como ponto
>    de partida e refine os tipos olhando o `schema.json`).
> 2. Para cada collection do dump, gere um script Python (idempotente)
>    que insere os documentos via `supabase-py` ou direto via `psycopg`.
> 3. Trate campos aninhados como `jsonb`.
> 4. Use `id` (UUID em string) como PRIMARY KEY quando existir.
> 5. Habilite Row Level Security depois (não no setup inicial).
> 6. Crie índices para os campos mais usados: `created_at`, `status`,
>    `funcionario_id`, `entity_type`, `entity_id`, `cnpj_emitente`.
>
> Documentos importantes do domínio:
> - `users`: contas de acesso. Hash bcrypt em `password_hash`.
> - `funcionarios`: cadastro de colaboradores (RH).
> - `contas_pagar` / `contas_receber`: financeiro com `anexos[]`.
> - `attachments`: tabela mestre de anexos por entidade.
> - `nfe_importadas` / `nfse_importadas`: notas fiscais importadas.
> - `chat_*`: histórico do chatbot IA e PDFs gerados.
> - `tasks`: caixa de tarefas inter-sistemas.
>
> Entregue: 1) DDL final completo, 2) script de import Python, 3) lista
> de índices recomendados, 4) checklist de validação pós-migração.

## 📊 Inventário de Collections

| Collection | Docs | Domínio |
|------------|-----:|---------|
| `alugueis` | 1 | Financeiro/Frota |
| `attachments` | 3 | Anexos (polimórfico) |
| `audit_logs` | 763 | Auditoria |
| `banco_horas_ajustes` | 0 | RH |
| `cadastros` | 8 | Financeiro (Clientes/Fornecedores) |
| `categories` | 6 | Sistema |
| `centros_custo` | 1 | Financeiro |
| `chat_artifacts` | 13 | Chat IA (PDFs gerados) |
| `chat_conversations` | 18 | Chat IA |
| `chat_knowledge_base` | 4 | Chat IA (PCMSO/PGR/LTCAT/CCT) |
| `chat_messages` | 54 | Chat IA |
| `combustivel` | 7 | Frota |
| `conciliacoes` | 2 | Financeiro |
| `contas_bancarias` | 2 | Financeiro |
| `contas_pagar` | 39 | Financeiro |
| `contas_receber` | 16 | Financeiro |
| `counters` | 6 | Sistema |
| `custos_rh_config` | 1 | RH |
| `epi_cargos` | 1 | RH (EPI) |
| `epi_fichas` | 1 | RH (EPI) |
| `extratos_bancarios` | 2 | Financeiro |
| `ferias` | 0 | RH |
| `ferias_alertas_dispensados` | 0 | RH |
| `fleets` | 2 | Frota |
| `folder_passwords` | 3 | Armazenamento |
| `folha_pagamento` | 1 | RH |
| `folhas_importadas` | 0 | RH |
| `formas_pagamento` | 1 | Financeiro |
| `fornecedores` | 0 | Cadastros |
| `funcionarios` | 9 | RH |
| `horimetro` | 1 | Frota |
| `imoveis` | 1 | Financeiro/Imóveis |
| `jornadas_trabalho` | 2 | RH |
| `logs_importacao` | 3 | Financeiro |
| `machines` | 6 | Frota |
| `maintenances` | 6 | Frota (Manutenção) |
| `movimentacoes_contas` | 1 | Financeiro |
| `nfe_certificados` | 1 | Financeiro/NF-e |
| `nfe_importadas` | 155 | Financeiro/NF-e |
| `nfse_importadas` | 3 | Financeiro/NFS-e |
| `notas_emitidas` | 2 | Financeiro/NFS-e Emissão |
| `notificacoes_dispensadas` | 0 | Sistema |
| `notifications` | 3 | Sistema |
| `obras` | 2 | Frota/Obras |
| `ordens_servico` | 8 | Financeiro/OS |
| `plano_contas` | 6 | Financeiro |
| `ponto_abonos` | 1 | RH (Ponto) |
| `ponto_observacoes` | 1 | RH (Ponto) |
| `ponto_registros` | 135 | RH (Ponto) |
| `produtos` | 0 | Estoque |
| `produtos_admin` | 1 | Financeiro |
| `rh_notificacoes` | 4 | RH |
| `solicitacoes_folha` | 0 | RH |
| `solicitacoes_folha_financeiro` | 0 | RH↔Financeiro |
| `stock_categories` | 1 | Estoque |
| `stock_items` | 5 | Estoque |
| `stock_movements` | 2 | Estoque |
| `stock_subcategories` | 2 | Estoque |
| `storage_trash` | 1 | Armazenamento |
| `subcategories` | 1 | Sistema |
| `subfleets` | 1 | Frota |
| `tasks` | 1 | Sistema (Caixa de Tarefas) |
| `usage_logs` | 3 | Auditoria |
| `users` | 15 | Auth/Sistema |
| `veiculos_abastecedores` | 2 | Frota |

## 🔗 Relacionamentos importantes

- `attachments.entity_id` → referencia o `id` de **muitas** collections (campo `entity_type` indica qual). Polimórfico.
- `contas_pagar.fornecedor_id` → `cadastros.id` (categoria=fornecedor).
- `contas_receber.cliente_id` → `cadastros.id` (categoria=cliente).
- `ordens_servico.cliente_id` → `cadastros.id`.
- `folha_pagamento.funcionario_id` → `funcionarios.id`.
- `ferias.funcionario_id`, `ponto_registros.funcionario_id`, `epi_fichas.funcionario_id` → `funcionarios.id`.
- `chat_messages.conversation_id` → `chat_conversations.id`.
- `nfe_importadas.certificado_id` → `nfe_certificados.id`.
- `notas_emitidas.cliente_id` → `cadastros.id`.
- `solicitacoes_folha_financeiro.folha_id` → `folhas_importadas.id`.
- `tasks.target_system` ∈ { `rh`, `administrativo`, `gerenciamento` }.

## ⚠️ Pontos de atenção na migração

1. **Senhas (`users.password_hash`)**: já vêm com bcrypt — preserve a string como `text`. Não rehash.
2. **Datas em string vs datetime BSON**: o mesmo campo pode aparecer dos dois jeitos em documentos diferentes (legado). Trate como `timestamptz` aceitando os dois formatos no parser.
3. **Arrays de IDs como `parcelas_ids`, `contas_pagar_ids`**: mapeie para `text[]` ou `jsonb`.
4. **Campos com `null` ou ausentes** em até 60% dos documentos: NÃO use NOT NULL (o DDL gerado já considera isso).
5. **`chat_artifacts.content_b64`**: PDFs em base64. Pode crescer — considere migrar para Supabase Storage e guardar só a URL.
6. **`audit_logs` (763 docs)**: log enorme; considere migrar para tabela particionada por mês.
7. **`nfe_importadas.xml_base64`**: XML completo da NF-e em base64; idem ao item 5.

## ✅ Checklist pós-migração

- [ ] Contagem de linhas por tabela bate com `schema.json[collection].document_count`.
- [ ] `users` migrados: confirmar login com bcrypt original.
- [ ] `funcionarios` migrados: cada `id` único, sem duplicidade.
- [ ] FKs polimórficas (`attachments`): teste consultar anexos por `entity_type`.
- [ ] Índices criados em `created_at`, `status`, `funcionario_id`, `entity_type+entity_id`.
- [ ] Backup do Supabase ativado.
