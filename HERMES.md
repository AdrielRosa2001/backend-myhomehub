# 🏠 MyHomeHub — Backend (FastAPI + Peewee)

## Workflow de Desenvolvimento

### 1. Desenvolver funcionalidades ou corrigir problemas
- Sempre trabalhe em branches separadas: `feature/nome-da-feature` ou `fix/nome-do-fix`
- Siga o padrão REST existente (FastAPI routers em `app/routers/`)
- Mantenha os schemas Pydantic em `app/schemas.py`
- Modelos Peewee em `app/models.py`

### 2. Escrever testes
- Testes em `tests/` usando pytest
- Cobertura mínima: 50% (configurado no CI/CD)
- Testes unitários para regras de negócio
- Testes de integração para endpoints com banco de dados

### 3. Rodar testes e ciclo de refinamento
```bash
pytest --cov=app --cov-report=term-missing
```
- Se encontrar erro: corrija e rode novamente
- Se precisar de novos testes: escreva e rode novamente
- Repita até todos os testes passarem

### 4. Validar com Docker (após testes OK)
```bash
docker compose up -d --build
```
- Se o sistema tiver login, preparar conta de teste:
  - Email: `teste@teste.com`
  - Senha: `teste123`

### 5. Preparar para deploy
- Verificar código com linters:
  ```bash
  ruff check .
  ```
- Verificar vulnerabilidades em dependências
- Validar build Docker: `docker compose build backend`

### 6. Commit e Push (após aprovação)
```bash
git add -A
git commit -m "tipo: descrição clara do que foi feito"
git push origin <branch>
```

## Padrões do Projeto
- **Banco**: PostgreSQL (via Peewee ORM), com fallback SQLite para dev local
- **Autenticação**: JWT (python-jose) + OAuth2PasswordBearer
- **Migração**: Script `migrate_data.py` para migrar SQLite → PostgreSQL
- **Container**: Docker Compose com db (PostgreSQL), backend (FastAPI), frontend (Next.js), nginx
