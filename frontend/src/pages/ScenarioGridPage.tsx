import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import PivotTable from '../components/PivotTable';
import { cashFlowApi, objectsApi, scenariosApi } from '../api/client';

export default function ScenarioGridPage() {
  const { scenarioId } = useParams();
  const id = Number(scenarioId);
  const [scenario, setScenario] = useState<{ name: string; status: string; calculated_at?: string } | null>(null);
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [sc, lines, objects] = await Promise.all([
      scenariosApi.get(id),
      cashFlowApi.list(id),
      objectsApi.list(),
    ]);
    setScenario(sc);
    const codeById = Object.fromEntries(objects.map((o: { id: number; code: string }) => [o.id, o.code]));
    setRows(
      lines.map((l: Record<string, unknown>) => ({
        ...l,
        object_code: codeById[l.construction_object_id as number] || l.construction_object_id,
      })),
    );
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const onCellEdit = useCallback(
    async (lineId: number, field: string, value: number) => {
      await cashFlowApi.update(lineId, { [field]: value });
      await load();
    },
    [load],
  );

  async function recalculate() {
    setBusy(true);
    try {
      await scenariosApi.recalculate(id);
      await load();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Ввод данных</h1>
          <p>
            {scenario?.name || 'Сценарий'} · статус {scenario?.status || '—'}
          </p>
        </div>
        <button className="btn btn-primary" style={{ width: 'auto' }} onClick={recalculate} disabled={busy}>
          {busy ? 'Пересчёт…' : 'Пересчитать сценарий'}
        </button>
      </div>
      <div className="panel">
        <PivotTable data={rows} onCellEdit={onCellEdit} />
        <div className="status-bar">
          <span>Строк: {rows.length}</span>
          <span>Рассчитан: {scenario?.calculated_at ? new Date(scenario.calculated_at).toLocaleString('ru-RU') : 'ещё нет'}</span>
        </div>
      </div>
    </div>
  );
}
