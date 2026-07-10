import { useEffect, useState } from 'react';
import { objectsApi } from '../api/client';

type Obj = {
  id: number;
  name: string;
  code: string;
  construction_start: string;
  construction_end: string;
  status: string;
};

export default function ObjectsPage() {
  const [items, setItems] = useState<Obj[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: '',
    code: '',
    construction_start: '2025-01-01',
    construction_end: '2027-12-31',
    status: 'in_progress',
  });
  const [error, setError] = useState('');

  const load = () => objectsApi.list().then(setItems);
  useEffect(() => {
    load();
  }, []);

  async function create() {
    setError('');
    try {
      await objectsApi.create(form);
      setOpen(false);
      await load();
    } catch {
      setError('Проверьте даты и уникальность кода');
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Объекты</h1>
          <p>Справочник строительных объектов и горизонт планирования</p>
        </div>
        <button className="btn btn-primary" style={{ width: 'auto' }} onClick={() => setOpen(true)}>
          Добавить объект
        </button>
      </div>
      <div className="panel table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Код</th>
              <th>Название</th>
              <th>Начало</th>
              <th>Окончание</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            {items.map((o) => (
              <tr key={o.id}>
                <td>{o.code}</td>
                <td>{o.name}</td>
                <td>{o.construction_start}</td>
                <td>{o.construction_end}</td>
                <td>
                  <span className="badge">{o.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {open && (
        <div className="modal-backdrop" onClick={() => setOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Новый объект</h3>
            {(['name', 'code', 'construction_start', 'construction_end'] as const).map((key) => (
              <div className="field" key={key}>
                <label>{key}</label>
                <input
                  type={key.includes('construction') ? 'date' : 'text'}
                  value={form[key]}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              </div>
            ))}
            {error && <p className="error-text">{error}</p>}
            <div className="modal-actions">
              <button className="btn btn-ghost" onClick={() => setOpen(false)}>
                Отмена
              </button>
              <button className="btn btn-primary" style={{ width: 'auto' }} onClick={create}>
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
