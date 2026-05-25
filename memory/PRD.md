# ERP CRA - Product Requirements Document

## Visão Geral
ERP Full-stack (React + FastAPI + MongoDB) para gestão de Frota, Finanças, RH e Operações.

## Módulos Principais
- **Gerenciamento**: Máquinas, Manutenções, Estoque, Obras, Categorias
- **Administrativo (Financeiro)**: Contas a Pagar/Receber, OS, Cadastros, Plano de Contas, Centro de Custo, Conciliação, Aluguéis, Imóveis, Importação NF-e/NFS-e
- **RH**: Funcionários, Jornadas de Trabalho, Ponto Eletrônico (dinâmico), Banco de Horas, EPIs, Solicitações de Folha
- **Armazenamento**: Pastas, Upload, Documentos
- **Painel Admin**: Usuários, Permissões, Auditoria (com Rollback), Database Manager, Backup Exportação

## Histórico de Implementações

### 25/05/2026
- **Histórico de Ações ampliado** (FinanceiroHistoryPanel): removido filtro restritivo de `module: Administrativo` e aumentado limite de 80 → 200 registros, agora exibindo ações de todos os módulos.

### Sessões anteriores
- Coluna "Saldo Restante" e modal de parcelas em Contas a Pagar/Receber
- Audit Logs e Rollback expandidos (`reversible=True`) para Cadastros, Aluguéis, Imóveis, Centro de Custo, etc.
- Ordenação de colunas server-side na Importação NF-e/NFS-e
- Bug fix RH: Ponto Eletrônico passou a usar `jornada_id` dinâmica
- Bug fix Financeiro: Filtros incluem contas `parcial` em "A Pagar", "Vencidas" e "A Vencer"
- Endpoint admin de exportação ZIP completa do banco (MongoDB → Supabase) preservando `_id`
- Bug fix Financeiro: PUT em conta quitada não reverte mais o status

## Backlog (Pendente)
- **P2**: Refatoração Fase 2 do `server.py` (extrair rotas restantes)
- **P2**: Gerar parcelas automáticas em Contas a Receber quando OS recorrente é criada
- **P2**: Mini-histórico do cliente no dropdown da OS
- **P3**: Dashboard de Custo por Máquina (combustível, manutenção, peças vs aluguel)
- **P3**: Links públicos de compartilhamento para relatórios PDF

## Integrações
- ABRASF Webservice (SOAP)
- Emergent LLM Key (OCR / Chat)
- ViaCEP / BrasilAPI / CBO API

## Credenciais de Teste
Email: test@test.com / Senha: password
