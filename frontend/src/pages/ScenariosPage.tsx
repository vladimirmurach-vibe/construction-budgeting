import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { objectsApi, scenariosApi } from '../api/client';

export default function ScenariosPage() {
  const [scenarios, setScenarios] = useState<Record<string, unknown>[]>([]);
  const [objects, setObjects] = useState<{ id: string; name: string }[]>([]);
  const [showForm, setShowForm] = useState(false);
  const { register, handleSubmit, watch } = useForm();
  const navigate = useNavigate();
  const scope = watch('scope');

  const load = () => scenariosApi.list(true).then(setScenarios);
  useEffect(() => { load(); objectsApi.list().then(setObjects); }, []);

  const create = async (data: Record<string, string>) => {
    await scenariosApi.create({
      name: data.name,
      type: data.type,
      scope: data.scope,
      construction_object_id: data.scope === 'single_object' ? data.construction_object_id : undefined,
    });
    setShowForm(false);
    load();
  };

  return (
    <div>
      <h2>Сценарии</h2>
      <button className="btn" onClick={() => setShowForm(!showForm)}>Создать сценарий</button>
      {showForm && (
        <div className="card">
          <form onSubmit={handleSubmit(create)}>
            <div className="form-group"><label>Название</label><input {...register('name')} required /></div>
            <div className="form-group">
              <label>Тип</label>
              <select {...register('type')}><option value="budget">Бюджет</option><option value="forecast">Прогноз</option></select>
            </div>
            <div className="form-group">
              <label>Охват</label>
              <select {...register('scope')}><option value="all_objects">Все объекты</option><option value="single_object">Один объект</option></select>
            </div>
            {scope === 'single_object' && (
              <div className="form-group">
                <label>Объект</label>
                <select {...register('construction_object_id')} required>
                  {objects.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
                </select>
              </div>
            )}
            <button className="btn" type="submit">Создать</button>
          </form>
        </div>
      )}
      <div className="card">
        <table className="data">
          <thead><tr><th>Название</th><th>Тип</th><th>Версия</th><th>Статус</th><th>Действия</th></tr></thead>
          <tbody>
            {scenarios.map((s) => (
              <tr key={s.id as string}>
                <td>{s.name as string}</td>
                <td>{s.type as string}</td>
                <td>{s.version_number as number}</td>
                <td>{s.status as string}</td>
                <td>
                  <button className="btn btn-secondary" onClick={() => navigate(`/scenarios/${s.id}/grid`)}>Ввод данных</button>
                  {' '}
                  <button className="btn" onClick={() => scenariosApi.recalculate(s.id as string).then(load)}>Пересчёт</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
