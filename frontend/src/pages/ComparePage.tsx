import { useEffect, useState } from 'react';
import ChartComponent from '../components/ChartComponent';
import { scenariosApi } from '../api/client';

export default function ComparePage() {
  const [scenarios, setScenarios] = useState<{ id: string; name: string }[]>([]);
  const [versionA, setVersionA] = useState('');
  const [versionB, setVersionB] = useState('');
  const [compareData, setCompareData] = useState<{ period: string; variance: number; variance_percent: number }[]>([]);
  const [chartData, setChartData] = useState<{ categories: string[]; series: { name: string; data: number[] }[] } | null>(null);

  useEffect(() => { scenariosApi.list().then(setScenarios); }, []);

  const compare = async () => {
    if (!versionA || !versionB) return;
    const data = await scenariosApi.compare(versionA, versionB);
    setCompareData(data);
    const chart = await scenariosApi.compareChart(versionA, versionB);
    setChartData(chart);
  };

  return (
    <div>
      <h2>Сравнение версий</h2>
      <div className="card">
        <div className="form-group">
          <label>Версия A</label>
          <select value={versionA} onChange={(e) => setVersionA(e.target.value)}>
            <option value="">Выберите</option>
            {scenarios.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Версия B</label>
          <select value={versionB} onChange={(e) => setVersionB(e.target.value)}>
            <option value="">Выберите</option>
            {scenarios.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <button className="btn" onClick={compare}>Сравнить</button>
      </div>
      {chartData && (
        <div className="card">
          <ChartComponent categories={chartData.categories} series={chartData.series} chartType="bar" />
        </div>
      )}
      <div className="card">
        <table className="data">
          <thead><tr><th>Период</th><th>Отклонение</th><th>Отклонение %</th></tr></thead>
          <tbody>
            {compareData.map((r) => (
              <tr key={r.period}>
                <td>{r.period}</td>
                <td>{r.variance.toLocaleString()}</td>
                <td>{r.variance_percent.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
