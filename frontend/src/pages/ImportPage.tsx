import { useEffect, useState } from 'react';
import { importApi, scenariosApi } from '../api/client';

export default function ImportPage() {
  const [scenarios, setScenarios] = useState<{ id: number; name: string }[]>([]);
  const [scenarioId, setScenarioId] = useState<number | ''>('');
  const [filePath, setFilePath] = useState('imports/demo.csv');
  const [result, setResult] = useState('');

  useEffect(() => {
    scenariosApi.list().then((list: { id: number; name: string }[]) => {
      setScenarios(list);
      if (list[0]) setScenarioId(list[0].id);
    });
  }, []);

  async function validate() {
    try {
      const data = await importApi.validate(filePath);
      setResult(JSON.stringify(data, null, 2));
    } catch {
      setResult('Ошибка валидации файла');
    }
  }

  async function runImport() {
    if (!scenarioId) return;
    try {
      const data = await importApi.run(Number(scenarioId), filePath);
      setResult(JSON.stringify(data, null, 2));
    } catch {
      setResult('Ошибка импорта');
    }
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Импорт из Excel</h1>
          <p>Загрузка исходных данных с проверкой полноты переноса</p>
        </div>
      </div>
      <div className="panel" style={{ maxWidth: 560 }}>
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
          <label>Путь к файлу на сервере</label>
          <input value={filePath} onChange={(e) => setFilePath(e.target.value)} />
        </div>
        <div className="toolbar">
          <button className="btn btn-secondary" onClick={validate}>
            Проверить
          </button>
          <button className="btn btn-primary" style={{ width: 'auto' }} onClick={runImport}>
            Импортировать
          </button>
        </div>
        {result && <pre className="hint" style={{ whiteSpace: 'pre-wrap' }}>{result}</pre>}
      </div>
    </div>
  );
}
