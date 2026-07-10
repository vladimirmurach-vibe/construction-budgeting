import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import PivotTable from '../components/PivotTable';
import { cashFlowApi, scenariosApi } from '../api/client';

export default function ScenarioGridPage() {
  const { scenarioId } = useParams();
  const [data, setData] = useState<Record<string, unknown>[]>([]);
  const [status, setStatus] = useState('');

  const load = () => {
    if (!scenarioId) return;
    cashFlowApi.grid(scenarioId).then(setData);
  };

  useEffect(load, [scenarioId]);

  const handleEdit = async (id: string, field: string, value: number) => {
    await cashFlowApi.update(id, { [field]: value });
    load();
  };

  const recalculate = async () => {
    if (!scenarioId) return;
    const resp = await scenariosApi.recalculate(scenarioId);
    setStatus(`Пересчёт завершён: ${resp.calculated_at}`);
    load();
  };

  return (
    <div>
      <h2>Таблица ввода по формам</h2>
      <div className="card">
        <button className="btn" data-testid="save-button" onClick={load}>Сохранить</button>
        {' '}
        <button className="btn" onClick={recalculate}>Пересчёт</button>
        {status && <p>{status}</p>}
      </div>
      <div className="card">
        <PivotTable data={data} editable onCellEdit={handleEdit} />
      </div>
    </div>
  );
}
