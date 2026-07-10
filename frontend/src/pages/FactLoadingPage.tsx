import { useEffect, useState } from 'react';
import { factApi } from '../api/client';

export default function FactLoadingPage() {
  const [logs, setLogs] = useState<Record<string, unknown>[]>([]);
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null);

  const loadLogs = () => factApi.log().then(setLogs);
  useEffect(() => { loadLogs(); }, []);

  const trigger = async () => {
    setLastResult(await factApi.trigger());
    loadLogs();
  };

  return (
    <div>
      <h2>Загрузка фактических данных</h2>
      <div className="card">
        <button className="btn" onClick={trigger}>Запустить загрузку</button>
        {lastResult && <pre>{JSON.stringify(lastResult, null, 2)}</pre>}
      </div>
      <div className="card">
        <table className="data">
          <thead><tr><th>Время</th><th>Статус</th><th>Записей</th><th>Сообщение</th></tr></thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id as string}>
                <td>{l.timestamp as string}</td>
                <td>{l.status as string}</td>
                <td>{l.records_loaded as number}</td>
                <td>{l.message as string}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
