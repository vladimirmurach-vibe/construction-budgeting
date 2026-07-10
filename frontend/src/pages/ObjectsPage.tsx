import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { objectsApi } from '../api/client';

export default function ObjectsPage() {
  const [objects, setObjects] = useState<Record<string, unknown>[]>([]);
  const { register, handleSubmit, reset } = useForm();

  const load = () => objectsApi.list().then(setObjects);
  useEffect(() => { load(); }, []);

  const create = async (data: Record<string, string>) => {
    await objectsApi.create(data);
    reset();
    load();
  };

  return (
    <div>
      <h2>Строительные объекты</h2>
      <div className="card">
        <form onSubmit={handleSubmit(create)}>
          <div className="form-group"><label>Название</label><input {...register('name')} required /></div>
          <div className="form-group"><label>Код</label><input {...register('code')} required /></div>
          <div className="form-group"><label>Начало</label><input type="date" {...register('construction_start')} required /></div>
          <div className="form-group"><label>Окончание</label><input type="date" {...register('construction_end')} required /></div>
          <div className="form-group">
            <label>Статус</label>
            <select {...register('status')}>
              <option value="planning">Планирование</option>
              <option value="in_progress">В работе</option>
              <option value="completed">Завершён</option>
            </select>
          </div>
          <button className="btn" type="submit">Добавить</button>
        </form>
      </div>
      <div className="card">
        <table className="data">
          <thead><tr><th>Код</th><th>Название</th><th>Начало</th><th>Окончание</th><th>Статус</th></tr></thead>
          <tbody>
            {objects.map((o) => (
              <tr key={o.id as string}>
                <td>{o.code as string}</td>
                <td>{o.name as string}</td>
                <td>{o.construction_start as string}</td>
                <td>{o.construction_end as string}</td>
                <td>{o.status as string}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
