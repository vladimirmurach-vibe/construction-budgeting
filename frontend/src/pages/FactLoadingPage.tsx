import { useEffect, useState } from 'react';
import { factApi } from '../api/client';

export default function FactLoadingPage() {
  const [log, setLog] = useState<{ id: number; status: string; records_loaded: number; timestamp: string; message?: string }[]>([]);
  const [message, setMessage] = useState('');

  const load = () => factApi.log().then(setLog);
  useEffect(() => {
    load();
  }, []);

  async function trigger() {
    try {
      const res = await factApi.trigger();
      setMessage(`Загружено записей: ${res.records_loaded}`);
      await load();
    } catch {
      setMessage('Ошибка загрузки факта');
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Загрузка факта</h1>
          <p>Автоматический и ручной импорт фактических данных из учётных систем</p>
        </div>
        <button className="btn btn-primary" style={{ width: 'auto' }} onClick={trigger}>
          Запустить сейчас
        </button>
      </div>
      {message && <p className="hint" style={{ border: 0, marginBottom: '1rem', paddingTop: 0 }}>{message}</p>}
      <div className="panel table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Время</th>
              <th>Статус</th>
              <th>Записей</th>
              <th>Сообщение</th>
            </tr>
          </thead>
          <tbody>
            {log.map((row) => (
              <tr key={row.id}>
                <td>{new Date(row.timestamp).toLocaleString('ru-RU')}</td>
                <td>
                  <span className="badge">{row.status}</span>
                </td>
                <td>{row.records_loaded}</td>
                <td>{row.message || '—'}</td>
              </tr>
            ))}
            {log.length === 0 && (
              <tr>
                <td colSpan={4} className="empty">
                  Журнал пуст
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
