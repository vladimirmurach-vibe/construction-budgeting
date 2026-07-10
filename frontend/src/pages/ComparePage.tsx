import { useEffect, useMemo, useState } from 'react';
import { CompareChart } from '../components/ChartComponent';
import { money, scenariosApi } from '../api/client';

type Scenario = { id: number; name: string; version_number: number };
type Row = {
  period: string | null;
  metric: string;
  version_a: number;
  version_b: number;
  variance: number;
  variance_percent: number | null;
};

export default function ComparePage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [a, setA] = useState<number | ''>('');
  const [b, setB] = useState<number | ''>('');
  const [rows, setRows] = useState<Row[]>([]);

  useEffect(() => {
    scenariosApi.list(true).then((list: Scenario[]) => {
      setScenarios(list);
      if (list[0]) setA(list[0].id);
      if (list[1]) setB(list[1].id);
      else if (list[0]) setB(list[0].id);
    });
  }, []);

  useEffect(() => {
    if (!a || !b) return;
    scenariosApi.compare(Number(a), Number(b)).then(setRows).catch(() => setRows([]));
  }, [a, b]);

  const chartRows = useMemo(
    () =>
      rows
        .filter((r) => r.metric === 'profit' && r.period)
        .map((r) => ({ period: r.period as string, variance: r.variance })),
    [rows],
  );

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Сравнение версий</h1>
          <p>Моментальные отклонения между любыми сохранёнными версиями бюджета</p>
        </div>
      </div>
      <div className="toolbar">
        <select value={a} onChange={(e) => setA(Number(e.target.value))}>
          {scenarios.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} (v{s.version_number})
            </option>
          ))}
        </select>
        <span>vs</span>
        <select value={b} onChange={(e) => setB(Number(e.target.value))}>
          {scenarios.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} (v{s.version_number})
            </option>
          ))}
        </select>
      </div>
      <div className="grid-2">
        <div className="panel">
          <CompareChart rows={chartRows} />
        </div>
        <div className="panel table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Период</th>
                <th>Метрика</th>
                <th>A</th>
                <th>B</th>
                <th>Δ</th>
                <th>Δ%</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 40).map((r, i) => (
                <tr key={i}>
                  <td>{r.period || '—'}</td>
                  <td>{r.metric}</td>
                  <td>{money(r.version_a)}</td>
                  <td>{money(r.version_b)}</td>
                  <td>{money(r.variance)}</td>
                  <td>{r.variance_percent == null ? '—' : `${r.variance_percent.toFixed(1)}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
