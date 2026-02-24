# Backend - Estrutura de Refatoração

## Estrutura Atual (server.py monolítico)
O arquivo `server.py` contém toda a lógica da API em ~5400 linhas.
Um índice foi adicionado no início do arquivo para facilitar a navegação.

## Estrutura Proposta (Modular)

```
/app/backend/
├── main.py              # Ponto de entrada da aplicação
├── server.py            # Versão atual (monolítica)
├── server_backup.py     # Backup do server.py original
│
├── routes/              # Rotas da API
│   ├── __init__.py
│   ├── auth.py          # /api/auth/*
│   ├── categories.py    # /api/categories/*
│   ├── machines.py      # /api/machines/*
│   ├── maintenances.py  # /api/maintenances/*
│   ├── stock.py         # /api/stock/*
│   ├── obras.py         # /api/obras/*
│   ├── dashboard.py     # /api/dashboard/*
│   ├── admin.py         # /api/admin/* (financeiro)
│   ├── admin_panel.py   # /api/admin-panel/* (gestão)
│   ├── export.py        # /api/export/*
│   ├── chatbot.py       # /api/chatbot/*
│   ├── files.py         # /api/files/*
│   └── tasks.py         # /api/tasks/*
│
├── models/              # Modelos Pydantic
│   ├── __init__.py
│   ├── core.py          # User, Category, Machine, Maintenance, etc.
│   └── admin.py         # Cadastro, Produto, Contas, OS, etc.
│
├── utils/               # Utilitários
│   ├── __init__.py
│   ├── database.py      # Conexão MongoDB, configurações
│   ├── auth.py          # JWT, hash de senha, get_current_user
│   └── audit.py         # Função de log de auditoria
│
├── services/            # Lógica de negócios (futuro)
│   └── __init__.py
│
└── uploads/             # Arquivos enviados
    └── task_uploads/    # Anexos de tarefas
```

## Como Migrar para Estrutura Modular

1. **Fase 1**: Extrair utilitários (✅ Concluído)
   - `utils/database.py` - Conexão MongoDB
   - `utils/auth.py` - Autenticação JWT
   - `utils/audit.py` - Log de auditoria

2. **Fase 2**: Extrair modelos (✅ Concluído)
   - `models/core.py` - Modelos principais
   - `models/admin.py` - Modelos administrativos

3. **Fase 3**: Extrair rotas (Parcial)
   - `routes/auth.py` - ✅ Criado
   - `routes/categories.py` - ✅ Criado
   - Demais rotas podem ser extraídas seguindo o mesmo padrão

4. **Fase 4**: Atualizar main.py
   - Importar todos os routers
   - Registrar no app

## Benefícios da Refatoração

- **Manutenibilidade**: Arquivos menores e focados
- **Testabilidade**: Cada módulo pode ser testado isoladamente
- **Escalabilidade**: Fácil adicionar novas funcionalidades
- **Colaboração**: Múltiplos desenvolvedores podem trabalhar em paralelo

## Notas

- O `server.py` atual está funcional e documentado com índice
- A migração para estrutura modular pode ser feita incrementalmente
- Sempre manter backup antes de alterações estruturais
