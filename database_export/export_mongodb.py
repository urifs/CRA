"""
Export completo do MongoDB da CRA Construtora.

Gera:
  - dump.json                  → todas as collections, todos os documentos
  - schema.json                → schema inferido (tipos por campo, contagens)
  - MANIFEST.md                → instruções legíveis para humano + Claude
  - migrate_to_supabase.sql    → DDL Postgres equivalente (esqueleto)

Uso:
    cd /app/backend && source .env && cd ../database_export
    python3 export_mongodb.py
"""
import asyncio
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).parent
OUT_DUMP = ROOT / "dump.json"
OUT_SCHEMA = ROOT / "schema.json"
OUT_MANIFEST = ROOT / "MANIFEST.md"
OUT_SQL = ROOT / "migrate_to_supabase.sql"


def _serialize(value):
    """Converte tipos BSON/Mongo para JSON puro."""
    if isinstance(value, ObjectId):
        return {"$oid": str(value)}
    if isinstance(value, datetime):
        return {"$date": value.isoformat()}
    if isinstance(value, bytes):
        import base64
        return {"$binary": base64.b64encode(value).decode("ascii")}
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    return value


def _classify_type(value) -> str:
    """Identifica o tipo de uma valor para o schema."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        # heurística para datas em string
        if len(value) >= 19 and value[4] == "-" and value[7] == "-":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
                return "datetime-string"
            except (ValueError, TypeError):
                pass
        return "string"
    if isinstance(value, datetime):
        return "datetime"
    if isinstance(value, ObjectId):
        return "objectid"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        if not value:
            return "array<empty>"
        inner = {_classify_type(v) for v in value[:20]}
        return f"array<{'|'.join(sorted(inner))}>"
    if isinstance(value, bytes):
        return "binary"
    return type(value).__name__


def _infer_schema(docs: list[dict]) -> dict:
    """A partir de uma amostra de documentos, infere o schema."""
    field_types: dict[str, Counter] = defaultdict(Counter)
    field_presence: Counter = Counter()
    for d in docs:
        for k, v in d.items():
            field_presence[k] += 1
            field_types[k][_classify_type(v)] += 1
    fields = {}
    total = len(docs) or 1
    for k, types_counter in field_types.items():
        fields[k] = {
            "types": dict(types_counter),
            "presence_pct": round(100.0 * field_presence[k] / total, 1),
        }
    return {"sample_size": len(docs), "fields": fields}


async def main():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    cli = AsyncIOMotorClient(mongo_url)
    db = cli[db_name]

    collection_names = sorted(await db.list_collection_names())

    dump = {
        "_meta": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "database": db_name,
            "source": "MongoDB",
            "format_version": "1.0",
            "collection_count": len(collection_names),
        },
        "collections": {},
    }
    schema = {
        "_meta": dict(dump["_meta"]),
        "collections": {},
    }

    grand_total = 0
    for name in collection_names:
        docs = await db[name].find({}, {"_id": 0}).to_list(None)
        serialized = [_serialize(d) for d in docs]
        dump["collections"][name] = serialized
        schema["collections"][name] = {
            "document_count": len(docs),
            **_infer_schema(docs),
        }
        grand_total += len(docs)
        print(f"  ✓ {name:50} {len(docs):>6} docs")

    dump["_meta"]["total_documents"] = grand_total
    schema["_meta"]["total_documents"] = grand_total

    with open(OUT_DUMP, "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=2, default=str)
    with open(OUT_SCHEMA, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n>>> Total: {grand_total} documentos em {len(collection_names)} collections")
    print(f">>> dump.json     : {OUT_DUMP.stat().st_size / 1024:,.1f} KB")
    print(f">>> schema.json   : {OUT_SCHEMA.stat().st_size / 1024:,.1f} KB")

    _write_manifest(schema)
    _write_sql_skeleton(schema)
    print(f">>> MANIFEST.md             gerado")
    print(f">>> migrate_to_supabase.sql gerado")


# ────────────────────────────────────────────────────────────────────
# Manifesto e SQL skeleton
# ────────────────────────────────────────────────────────────────────


def _mongo_type_to_pg(types_counter: dict) -> str:
    """Decide um tipo Postgres a partir do dict de tipos do schema."""
    types = set(types_counter.keys()) - {"null"}
    if not types:
        return "text"
    if types <= {"int"}:
        return "bigint"
    if types <= {"int", "float"}:
        return "numeric"
    if types <= {"bool"}:
        return "boolean"
    if types <= {"datetime", "datetime-string"}:
        return "timestamptz"
    if any(t.startswith("array") for t in types):
        return "jsonb"
    if "object" in types:
        return "jsonb"
    return "text"


def _write_sql_skeleton(schema: dict):
    lines = [
        "-- ============================================================",
        "-- DDL Postgres / Supabase gerado a partir do dump MongoDB",
        f"-- Gerado em: {datetime.now(timezone.utc).isoformat()}",
        "-- ============================================================",
        "",
        "-- Habilita a extensão para gerar UUIDs (caso não esteja)",
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
        "",
    ]
    for name, info in schema["collections"].items():
        if info["document_count"] == 0:
            lines.append(f"-- Tabela `{name}` (0 documentos) — schema inferido vazio, pulada.")
            lines.append("")
            continue
        lines.append(f"-- {name}: {info['document_count']} documentos")
        lines.append(f"CREATE TABLE IF NOT EXISTS {name} (")
        cols = []
        for field, fdata in info["fields"].items():
            pg_type = _mongo_type_to_pg(fdata["types"])
            null_ok = fdata["presence_pct"] < 100
            col_def = f'  "{field}" {pg_type}'
            if not null_ok:
                col_def += " NOT NULL"
            cols.append(col_def)
        lines.append(",\n".join(cols))
        lines.append(");")
        lines.append("")
    with open(OUT_SQL, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_manifest(schema: dict):
    lines = []
    lines.append("# Backup Completo do Banco de Dados — CRA Construtora")
    lines.append("")
    lines.append(f"**Gerado em:** {schema['_meta']['exported_at']}")
    lines.append(f"**Banco origem:** {schema['_meta']['database']} (MongoDB)")
    lines.append(f"**Total de collections:** {schema['_meta']['collection_count']}")
    lines.append(f"**Total de documentos:** {schema['_meta']['total_documents']}")
    lines.append("")
    lines.append("## 📦 Arquivos deste pacote")
    lines.append("")
    lines.append("| Arquivo | Descrição |")
    lines.append("|---------|-----------|")
    lines.append("| `dump.json` | Dump COMPLETO de todas as collections — todos os campos, todos os documentos. Tipos não-JSON estão envelopados (`{\"$date\": ...}` e `{\"$oid\": ...}`). |")
    lines.append("| `schema.json` | Schema inferido a partir do dump (tipos detectados + % de presença por campo). |")
    lines.append("| `migrate_to_supabase.sql` | DDL Postgres com `CREATE TABLE IF NOT EXISTS` para cada collection (esqueleto). |")
    lines.append("| `MANIFEST.md` | Este arquivo. |")
    lines.append("")
    lines.append("## 🧭 Como o Claude Code (ou você) deve ler `dump.json`")
    lines.append("")
    lines.append("```json")
    lines.append("{")
    lines.append('  "_meta": { "database": "...", "exported_at": "...", "collection_count": 65, "total_documents": 1340 },')
    lines.append('  "collections": {')
    lines.append('    "funcionarios": [ { "id": "...", "nome": "...", ... }, ... ],')
    lines.append('    "contas_pagar": [ ... ],')
    lines.append('    "nfe_importadas": [ ... ]')
    lines.append("  }")
    lines.append("}")
    lines.append("```")
    lines.append("")
    lines.append("### Convenções de tipos")
    lines.append("")
    lines.append("- **Datas**: strings ISO 8601 normais (`\"2026-02-25T19:41:25.665067+00:00\"`) ou envelopes `{\"$date\": \"...\"}` para `datetime` nativo do BSON.")
    lines.append("- **ObjectId**: objetos `{\"$oid\": \"507f1f77bcf86cd799439011\"}`. NA MAIORIA das collections o `_id` foi removido e usamos a chave `id` (UUID v4 em string) — Supabase pode usar `id` como PK.")
    lines.append("- **Binary**: `{\"$binary\": \"<base64>\"}` (raro, só em alguns artefatos).")
    lines.append("- **Arrays / objetos aninhados**: preservados como JSON puro → mapear para `jsonb` no Postgres.")
    lines.append("")
    lines.append("## 🚀 Instruções para o Claude Code converter para Supabase")
    lines.append("")
    lines.append("**Prompt sugerido para colar no Claude Code:**")
    lines.append("")
    lines.append("> Você é um especialista em migração MongoDB → Supabase Postgres.")
    lines.append("> Em anexo está o `dump.json` com 65 collections (~1340 docs) do nosso ERP CRA")
    lines.append("> Construtora. Use `MANIFEST.md` e `schema.json` como referência de tipos.")
    lines.append(">")
    lines.append("> Faça:")
    lines.append("> 1. Crie as tabelas no Supabase (use `migrate_to_supabase.sql` como ponto")
    lines.append(">    de partida e refine os tipos olhando o `schema.json`).")
    lines.append("> 2. Para cada collection do dump, gere um script Python (idempotente)")
    lines.append(">    que insere os documentos via `supabase-py` ou direto via `psycopg`.")
    lines.append("> 3. Trate campos aninhados como `jsonb`.")
    lines.append("> 4. Use `id` (UUID em string) como PRIMARY KEY quando existir.")
    lines.append("> 5. Habilite Row Level Security depois (não no setup inicial).")
    lines.append("> 6. Crie índices para os campos mais usados: `created_at`, `status`,")
    lines.append(">    `funcionario_id`, `entity_type`, `entity_id`, `cnpj_emitente`.")
    lines.append(">")
    lines.append("> Documentos importantes do domínio:")
    lines.append("> - `users`: contas de acesso. Hash bcrypt em `password_hash`.")
    lines.append("> - `funcionarios`: cadastro de colaboradores (RH).")
    lines.append("> - `contas_pagar` / `contas_receber`: financeiro com `anexos[]`.")
    lines.append("> - `attachments`: tabela mestre de anexos por entidade.")
    lines.append("> - `nfe_importadas` / `nfse_importadas`: notas fiscais importadas.")
    lines.append("> - `chat_*`: histórico do chatbot IA e PDFs gerados.")
    lines.append("> - `tasks`: caixa de tarefas inter-sistemas.")
    lines.append(">")
    lines.append("> Entregue: 1) DDL final completo, 2) script de import Python, 3) lista")
    lines.append("> de índices recomendados, 4) checklist de validação pós-migração.")
    lines.append("")
    lines.append("## 📊 Inventário de Collections")
    lines.append("")
    lines.append("| Collection | Docs | Domínio |")
    lines.append("|------------|-----:|---------|")
    domain_map = _domain_map()
    for name, info in schema["collections"].items():
        domain = domain_map.get(name, "—")
        lines.append(f"| `{name}` | {info['document_count']} | {domain} |")
    lines.append("")
    lines.append("## 🔗 Relacionamentos importantes")
    lines.append("")
    lines.append("- `attachments.entity_id` → referencia o `id` de **muitas** collections (campo `entity_type` indica qual). Polimórfico.")
    lines.append("- `contas_pagar.fornecedor_id` → `cadastros.id` (categoria=fornecedor).")
    lines.append("- `contas_receber.cliente_id` → `cadastros.id` (categoria=cliente).")
    lines.append("- `ordens_servico.cliente_id` → `cadastros.id`.")
    lines.append("- `folha_pagamento.funcionario_id` → `funcionarios.id`.")
    lines.append("- `ferias.funcionario_id`, `ponto_registros.funcionario_id`, `epi_fichas.funcionario_id` → `funcionarios.id`.")
    lines.append("- `chat_messages.conversation_id` → `chat_conversations.id`.")
    lines.append("- `nfe_importadas.certificado_id` → `nfe_certificados.id`.")
    lines.append("- `notas_emitidas.cliente_id` → `cadastros.id`.")
    lines.append("- `solicitacoes_folha_financeiro.folha_id` → `folhas_importadas.id`.")
    lines.append("- `tasks.target_system` ∈ { `rh`, `administrativo`, `gerenciamento` }.")
    lines.append("")
    lines.append("## ⚠️ Pontos de atenção na migração")
    lines.append("")
    lines.append("1. **Senhas (`users.password_hash`)**: já vêm com bcrypt — preserve a string como `text`. Não rehash.")
    lines.append("2. **Datas em string vs datetime BSON**: o mesmo campo pode aparecer dos dois jeitos em documentos diferentes (legado). Trate como `timestamptz` aceitando os dois formatos no parser.")
    lines.append("3. **Arrays de IDs como `parcelas_ids`, `contas_pagar_ids`**: mapeie para `text[]` ou `jsonb`.")
    lines.append("4. **Campos com `null` ou ausentes** em até 60% dos documentos: NÃO use NOT NULL (o DDL gerado já considera isso).")
    lines.append("5. **`chat_artifacts.content_b64`**: PDFs em base64. Pode crescer — considere migrar para Supabase Storage e guardar só a URL.")
    lines.append("6. **`audit_logs` (763 docs)**: log enorme; considere migrar para tabela particionada por mês.")
    lines.append("7. **`nfe_importadas.xml_base64`**: XML completo da NF-e em base64; idem ao item 5.")
    lines.append("")
    lines.append("## ✅ Checklist pós-migração")
    lines.append("")
    lines.append("- [ ] Contagem de linhas por tabela bate com `schema.json[collection].document_count`.")
    lines.append("- [ ] `users` migrados: confirmar login com bcrypt original.")
    lines.append("- [ ] `funcionarios` migrados: cada `id` único, sem duplicidade.")
    lines.append("- [ ] FKs polimórficas (`attachments`): teste consultar anexos por `entity_type`.")
    lines.append("- [ ] Índices criados em `created_at`, `status`, `funcionario_id`, `entity_type+entity_id`.")
    lines.append("- [ ] Backup do Supabase ativado.")
    lines.append("")
    with open(OUT_MANIFEST, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _domain_map() -> dict:
    return {
        # Sistema base
        "users": "Auth/Sistema",
        "audit_logs": "Auditoria",
        "usage_logs": "Auditoria",
        "notifications": "Sistema",
        "notificacoes_dispensadas": "Sistema",
        "tasks": "Sistema (Caixa de Tarefas)",
        "counters": "Sistema",
        "categories": "Sistema",
        "subcategories": "Sistema",
        "folder_passwords": "Armazenamento",
        "storage_trash": "Armazenamento",
        "attachments": "Anexos (polimórfico)",
        # Financeiro
        "contas_pagar": "Financeiro",
        "contas_receber": "Financeiro",
        "movimentacoes_contas": "Financeiro",
        "contas_bancarias": "Financeiro",
        "extratos_bancarios": "Financeiro",
        "conciliacoes": "Financeiro",
        "formas_pagamento": "Financeiro",
        "plano_contas": "Financeiro",
        "centros_custo": "Financeiro",
        "cadastros": "Financeiro (Clientes/Fornecedores)",
        "alugueis": "Financeiro/Frota",
        "imoveis": "Financeiro/Imóveis",
        "produtos_admin": "Financeiro",
        "notas_emitidas": "Financeiro/NFS-e Emissão",
        "nfe_certificados": "Financeiro/NF-e",
        "nfe_importadas": "Financeiro/NF-e",
        "nfse_importadas": "Financeiro/NFS-e",
        "logs_importacao": "Financeiro",
        "ordens_servico": "Financeiro/OS",
        # RH
        "funcionarios": "RH",
        "folha_pagamento": "RH",
        "folhas_importadas": "RH",
        "solicitacoes_folha": "RH",
        "solicitacoes_folha_financeiro": "RH↔Financeiro",
        "ferias": "RH",
        "ferias_alertas_dispensados": "RH",
        "ponto_registros": "RH (Ponto)",
        "ponto_abonos": "RH (Ponto)",
        "ponto_observacoes": "RH (Ponto)",
        "banco_horas_ajustes": "RH",
        "jornadas_trabalho": "RH",
        "epi_cargos": "RH (EPI)",
        "epi_fichas": "RH (EPI)",
        "custos_rh_config": "RH",
        "rh_notificacoes": "RH",
        # Frota/Gerenciamento
        "machines": "Frota",
        "fleets": "Frota",
        "subfleets": "Frota",
        "maintenances": "Frota (Manutenção)",
        "combustivel": "Frota",
        "horimetro": "Frota",
        "veiculos_abastecedores": "Frota",
        "obras": "Frota/Obras",
        # Estoque
        "stock_items": "Estoque",
        "stock_categories": "Estoque",
        "stock_subcategories": "Estoque",
        "stock_movements": "Estoque",
        "produtos": "Estoque",
        "fornecedores": "Cadastros",
        # Chat IA
        "chat_conversations": "Chat IA",
        "chat_messages": "Chat IA",
        "chat_artifacts": "Chat IA (PDFs gerados)",
        "chat_knowledge_base": "Chat IA (PCMSO/PGR/LTCAT/CCT)",
    }


if __name__ == "__main__":
    asyncio.run(main())
