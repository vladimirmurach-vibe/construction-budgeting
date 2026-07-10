import { useEffect, useState } from 'react';
import ChartComponent from '../components/ChartComponent';
import { financialApi, scenariosApi } from '../api/client';

export default function DashboardPage() {
  const [scenarios, setScenarios] = useState<{ id: string; name: string }[]>([]);
  const [scenarioId, setScenarioId] = useState('');
  const [consolidated, setConsolidated] = useState<{ period: string; revenue: number; costs: number; profit: number }[]>([]);
  const [summary, setSummary] = useState({ total_revenue: 0, total_costs: 0, total_profit: 0, objects_count: 0 });

  useEffect(() => {
    scenariosApi.list().then((s) => {
      setScenarios(s);
      if (s.length) setScenarioId(s[0].id);
    });
  }, []);

  useEffect(() => {
    if (!scenarioId) return;
    financialApi.consolidated(scenarioId).then(setConsolidated);
    financialApi.summary(scenarioId).then(setSummary);
  }, [scenarioId]);

  return (
    <div>
      <h2>Консолидация финансового результата</h2>
      <div className="card">
        <div className="form-group">
          <label>Сценарий</label>
          <select value={scenarioId} onChange={(e) => setScenarioId(e.target.value)}>
            {scenarios.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
      </div>
      <div className="summary-grid">
        <div className="summary-card"><div className="value">{summary.total_revenue.toLocaleString()}</div><div>Выручка</div></div>
        <div className="summary-card"><div className="value">{summary.total_costs.toLocaleString()}</div><div>Затраты</div></div>
        <div className="summary-card"><div className="value">{summary.total_profit.toLocaleString()}</div><div>Прибыль</div></div>
        <div className="summary-card"><div className="value">{summary.objects_count}</div><div>Объектов</div></div>
      </div>
      <div className="card">
        <ChartComponent
          categories={consolidated.map((r) => r.period)}
          series={[
            { name: 'Выручка', data: consolidated.map((r) => r.revenue) },
            { name: 'Затраты', data: consolidated.map((r) => r.costs) },
            { name: 'Прибыль', data: consolidated.map((r) => r.profit) },
          ]}
        />
      </div>
    </div>
  );
}
