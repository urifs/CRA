# Backup do Banco de Dados — CRA Construtora

> Pasta `/database_export/` contém o **dump COMPLETO** (1340 documentos / 65 collections) do MongoDB de produção do ERP CRA, junto de instruções e DDL para migrar para Supabase Postgres.

## 🚀 Como usar

### Opção 1 — Baixar o ZIP (recomendado)
1. Abra `database_export/backup_cra_construtora.zip` no GitHub.
2. Clique em **"Download raw"** (ícone de download no topo direito).
3. Descompacte localmente.
4. Cole os arquivos `dump.json`, `schema.json`, `MANIFEST.md`, `migrate_to_supabase.sql` no Claude Code.

### Opção 2 — Baixar arquivos individuais
Cada arquivo da pasta pode ser baixado direto via "Download raw" no GitHub:
- `dump.json` (~4.4 MB) — backup completo
- `schema.json` (~116 KB) — schema inferido
- `MANIFEST.md` (~8 KB) — instruções e prompt para o Claude Code
- `migrate_to_supabase.sql` (~30 KB) — DDL Postgres esqueleto

## 📋 Prompt sugerido para colar no Claude Code

```
Você é um especialista em migração MongoDB → Supabase Postgres.

Anexei 4 arquivos do ERP CRA Construtora:
- dump.json: 65 collections, 1340 documentos
- schema.json: tipos inferidos por campo
- migrate_to_supabase.sql: DDL esqueleto
- MANIFEST.md: instruções detalhadas

Por favor:
1. Refine o DDL com base no schema.json (escolha tipos finais e PK).
2. Gere script Python idempotente que insere todos os documentos no Supabase
   usando supabase-py (ou psycopg).
3. Trate datas (formato ISO + envelope $date), ObjectIds ($oid), arrays/objetos
   aninhados (vai para jsonb), e campos opcionais.
4. Use `id` (UUID string) como PRIMARY KEY quando existir.
5. Sugira índices para os campos mais consultados.
6. Entregue um checklist de validação pós-migração.

Leia o MANIFEST.md antes para entender domínio e relacionamentos.
```

## 🔄 Como regerar o backup mais tarde

Sempre que precisar de um backup atualizado, basta rodar:

```bash
cd /app/backend && source .env && cd ../database_export
python3 export_mongodb.py
```

O script reescreve `dump.json`, `schema.json`, `MANIFEST.md`, `migrate_to_supabase.sql` com os dados mais recentes.

## ⚠️ Atenção

- O `dump.json` contém **dados reais** (incluindo hashes bcrypt de senhas em `users.password`). Trate como sensível — não publique em repositório público.
- Senhas estão hasheadas com bcrypt; não precisa rehashear durante a migração, apenas preserve a string.
- Para PDFs/XML grandes em base64 (`chat_artifacts.content_b64`, `nfe_importadas.xml_base64`), considere migrar para Supabase Storage e guardar só URL.
