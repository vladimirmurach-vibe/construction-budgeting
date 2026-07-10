import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { objectsApi, scenariosApi } from '../api/client';

type Scenario = {
  id: number;
  name: string;
  type: string;
  scope: string;
  status: string;
  version_number: number;
  calculated_at?: string;
};

export default function ScenariosPage() {
  const [items, setItems] = useState<Scenario[]>([]);
  const [objects, setObjects] = useState<{ id: number; name: string }[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: '',
    type: 'budget',
    scope: 'all_objects',
    construction_object_id: '' as number | '',
  });
  const [busy, setBusy] = useState<number | null>(null);
  const [error, setError] = useState('');

  const load = () => scenariosApi.list(true).then(setItems);
  useEffect(() => {
    load();
    objectsApi.list().then(setObjects);
  }, []);

  async function create() {
    setError('');
    try {
      await scenariosApi.create({
        name: form.name,
        type: form.type,
        scope: form.scope,
        construction_object_id: form.scope === 'single_object' ? form.construction_object_id : null,
      });
      setOpen(false);
      setForm({ name: '', type: 'budget', scope: 'all_objects', construction_object_id: '' });
      await load();
    } catch (e: unknown) {
      setError('Не удалось создать сценарий. Проверьте поля.');
    }
  }

  async function recalculate(id: number) {
    setBusy(id);
    try {
      await scenariosApi.recalculate(id);
      await load();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Сценарии</h1>
          <p>Версии бюджета и прогноза с полным хранением истории расчётов</p>
        </div>
        <button className="btn btn-primary" style={{ width: 'auto' }} onClick={() => setOpen(true)}>
          Новый сценарий
        </button>
      </div>

      <div className="panel table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Название</th>
              <th>Тип</th>
              <th>Охват</th>
              <th>Версия</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td>{s.type === 'budget' ? 'Бюджет' : 'Прогноз'}</td>
                <td>{s.scope === 'all_objects' ? 'Все объекты' : 'Один объект'}</td>
                <td>v{s.version_number}</td>
                <td>
                  <span className={`badge ${s.status}`}>{s.status}</span>
                </td>
                <td>
                  <div className="toolbar" style={{ margin: 0 }}>
                    <Link className="btn btn-secondary" to={`/scenarios/${s.id}/grid`}>
                      Ввод
                    </Link>
                    <button className="btn btn-secondary" disabled={busy === s.id} onClick={() => recalculate(s.id)}>
                      {busy === s.id ? 'Пересчёт…' : 'Пересчитать'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {open && (
        <div className="modal-backdrop" onClick={() => setOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Создать сценарий</h3>
            <div className="field">
              <label>Название</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="field">
              <label>Тип</label>
              <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                <option value="budget">Бюджет</option>
                <option value="forecast">Прогноз</option>
              </select>
            </div>
            <div className="field">
              <label>Охват</label>
              <select value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value })}>
                <option value="all_objects">Все объекты</option>
                <option value="single_object">Один объект</option>
              </select>
            </div>
            {form.scope === 'single_object' && (
              <div className="field">
                <label>Объект</label>
                <select
                  value={form.construction_object_id}
                  onChange={(e) => setForm({ ...form, construction_object_id: Number(e.target.value) })}
                >
                  <option value="">Выберите…</option>
                  {objects.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {error && <p className="error-text">{error}</p>}
            <div className="modal-actions">
              <button className="btn btn-ghost" onClick={() => setOpen(false)}>
                Отмена
              </button>
              <button className="btn btn-primary" style={{ width: 'auto' }} onClick={create}>
                Создать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
