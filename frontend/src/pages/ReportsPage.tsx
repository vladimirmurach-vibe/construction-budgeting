import { useEffect, useState } from 'react';
import { reportsApi, scenariosApi } from '../api/client';

export default function ReportsPage() {
  const [scenarios, setScenarios] = useState<{ id: string; name: string }[]>([]);
  const [reports, setReports] = useState<Record<string, unknown>[]>([]);
  const [scenarioId, setScenarioId] = useState('');
  const [reportType, setReportType] = useState('consolidated');
  const [format, setFormat] = useState('excel');

  useEffect(() => {
    scenariosApi.list().then((s) => { setScenarios(s); if (s.length) setScenarioId(s[0].id); });
    reportsApi.list().then(setReports);
  }, []);

  const generate = async () => {
    await reportsApi.generate({ scenario_id: scenarioId, type: reportType, format });
    reportsApi.list().then(setReports);
  };

  return (
    <div>
      <h2>Отчёты</h2>
      <div className="card">
        <div className="form-group">
          <label>Сценарий</label>
          <select value={scenarioId} onChange={(e) => setScenarioId(e.target.value)}>
            {scenarios.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Тип</label>
          <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
            <option value="consolidated">Консолидированный</option>
            <option value="by_object">По объекту</option>
          </select>
        </div>
        <div className="form-group">
          <label>Формат</label>
          <select value={format} onChange={(e) => setFormat(e.target.value)}>
            <option value="excel">Excel</option>
            <option value="pdf">PDF</option>
          </select>
        </div>
        <button className="btn" onClick={generate}>Сформировать</button>
      </div>
      <div className="card">
        <table className="data">
          <thead><tr><th>Дата</th><th>Тип</th><th>Формат</th><th>Файл</th></tr></thead>
          <tbody>
            {reports.map((r) => (
              <tr key={r.id as string}>
                <td>{r.generated_at as string}</td>
                <td>{r.type as string}</td>
                <td>{r.format as string}</td>
                <td>{r.file_path as string}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
