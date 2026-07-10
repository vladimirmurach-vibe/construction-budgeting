import { useEffect, useState } from 'react';
import { reportsApi, scenariosApi } from '../api/client';

export default function ReportsPage() {
  const [scenarios, setScenarios] = useState<{ id: number; name: string }[]>([]);
  const [scenarioId, setScenarioId] = useState<number | ''>('');
  const [type, setType] = useState('consolidated');
  const [format, setFormat] = useState<'excel' | 'pdf'>('excel');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    scenariosApi.list().then((list: { id: number; name: string }[]) => {
      setScenarios(list);
      if (list[0]) setScenarioId(list[0].id);
    });
  }, []);

  async function generate() {
    if (!scenarioId) return;
    setBusy(true);
    setMessage('');
    try {
      const report = await reportsApi.generate({
        scenario_id: Number(scenarioId),
        type,
        format,
      });
      setMessage(`Отчёт #${report.id} готов`);
      const res = await fetch(reportsApi.downloadUrl(report.id), {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${report.id}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setMessage('Не удалось сформировать отчёт. Пересчитайте сценарий.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Отчёты</h1>
          <p>Автоматическая выгрузка PDF и Excel для менеджмента и органов управления</p>
        </div>
      </div>
      <div className="panel" style={{ maxWidth: 520 }}>
        <div className="field">
          <label>Сценарий</label>
          <select value={scenarioId} onChange={(e) => setScenarioId(Number(e.target.value))}>
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Тип</label>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="consolidated">Консолидированный</option>
            <option value="by_object">По объекту</option>
            <option value="comparison">Сравнение</option>
          </select>
        </div>
        <div className="field">
          <label>Формат</label>
          <select value={format} onChange={(e) => setFormat(e.target.value as 'excel' | 'pdf')}>
            <option value="excel">Excel</option>
            <option value="pdf">PDF</option>
          </select>
        </div>
        <button className="btn btn-primary" onClick={generate} disabled={busy}>
          {busy ? 'Формируем…' : 'Сформировать и скачать'}
        </button>
        {message && (
          <p className="hint" style={{ border: 0, marginTop: '1rem', paddingTop: 0 }}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}
