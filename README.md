# Бюджетирование строительных объектов

Спецификация веб-инструмента быстрого пересчёта сценариев бюджета строительных объектов.

**Репозиторий:** https://github.com/vladimirmurach-vibe/construction-budgeting  
**Module registry:** https://github.com/vladimirmurach-vibe/module-registry  
**Версия спецификации:** 0.1.0 (draft)

## Структура

Все артефакты спецификации находятся в папке [`spec/`](./spec/):

| Файл | Назначение |
|------|------------|
| `index.yaml` | Метаданные проекта и индекс файлов |
| `business.yaml` | Проблема, цель, роли, ограничения |
| `data.yaml` | Сущности и атрибуты |
| `requirements.yaml` | Требования с приоритетами |
| `ui.yaml` | Экраны и навигация |
| `modules.yaml` | Выбранные модули из registry |
| `architecture.yaml` | Слои и маппинг требований → модули |
| `acceptance.yaml` | Приёмочные тесты (high) |
| `assumptions.yaml` | Допущения |
| `gaps.yaml` | Неопределённости |
| `validation.yaml` | Правила валидации |
| `decisions.yaml` | Архитектурные решения |
| `history.yaml` | История версий спецификации |
