import { useEffect, useMemo, useState } from 'react';
import { ConsolidationChart } from '../components/ChartComponent';
import { money, resultsApi, scenariosApi } from '../api/client';

type Scenario = { id: number; name: string; status: string };
type Result = { period: string; revenue: number; costs: number; profit: number; is_consolidated: boolean };

export default function DashboardPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [scenarioId, setScenarioId] = useState<number | ''>('');
  const [rows, setRows] = useState<Result[]>([]);

  useEffect(() => {
    scenariosApi.list().then((list: Scenario[]) => {
      setScenarios(list);
      const calculated = list.find((s) => s.status === 'calculated') || list[0];
      if (calculated) setScenarioId(calculated.id);
    });
  }, []);

  useEffect(() => {
    if (!scenarioId) return;
    resultsApi.consolidated(Number(scenarioId)).then(setRows).catch(() => setRows([]));
  }, [scenarioId]);

  const totals = useMemo(() => {
    return rows.reduce(
      (acc, r) => ({
        revenue: acc.revenue + r.revenue,
        costs: acc.costs + r.costs,
        profit: acc.profit + r.profit,
      }),
      { revenue: 0, costs: 0, profit: 0 },
    );
  }, [rows]);

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Консолидация</h1>
          <p>Финансовый результат по портфелю объектов на горизонте планирования</p>
        </div>
        <select value={scenarioId} onChange={(e) => setScenarioId(Number(e.target.value))}>
          {scenarios.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} · {s.status}
            </option>
          ))}
        </select>
      </div>

      <div className="metrics">
        <div className="metric">
          <p className="label">Выручка</p>
          <p className="value">{money(totals.revenue)}</p>
        </div>
        <div className="metric">
          <p className="label">Затраты</p>
          <p className="value">{money(totals.costs)}</p>
        </div>
        <div className="metric">
          <p className="label">Прибыль</p>
          <p className="value">{money(totals.profit)}</p>
        </div>
        <div className="metric">
          <p className="label">Периодов</p>
          <p className="value">{rows.length}</p>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <ConsolidationChart data={rows} />
        </div>
        <div className="panel table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Период</th>
                <th>Выручка</th>
                <th>Затраты</th>
                <th>Прибыль</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td colSpan={4} className="empty">
                    Нет консолидированных данных. Пересчитайте сценарий.
                  </td>
                </tr>
              )}
              {rows.map((r) => (
                <tr key={r.period}>
                  <td>{r.period}</td>
                  <td>{money(r.revenue)}</td>
                  <td>{money(r.costs)}</td>
                  <td>{money(r.profit)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
