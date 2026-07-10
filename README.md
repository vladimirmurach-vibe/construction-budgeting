# Бюджетирование строительных объектов

Веб-система быстрого пересчёта сценариев бюджета строительных объектов: денежные потоки, консолидация, сравнение версий, отчёты PDF/Excel, загрузка факта.

**Репозиторий:** https://github.com/vladimirmurach-vibe/construction-budgeting  
**Module registry:** https://github.com/vladimirmurach-vibe/module-registry  
**Спецификация:** [`spec/`](./spec/) (v0.1.0)

## Быстрый старт (Docker)

```bash
cp .env.example .env
docker-compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend API / docs:** http://localhost:8000/docs
- **PostgreSQL:** localhost:5432

## Локальный запуск

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
# Запустите PostgreSQL и укажите DATABASE_URL в .env (см. .env.example)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
set VITE_API_URL=http://localhost:8000/api
npm run dev
```

## Учётные записи по умолчанию

| Email | Пароль | Роль |
|-------|--------|------|
| admin@example.com | admin123 | admin |
| analyst@example.com | valid_password | budget_analyst |
| manager@example.com | manager123 | project_manager |
| mgmt@example.com | mgmt123 | management |

## Тесты

```bash
cd backend
set DATABASE_URL=sqlite:///./test.db
python -m pytest tests/ -v
```

## Структура

```
backend/          # FastAPI — API, domain, infrastructure
frontend/         # React 18 — dashboard, CRUD, pivot, charts
spec/             # Спецификация (13 YAML)
docker-compose.yml
```

## Модули из module-registry

| Модуль | Реализация |
|--------|-----------|
| fastapi-base | `backend/app/main.py` |
| auth-jwt | `backend/app/core/security.py`, `api/routers/auth.py` |
| postgres-storage | `backend/app/infrastructure/db/` |
| fastapi-crud-generator | CRUD-роутеры сущностей |
| consensus-calculator | `domain/services/consensus_service.py` |
| adjustment-disaggregation | `domain/services/disaggregation_service.py` |
| forecast-aggregation | `domain/services/aggregation_service.py` |
| csv-data-source | `infrastructure/connectors/csv_data_source.py` |
| react-dashboard-template | `frontend/src/App.tsx` |
| react-crud-pages | страницы CRUD |
| mod-pivot-tabulator | `frontend/src/components/PivotTable.tsx` |
| mod-chart-echarts | `frontend/src/components/ChartComponent.tsx` |
| clean-architecture-pattern | слои presentation / api / domain / infrastructure |
| basic-security-policy | JWT + RBAC в `api/deps.py` |
| PDF (GAP-003) | `domain/services/report_service.py` (ReportLab) |
