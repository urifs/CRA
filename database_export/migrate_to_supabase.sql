-- ============================================================
-- DDL Postgres / Supabase gerado a partir do dump MongoDB
-- Gerado em: 2026-05-14T18:38:24.735003+00:00
-- ============================================================

-- Habilita a extensão para gerar UUIDs (caso não esteja)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- alugueis: 1 documentos
CREATE TABLE IF NOT EXISTS alugueis (
  "id" text NOT NULL,
  "numero" bigint NOT NULL,
  "maquina_id" text NOT NULL,
  "maquina_nome" text NOT NULL,
  "maquina_placa" text NOT NULL,
  "cliente_nome" text NOT NULL,
  "cliente_telefone" text NOT NULL,
  "cliente_documento" text NOT NULL,
  "numero_contrato" text NOT NULL,
  "tipo_periodo" text NOT NULL,
  "periodo_especificado" text NOT NULL,
  "data_entrega" text NOT NULL,
  "data_vencimento" text NOT NULL,
  "data_devolucao" text NOT NULL,
  "valor" numeric NOT NULL,
  "valor_caucao" numeric NOT NULL,
  "local_entrega" text NOT NULL,
  "status" text NOT NULL,
  "observacoes" text NOT NULL,
  "conta_receber_id" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- attachments: 3 documentos
CREATE TABLE IF NOT EXISTS attachments (
  "id" text NOT NULL,
  "filename" text NOT NULL,
  "stored_filename" text NOT NULL,
  "file_type" text NOT NULL,
  "file_size" bigint NOT NULL,
  "entity_type" text NOT NULL,
  "entity_id" text NOT NULL,
  "uploaded_by" text NOT NULL,
  "uploaded_by_name" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- audit_logs: 763 documentos
CREATE TABLE IF NOT EXISTS audit_logs (
  "id" text NOT NULL,
  "user_id" text NOT NULL,
  "user_name" text NOT NULL,
  "user_email" text,
  "action" text NOT NULL,
  "entity_type" text,
  "entity_id" text,
  "entity_name" text,
  "details" text NOT NULL,
  "created_at" timestamptz,
  "module" text,
  "user_role" text,
  "timestamp" timestamptz
);

-- Tabela `banco_horas_ajustes` (0 documentos) — schema inferido vazio, pulada.

-- cadastros: 8 documentos
CREATE TABLE IF NOT EXISTS cadastros (
  "id" text NOT NULL,
  "codigo" bigint,
  "tipo_cadastro" text,
  "tipo_pessoa" text,
  "status" text,
  "nome_razao" text NOT NULL,
  "apelido_fantasia" text,
  "cpf_cnpj" text NOT NULL,
  "rg_ie" text,
  "telefone" text NOT NULL,
  "celular" text,
  "email" text NOT NULL,
  "cep" text NOT NULL,
  "endereco" text NOT NULL,
  "numero" text,
  "complemento" text,
  "bairro" text,
  "cidade" text NOT NULL,
  "uf" text,
  "grupo" text,
  "rota" text,
  "vendedor" text,
  "limite_credito" text,
  "observacoes" text NOT NULL,
  "created_by" text,
  "created_at" timestamptz NOT NULL,
  "tipo" text,
  "estado" text
);

-- categories: 6 documentos
CREATE TABLE IF NOT EXISTS categories (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "description" text NOT NULL,
  "user_id" text,
  "created_at" timestamptz NOT NULL,
  "color" text,
  "created_by" text
);

-- centros_custo: 1 documentos
CREATE TABLE IF NOT EXISTS centros_custo (
  "id" text NOT NULL,
  "codigo" text NOT NULL,
  "nome" text NOT NULL,
  "descricao" text NOT NULL,
  "status" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- chat_artifacts: 13 documentos
CREATE TABLE IF NOT EXISTS chat_artifacts (
  "id" text NOT NULL,
  "user_id" text,
  "filename" text NOT NULL,
  "content_type" text,
  "content_b64" text,
  "created_at" timestamptz NOT NULL,
  "conversation_id" text,
  "path" text,
  "mime" text
);

-- chat_conversations: 18 documentos
CREATE TABLE IF NOT EXISTS chat_conversations (
  "id" text NOT NULL,
  "user_id" text NOT NULL,
  "title" text NOT NULL,
  "module" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "updated_at" timestamptz NOT NULL,
  "last_message_preview" text NOT NULL
);

-- chat_knowledge_base: 4 documentos
CREATE TABLE IF NOT EXISTS chat_knowledge_base (
  "id" text NOT NULL,
  "category" text NOT NULL,
  "name" text NOT NULL,
  "title" text NOT NULL,
  "extracted_text" text NOT NULL,
  "pdf_path" text NOT NULL,
  "pdf_size" bigint NOT NULL,
  "pages" bigint NOT NULL,
  "created_at" timestamptz NOT NULL,
  "uploaded_by" text NOT NULL
);

-- chat_messages: 54 documentos
CREATE TABLE IF NOT EXISTS chat_messages (
  "id" text NOT NULL,
  "conversation_id" text NOT NULL,
  "role" text NOT NULL,
  "content" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "artifact" jsonb,
  "attachments" jsonb
);

-- combustivel: 7 documentos
CREATE TABLE IF NOT EXISTS combustivel (
  "id" text NOT NULL,
  "machine_id" text NOT NULL,
  "data" text NOT NULL,
  "tipo_medicao" text NOT NULL,
  "hora_km_inicial" numeric NOT NULL,
  "litros_inicial" numeric,
  "litros_final" numeric,
  "litros_consumidos" numeric,
  "operador" text,
  "observacoes" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "tipo_registro" text,
  "litros_diesel" numeric,
  "litros_oleo" numeric,
  "litros_graxa" numeric,
  "fonte_abastecimento" text,
  "veiculo_abastecedor_id" text,
  "operador_id" text
);

-- conciliacoes: 2 documentos
CREATE TABLE IF NOT EXISTS conciliacoes (
  "id" text NOT NULL,
  "extrato_ids" jsonb NOT NULL,
  "contas_ids" jsonb NOT NULL,
  "contas_tipos" jsonb NOT NULL,
  "extratos_descricao" jsonb NOT NULL,
  "contas_descricao" jsonb NOT NULL,
  "valor_extratos" numeric NOT NULL,
  "valor_contas" numeric NOT NULL,
  "diferenca" bigint NOT NULL,
  "data_conciliacao" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "created_by" text NOT NULL
);

-- contas_bancarias: 2 documentos
CREATE TABLE IF NOT EXISTS contas_bancarias (
  "id" text NOT NULL,
  "nome" text NOT NULL,
  "banco" text NOT NULL,
  "codigo_banco" text NOT NULL,
  "agencia" text NOT NULL,
  "agencia_digito" text NOT NULL,
  "conta" text NOT NULL,
  "conta_digito" text NOT NULL,
  "tipo_conta" text NOT NULL,
  "titular" text NOT NULL,
  "cpf_cnpj_titular" text NOT NULL,
  "chave_pix" text NOT NULL,
  "tipo_chave_pix" text NOT NULL,
  "saldo_inicial" numeric NOT NULL,
  "saldo_atual" numeric NOT NULL,
  "ativo" boolean NOT NULL,
  "cor" text NOT NULL,
  "observacoes" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "updated_at" timestamptz
);

-- contas_pagar: 39 documentos
CREATE TABLE IF NOT EXISTS contas_pagar (
  "id" text NOT NULL,
  "numero" bigint,
  "fornecedor_id" text,
  "fornecedor_nome" text,
  "documento" text,
  "numero_doc" text,
  "descricao" text NOT NULL,
  "valor" numeric NOT NULL,
  "valor_desconto" numeric,
  "valor_juros" numeric,
  "valor_multa" numeric,
  "data_emissao" text,
  "data_vencimento" text NOT NULL,
  "data_pagamento" text,
  "data_cancelamento" text,
  "plano_conta_id" text,
  "plano_conta_nome" text,
  "centro_custo" text,
  "forma_pagamento" text,
  "conta_movimento" text,
  "status" text NOT NULL,
  "observacoes" text,
  "valor_final" numeric,
  "created_by" text,
  "created_at" timestamptz NOT NULL,
  "conciliado" boolean,
  "anexos" jsonb,
  "frota_id" text,
  "frota_nome" text,
  "categoria" text,
  "tipo" text,
  "origem" text,
  "conta_bancaria_id" text,
  "data_ultimo_pagamento" text,
  "pagamentos" jsonb,
  "saldo_restante" numeric,
  "valor_pago" numeric,
  "total_parcelas" bigint,
  "numero_parcela" bigint,
  "parcela_origem_id" text,
  "subconta_id" text,
  "subconta_nome" text,
  "conta_bancaria_nome" text,
  "updated_at" timestamptz,
  "maquina_id" text,
  "maquina_nome" text,
  "valor_retencao" numeric
);

-- contas_receber: 16 documentos
CREATE TABLE IF NOT EXISTS contas_receber (
  "id" text NOT NULL,
  "descricao" text NOT NULL,
  "cliente_nome" text NOT NULL,
  "cliente_documento" text,
  "valor" numeric NOT NULL,
  "valor_final" numeric NOT NULL,
  "data_vencimento" text NOT NULL,
  "status" text NOT NULL,
  "origem" text,
  "imovel_id" text,
  "created_at" timestamptz NOT NULL,
  "created_by" text NOT NULL,
  "data_recebimento" text,
  "data_ultimo_recebimento" text,
  "recebimentos" jsonb,
  "saldo_restante" numeric,
  "valor_recebido" numeric,
  "numero" bigint,
  "cliente_id" text,
  "documento" text,
  "numero_doc" text,
  "valor_desconto" bigint,
  "valor_juros" bigint,
  "valor_multa" bigint,
  "data_emissao" text,
  "data_cancelamento" text,
  "plano_conta_id" text,
  "plano_conta_nome" text,
  "centro_custo" text,
  "frota_id" text,
  "frota_nome" text,
  "forma_pagamento" text,
  "conta_movimento" text,
  "faturamento" text,
  "observacoes" text,
  "conta_bancaria_id" text,
  "aluguel_id" text,
  "total_parcelas" bigint,
  "numero_parcela" bigint,
  "parcela_origem_id" text,
  "subconta_id" text,
  "subconta_nome" text,
  "conta_bancaria_nome" text,
  "anexos" jsonb,
  "updated_at" timestamptz,
  "maquina_id" text,
  "maquina_nome" text,
  "valor_retencao" numeric
);

-- counters: 6 documentos
CREATE TABLE IF NOT EXISTS counters (
  "seq" bigint NOT NULL
);

-- custos_rh_config: 1 documentos
CREATE TABLE IF NOT EXISTS custos_rh_config (
  "id" text NOT NULL,
  "fgts_aliquota" numeric NOT NULL,
  "inss_patronal_aliquota" numeric NOT NULL,
  "vale_transporte" numeric NOT NULL,
  "vale_alimentacao" numeric NOT NULL,
  "plano_saude" numeric NOT NULL,
  "outros_beneficios" numeric NOT NULL,
  "epis_custo_mensal" numeric NOT NULL,
  "horas_mes" bigint NOT NULL,
  "updated_at" timestamptz NOT NULL,
  "custos_extras" jsonb NOT NULL,
  "vale_transporte_funcionario_ids" jsonb NOT NULL
);

-- epi_cargos: 1 documentos
CREATE TABLE IF NOT EXISTS epi_cargos (
  "id" text NOT NULL,
  "nome" text NOT NULL
);

-- epi_fichas: 1 documentos
CREATE TABLE IF NOT EXISTS epi_fichas (
  "funcionario_id" text NOT NULL,
  "cargo" text NOT NULL,
  "codigo_cbo" text NOT NULL,
  "ocupacao_cbo" text NOT NULL,
  "data_entrega" text NOT NULL,
  "epis" jsonb NOT NULL,
  "observacoes" text NOT NULL,
  "id" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- extratos_bancarios: 2 documentos
CREATE TABLE IF NOT EXISTS extratos_bancarios (
  "id" text NOT NULL,
  "data" text NOT NULL,
  "descricao" text NOT NULL,
  "valor" numeric NOT NULL,
  "tipo" text NOT NULL,
  "conta_bancaria_id" text NOT NULL,
  "conciliado" boolean NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- Tabela `ferias` (0 documentos) — schema inferido vazio, pulada.

-- Tabela `ferias_alertas_dispensados` (0 documentos) — schema inferido vazio, pulada.

-- fleets: 2 documentos
CREATE TABLE IF NOT EXISTS fleets (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "description" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- folder_passwords: 3 documentos
CREATE TABLE IF NOT EXISTS folder_passwords (
  "path" text NOT NULL,
  "password_hash" text NOT NULL,
  "updated_at" timestamptz NOT NULL,
  "updated_by" text NOT NULL
);

-- folha_pagamento: 1 documentos
CREATE TABLE IF NOT EXISTS folha_pagamento (
  "funcionario_id" text NOT NULL,
  "mes" bigint NOT NULL,
  "ano" bigint NOT NULL,
  "salario_base" numeric NOT NULL,
  "horas_extras" numeric NOT NULL,
  "valor_hora_extra" numeric NOT NULL,
  "adicional_noturno" numeric NOT NULL,
  "comissoes" numeric NOT NULL,
  "vale_transporte" numeric NOT NULL,
  "vale_alimentacao" numeric NOT NULL,
  "plano_saude" numeric NOT NULL,
  "outros_descontos" numeric NOT NULL,
  "observacoes" text NOT NULL,
  "salario_bruto" numeric NOT NULL,
  "inss" numeric NOT NULL,
  "irpf" numeric NOT NULL,
  "fgts" numeric NOT NULL,
  "total_descontos" numeric NOT NULL,
  "salario_liquido" numeric NOT NULL,
  "id" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- Tabela `folhas_importadas` (0 documentos) — schema inferido vazio, pulada.

-- formas_pagamento: 1 documentos
CREATE TABLE IF NOT EXISTS formas_pagamento (
  "id" text NOT NULL,
  "codigo" text NOT NULL,
  "nome" text NOT NULL,
  "tipo" text NOT NULL,
  "taxa" numeric NOT NULL,
  "prazo_recebimento" bigint NOT NULL,
  "conta_bancaria" text NOT NULL,
  "ativo" boolean NOT NULL,
  "observacoes" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- Tabela `fornecedores` (0 documentos) — schema inferido vazio, pulada.

-- funcionarios: 9 documentos
CREATE TABLE IF NOT EXISTS funcionarios (
  "nome" text NOT NULL,
  "cpf" text NOT NULL,
  "rg" text NOT NULL,
  "data_nascimento" text NOT NULL,
  "telefone" text NOT NULL,
  "celular" text NOT NULL,
  "email" text NOT NULL,
  "cep" text NOT NULL,
  "endereco" text NOT NULL,
  "numero" text NOT NULL,
  "complemento" text NOT NULL,
  "bairro" text NOT NULL,
  "cidade" text NOT NULL,
  "uf" text NOT NULL,
  "cargo" text NOT NULL,
  "funcao" text NOT NULL,
  "departamento" text NOT NULL,
  "salario" numeric NOT NULL,
  "data_admissao" text NOT NULL,
  "regime_contratacao" text NOT NULL,
  "status" text NOT NULL,
  "observacoes" text NOT NULL,
  "id" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "anexos" jsonb NOT NULL
);

-- horimetro: 1 documentos
CREATE TABLE IF NOT EXISTS horimetro (
  "id" text NOT NULL,
  "machine_id" text NOT NULL,
  "data" text NOT NULL,
  "hora_inicial" numeric NOT NULL,
  "hora_final" numeric NOT NULL,
  "horas_trabalhadas" numeric NOT NULL,
  "operador" text NOT NULL,
  "observacoes" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- imoveis: 1 documentos
CREATE TABLE IF NOT EXISTS imoveis (
  "tipo_imovel" text NOT NULL,
  "descricao" text NOT NULL,
  "endereco" text NOT NULL,
  "numero" text NOT NULL,
  "complemento" text NOT NULL,
  "bairro" text NOT NULL,
  "cidade" text NOT NULL,
  "estado" text NOT NULL,
  "cep" text NOT NULL,
  "area_m2" numeric NOT NULL,
  "quartos" bigint NOT NULL,
  "banheiros" bigint NOT NULL,
  "vagas_garagem" bigint NOT NULL,
  "cliente_nome" text NOT NULL,
  "cliente_telefone" text NOT NULL,
  "cliente_documento" text NOT NULL,
  "numero_contrato" text NOT NULL,
  "tipo_periodo" text NOT NULL,
  "periodo_especificado" text NOT NULL,
  "data_inicio" text NOT NULL,
  "data_vencimento" text NOT NULL,
  "valor_aluguel" numeric NOT NULL,
  "valor_condominio" numeric NOT NULL,
  "valor_iptu" bigint NOT NULL,
  "valor_caucao" bigint NOT NULL,
  "dia_vencimento" bigint NOT NULL,
  "observacoes" text NOT NULL,
  "gerar_conta_receber" boolean NOT NULL,
  "id" text NOT NULL,
  "status" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "created_by" text NOT NULL,
  "conta_receber_id" text NOT NULL
);

-- jornadas_trabalho: 2 documentos
CREATE TABLE IF NOT EXISTS jornadas_trabalho (
  "id" text NOT NULL,
  "nome" text NOT NULL,
  "descricao" text NOT NULL,
  "is_padrao" boolean NOT NULL,
  "dias" jsonb NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- logs_importacao: 3 documentos
CREATE TABLE IF NOT EXISTS logs_importacao (
  "id" text NOT NULL,
  "tipo" text NOT NULL,
  "data_hora" timestamptz NOT NULL,
  "total_certificados" bigint NOT NULL,
  "nfe_importadas" bigint NOT NULL,
  "nfse_importadas" bigint NOT NULL,
  "erros" jsonb NOT NULL,
  "status" text NOT NULL
);

-- machines: 6 documentos
CREATE TABLE IF NOT EXISTS machines (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "plate" text NOT NULL,
  "category_id" text NOT NULL,
  "brand" text NOT NULL,
  "model" text NOT NULL,
  "year" bigint NOT NULL,
  "notes" text NOT NULL,
  "status" text NOT NULL,
  "user_id" text,
  "created_at" timestamptz NOT NULL,
  "obra_id" text,
  "hours_since_oil_change" numeric,
  "last_oil_change_date" text,
  "horimetro_atual" numeric,
  "fleet_id" text,
  "identificador_numero" text,
  "identificador_tipo" text,
  "operator_id" text,
  "subcategory_id" text,
  "subfleet_id" text,
  "created_by" text
);

-- maintenances: 6 documentos
CREATE TABLE IF NOT EXISTS maintenances (
  "id" text NOT NULL,
  "machine_id" text NOT NULL,
  "part_name" text NOT NULL,
  "replacement_date" text NOT NULL,
  "part_value" numeric NOT NULL,
  "maintenance_type" text NOT NULL,
  "description" text NOT NULL,
  "photos" jsonb NOT NULL,
  "user_id" text,
  "created_at" timestamptz NOT NULL,
  "is_oil_change" boolean,
  "created_by" text
);

-- movimentacoes_contas: 1 documentos
CREATE TABLE IF NOT EXISTS movimentacoes_contas (
  "id" text NOT NULL,
  "numero" bigint NOT NULL,
  "tipo" text NOT NULL,
  "descricao" text NOT NULL,
  "valor" numeric NOT NULL,
  "data_movimentacao" text NOT NULL,
  "conta_bancaria_origem_id" text NOT NULL,
  "conta_bancaria_origem_nome" text NOT NULL,
  "centro_custo_origem_id" text NOT NULL,
  "centro_custo_origem_nome" text NOT NULL,
  "conta_bancaria_destino_id" text NOT NULL,
  "conta_bancaria_destino_nome" text NOT NULL,
  "centro_custo_destino_id" text NOT NULL,
  "centro_custo_destino_nome" text NOT NULL,
  "categoria" text NOT NULL,
  "documento_referencia" text NOT NULL,
  "observacoes" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- nfe_certificados: 1 documentos
CREATE TABLE IF NOT EXISTS nfe_certificados (
  "id" text NOT NULL,
  "cnpj" text NOT NULL,
  "razao_social" text NOT NULL,
  "uf" text NOT NULL,
  "ambiente" text NOT NULL,
  "certificado_base64" text NOT NULL,
  "senha_certificado" text NOT NULL,
  "ativo" boolean NOT NULL,
  "ultimo_nsu" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "updated_at" timestamptz NOT NULL,
  "consultas_hoje" bigint NOT NULL,
  "data_consultas" text NOT NULL,
  "ultima_consulta_auto" timestamptz NOT NULL,
  "inscricao_municipal" text NOT NULL,
  "url_nfse" text NOT NULL,
  "soapaction_nfse" text NOT NULL,
  "bloqueado_ate" timestamptz NOT NULL
);

-- nfe_importadas: 155 documentos
CREATE TABLE IF NOT EXISTS nfe_importadas (
  "id" text NOT NULL,
  "certificado_id" text,
  "chave_acesso" text NOT NULL,
  "numero_nf" text,
  "serie" text NOT NULL,
  "data_emissao" text NOT NULL,
  "valor_total" numeric NOT NULL,
  "cnpj_emitente" text NOT NULL,
  "razao_social_emitente" text NOT NULL,
  "status" text NOT NULL,
  "xml_base64" text NOT NULL,
  "itens" jsonb NOT NULL,
  "created_at" timestamptz NOT NULL,
  "cnpj_destinatario" text,
  "nsu" text,
  "conta_pagar_id" text,
  "numero_nota" text,
  "uf_emitente" text,
  "razao_social_destinatario" text,
  "valor_produtos" numeric,
  "valor_servicos" text,
  "valor_frete" bigint,
  "valor_desconto" bigint,
  "centro_custo_id" text,
  "centro_custo_nome" text,
  "plano_conta_id" text,
  "plano_conta_nome" text,
  "pdf_base64" text,
  "observacoes" text,
  "importacao_manual" boolean,
  "created_by" text
);

-- nfse_importadas: 3 documentos
CREATE TABLE IF NOT EXISTS nfse_importadas (
  "id" text NOT NULL,
  "numero_nfse" text NOT NULL,
  "serie" text NOT NULL,
  "data_emissao" timestamptz NOT NULL,
  "valor_servico" numeric NOT NULL,
  "valor_total" numeric NOT NULL,
  "prestador_nome" text NOT NULL,
  "prestador_cnpj" text NOT NULL,
  "razao_social_prestador" text NOT NULL,
  "cnpj_prestador" text NOT NULL,
  "tomador_nome" text NOT NULL,
  "tomador_cnpj" text NOT NULL,
  "descricao_servico" text NOT NULL,
  "discriminacao" text NOT NULL,
  "status" text NOT NULL,
  "xml_base64" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- notas_emitidas: 2 documentos
CREATE TABLE IF NOT EXISTS notas_emitidas (
  "id" text NOT NULL,
  "tipo" text NOT NULL,
  "certificado_id" text NOT NULL,
  "cnpj_emitente" text NOT NULL,
  "razao_social_emitente" text NOT NULL,
  "uf_emitente" text NOT NULL,
  "ambiente" text NOT NULL,
  "numero" text NOT NULL,
  "serie" text NOT NULL,
  "chave_acesso" text,
  "protocolo" text NOT NULL,
  "status" text NOT NULL,
  "mensagem" text NOT NULL,
  "dest_cpf_cnpj" text,
  "dest_razao_social" text,
  "dest_ie" text,
  "dest_email" text,
  "dest_telefone" text,
  "dest_endereco" jsonb,
  "natureza_operacao" text,
  "tipo_operacao" text,
  "finalidade" text,
  "consumidor_final" text,
  "presenca_comprador" text,
  "forma_pagamento" text,
  "valor_pagamento" numeric,
  "modalidade_frete" text,
  "transportador_cnpj" text,
  "transportador_razao" text,
  "itens" jsonb NOT NULL,
  "valor_produtos" numeric,
  "valor_frete" numeric,
  "valor_seguro" numeric,
  "valor_desconto" numeric,
  "valor_outros" numeric,
  "valor_total" numeric NOT NULL,
  "info_complementar" text NOT NULL,
  "xml_base64" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "updated_at" text NOT NULL,
  "numero_nfse" text,
  "codigo_verificacao" text,
  "tomador_cpf_cnpj" text,
  "tomador_razao_social" text,
  "tomador_ie" text,
  "tomador_im" text,
  "tomador_email" text,
  "tomador_telefone" text,
  "tomador_endereco" jsonb,
  "codigo_cnae" text,
  "codigo_tributario_municipio" text,
  "item_lista_servico" text,
  "discriminacao" text,
  "valor_servicos" numeric,
  "valor_deducoes" numeric,
  "valor_pis" numeric,
  "valor_cofins" numeric,
  "valor_inss" numeric,
  "valor_ir" numeric,
  "valor_csll" numeric,
  "outras_retencoes" numeric,
  "valor_iss" numeric,
  "aliquota_iss" numeric,
  "valor_liquido" numeric,
  "iss_retido" boolean
);

-- Tabela `notificacoes_dispensadas` (0 documentos) — schema inferido vazio, pulada.

-- notifications: 3 documentos
CREATE TABLE IF NOT EXISTS notifications (
  "id" text NOT NULL,
  "user_id" text NOT NULL,
  "title" text NOT NULL,
  "message" text NOT NULL,
  "type" text NOT NULL,
  "read" boolean NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- obras: 2 documentos
CREATE TABLE IF NOT EXISTS obras (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "description" text NOT NULL,
  "location" text NOT NULL,
  "start_date" text NOT NULL,
  "end_date" text NOT NULL,
  "status" text NOT NULL,
  "user_id" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- ordens_servico: 8 documentos
CREATE TABLE IF NOT EXISTS ordens_servico (
  "id" text NOT NULL,
  "numero" bigint NOT NULL,
  "numero_contrato" text NOT NULL,
  "numero_documento_fiscal" text NOT NULL,
  "cliente_id" text NOT NULL,
  "cliente_nome" text NOT NULL,
  "cliente_fantasia" text NOT NULL,
  "cliente_documento" text NOT NULL,
  "cliente_email" text NOT NULL,
  "cliente_telefone" text NOT NULL,
  "cliente_celular" text NOT NULL,
  "cliente_ie" text NOT NULL,
  "cliente_endereco" text NOT NULL,
  "cliente_bairro" text NOT NULL,
  "cliente_cidade" text NOT NULL,
  "cliente_uf" text NOT NULL,
  "cliente_cep" text NOT NULL,
  "obra" text NOT NULL,
  "obra_id" text NOT NULL,
  "endereco_entrega" text NOT NULL,
  "prisma" text NOT NULL,
  "periodo" text NOT NULL,
  "periodicidade" text NOT NULL,
  "km" text NOT NULL,
  "data_abertura" text NOT NULL,
  "data_fechamento" text NOT NULL,
  "data_previsao_entrega" text NOT NULL,
  "data_conclusao" text NOT NULL,
  "tipo" text NOT NULL,
  "tipo_atendimento" text NOT NULL,
  "atendente" text NOT NULL,
  "atendente_nome" text NOT NULL,
  "empresa" text NOT NULL,
  "empresa_emissora" text NOT NULL,
  "responsavel_id" text NOT NULL,
  "responsavel_nome" text NOT NULL,
  "maquina_id" text NOT NULL,
  "maquina_nome" text NOT NULL,
  "itens" jsonb NOT NULL,
  "frotas_ids" jsonb NOT NULL,
  "maquinas_ids" jsonb NOT NULL,
  "fornecedores_ids" jsonb NOT NULL,
  "valor_total" numeric NOT NULL,
  "valor_principal" numeric NOT NULL,
  "valores_extras" jsonb NOT NULL,
  "valor_desconto" numeric NOT NULL,
  "valor_subtotal" bigint NOT NULL,
  "valor_antecipado" numeric NOT NULL,
  "forma_pagamento" text NOT NULL,
  "condicao_pagamento" text NOT NULL,
  "status" text NOT NULL,
  "confirmada" boolean NOT NULL,
  "prioridade" text NOT NULL,
  "tipo_financeiro" text NOT NULL,
  "descricao" text NOT NULL,
  "observacao_servicos" text NOT NULL,
  "observacoes" text NOT NULL,
  "notas_gerais" text NOT NULL,
  "valor_restante" numeric NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- plano_contas: 6 documentos
CREATE TABLE IF NOT EXISTS plano_contas (
  "id" text NOT NULL,
  "codigo" text NOT NULL,
  "nome" text NOT NULL,
  "tipo" text NOT NULL,
  "nivel" bigint NOT NULL,
  "pai_id" text NOT NULL,
  "descricao" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- ponto_abonos: 1 documentos
CREATE TABLE IF NOT EXISTS ponto_abonos (
  "id" text NOT NULL,
  "funcionario_id" text NOT NULL,
  "data" text NOT NULL,
  "tipo" text NOT NULL,
  "motivo" text NOT NULL,
  "anexo" jsonb NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- ponto_observacoes: 1 documentos
CREATE TABLE IF NOT EXISTS ponto_observacoes (
  "ano" bigint NOT NULL,
  "funcionario_id" text NOT NULL,
  "mes" bigint NOT NULL,
  "id" text NOT NULL,
  "texto" text NOT NULL,
  "updated_at" timestamptz NOT NULL
);

-- ponto_registros: 135 documentos
CREATE TABLE IF NOT EXISTS ponto_registros (
  "id" text NOT NULL,
  "funcionario_id" text NOT NULL,
  "funcionario_nome_planilha" text NOT NULL,
  "funcionario_nao_cadastrado" boolean NOT NULL,
  "id_usuario_planilha" text NOT NULL,
  "departamento_planilha" text NOT NULL,
  "data" text NOT NULL,
  "batidas" jsonb NOT NULL,
  "entrada" text NOT NULL,
  "saida_almoco" text NOT NULL,
  "retorno_almoco" text NOT NULL,
  "saida" text NOT NULL,
  "minutos_trabalhados" bigint NOT NULL,
  "minutos_previstos" bigint NOT NULL,
  "saldo_minutos" bigint NOT NULL,
  "status_dia" text NOT NULL,
  "dia_semana" bigint NOT NULL,
  "origem" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- Tabela `produtos` (0 documentos) — schema inferido vazio, pulada.

-- produtos_admin: 1 documentos
CREATE TABLE IF NOT EXISTS produtos_admin (
  "id" text NOT NULL,
  "codigo_interno" text NOT NULL,
  "codigo_fabricante" text NOT NULL,
  "codigo_barras" text NOT NULL,
  "descricao" text NOT NULL,
  "fabricante" text NOT NULL,
  "aplicacao" text NOT NULL,
  "grupo" text NOT NULL,
  "subgrupo" text NOT NULL,
  "unidade_comercial" text NOT NULL,
  "unidade_tributada" text NOT NULL,
  "multiplo" numeric NOT NULL,
  "preco_custo" numeric NOT NULL,
  "preco_custo_final" bigint NOT NULL,
  "preco_venda" numeric NOT NULL,
  "estoque_atual" numeric NOT NULL,
  "estoque_minimo" numeric NOT NULL,
  "estoque_maximo" numeric NOT NULL,
  "localizacao" text NOT NULL,
  "ncm" text NOT NULL,
  "cst" text NOT NULL,
  "cest" text NOT NULL,
  "origem" text NOT NULL,
  "ipi" numeric NOT NULL,
  "icms" numeric NOT NULL,
  "pis" numeric NOT NULL,
  "cofins" numeric NOT NULL,
  "tipo_item" text NOT NULL,
  "status" text NOT NULL,
  "em_promocao" boolean NOT NULL,
  "preco_promocao" text NOT NULL,
  "observacoes" text NOT NULL,
  "margem_lucro" bigint NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- rh_notificacoes: 4 documentos
CREATE TABLE IF NOT EXISTS rh_notificacoes (
  "id" text NOT NULL,
  "tipo" text NOT NULL,
  "titulo" text NOT NULL,
  "mensagem" text NOT NULL,
  "categoria" text NOT NULL,
  "funcionario_id" text NOT NULL,
  "funcionario_nome" text NOT NULL,
  "lida" boolean NOT NULL,
  "criada_por_ia" boolean NOT NULL,
  "criada_por_user_id" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "tem_pdf" boolean,
  "pdf_artifact_id" text
);

-- Tabela `solicitacoes_folha` (0 documentos) — schema inferido vazio, pulada.

-- Tabela `solicitacoes_folha_financeiro` (0 documentos) — schema inferido vazio, pulada.

-- stock_categories: 1 documentos
CREATE TABLE IF NOT EXISTS stock_categories (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- stock_items: 5 documentos
CREATE TABLE IF NOT EXISTS stock_items (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "code" text NOT NULL,
  "category" text NOT NULL,
  "unit" text NOT NULL,
  "quantity" numeric NOT NULL,
  "min_quantity" numeric NOT NULL,
  "unit_price" numeric NOT NULL,
  "location" text NOT NULL,
  "notes" text NOT NULL,
  "user_id" text,
  "created_at" timestamptz NOT NULL,
  "created_by" text,
  "machine_ids" jsonb
);

-- stock_movements: 2 documentos
CREATE TABLE IF NOT EXISTS stock_movements (
  "id" text NOT NULL,
  "item_id" text NOT NULL,
  "movement_type" text NOT NULL,
  "quantity" numeric NOT NULL,
  "previous_quantity" numeric NOT NULL,
  "new_quantity" numeric NOT NULL,
  "reason" text NOT NULL,
  "notes" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- stock_subcategories: 2 documentos
CREATE TABLE IF NOT EXISTS stock_subcategories (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "category_id" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- storage_trash: 1 documentos
CREATE TABLE IF NOT EXISTS storage_trash (
  "id" text NOT NULL,
  "original_name" text NOT NULL,
  "original_path" text NOT NULL,
  "type" text NOT NULL,
  "deleted_by" text NOT NULL,
  "deleted_by_name" text NOT NULL,
  "deleted_at" timestamptz NOT NULL
);

-- subcategories: 1 documentos
CREATE TABLE IF NOT EXISTS subcategories (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "category_id" text NOT NULL,
  "description" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- subfleets: 1 documentos
CREATE TABLE IF NOT EXISTS subfleets (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "fleet_id" text NOT NULL,
  "description" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- tasks: 1 documentos
CREATE TABLE IF NOT EXISTS tasks (
  "id" text NOT NULL,
  "target_system" text NOT NULL,
  "priority" text NOT NULL,
  "title" text NOT NULL,
  "message" text NOT NULL,
  "attachments" jsonb NOT NULL,
  "created_by_id" text NOT NULL,
  "created_by_name" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "read" boolean NOT NULL,
  "read_at" timestamptz NOT NULL,
  "read_by" text NOT NULL
);

-- usage_logs: 3 documentos
CREATE TABLE IF NOT EXISTS usage_logs (
  "id" text NOT NULL,
  "machine_id" text NOT NULL,
  "hours" numeric NOT NULL,
  "notes" text NOT NULL,
  "user_id" text NOT NULL,
  "created_at" timestamptz NOT NULL
);

-- users: 15 documentos
CREATE TABLE IF NOT EXISTS users (
  "id" text NOT NULL,
  "name" text NOT NULL,
  "email" text NOT NULL,
  "password" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "role" text NOT NULL,
  "last_login" timestamptz,
  "password_reset_at" timestamptz,
  "password_reset_by" text
);

-- veiculos_abastecedores: 2 documentos
CREATE TABLE IF NOT EXISTS veiculos_abastecedores (
  "id" text NOT NULL,
  "machine_id" text NOT NULL,
  "capacidade_diesel" numeric NOT NULL,
  "capacidade_oleo" numeric NOT NULL,
  "capacidade_graxa" numeric NOT NULL,
  "litros_diesel" numeric NOT NULL,
  "litros_oleo" numeric NOT NULL,
  "litros_graxa" numeric NOT NULL,
  "operador_id" text NOT NULL,
  "created_by" text NOT NULL,
  "created_at" timestamptz NOT NULL,
  "updated_at" timestamptz NOT NULL
);
