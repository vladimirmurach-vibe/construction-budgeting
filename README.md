# СВОД — бюджетирование строительных объектов

Продукт для быстрого пересчёта сценариев бюджета строительных объектов: консолидация, сравнение версий, отчёты PDF/Excel, загрузка факта.

**Репозиторий:** https://github.com/vladimirmurach-vibe/construction-budgeting  
**Module registry:** https://github.com/vladimirmurach-vibe/module-registry  
**Спецификация:** [`spec/`](./spec/)

## Быстрый старт

```bash
cp .env.example .env
docker-compose up --build
```

- UI: http://localhost:3000  
- API: http://localhost:8000/docs  

**Демо-вход:** `analyst@example.com` / `valid_password`

## Локально

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
set VITE_API_URL=http://localhost:8000/api
npm run dev
```

## Тесты

```bash
cd backend
set DATABASE_URL=sqlite:///./test.db
python -m pytest tests/ -v
```

## Архитектура

Собрано по `spec/architecture.yaml` и манифестам module-registry:

| Модуль | Реализация |
|--------|------------|
| fastapi-base | `backend/app/main.py` |
| auth-jwt | `core/security.py`, `presentation/api/routers/auth.py` |
| postgres-storage | `infrastructure/db/` |
| consensus-calculator | `domain/services/consensus_service.py` |
| adjustment-disaggregation | `domain/services/disaggregation_service.py` |
| forecast-aggregation | `domain/services/aggregation_service.py` |
| csv-data-source | `infrastructure/connectors/csv_data_source.py` |
| react-dashboard-template | `frontend/src/App.tsx` |
| mod-pivot-tabulator | `components/PivotTable.tsx` |
| mod-chart-echarts | `components/ChartComponent.tsx` |
| clean-architecture-pattern | presentation / domain / infrastructure |
| PDF (GAP-003) | `domain/services/report_service.py` |
