import { useState } from 'react';
import { importApi, scenariosApi } from '../api/client';

export default function ImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [validation, setValidation] = useState<Record<string, unknown> | null>(null);
  const [scenarioId, setScenarioId] = useState('');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const validate = async () => {
    if (!file) return;
    setValidation(await importApi.validate(file));
  };

  const doImport = async () => {
    if (!file || !scenarioId) return;
    setResult(await importApi.import(scenarioId, file));
  };

  return (
    <div>
      <h2>Импорт из Excel</h2>
      <div className="card">
        <input type="file" accept=".xlsx,.xls,.csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <br /><br />
        <button className="btn" onClick={validate}>Проверить</button>
        {validation && <pre>{JSON.stringify(validation, null, 2)}</pre>}
      </div>
      <div className="card">
        <label>ID сценария</label>
        <input value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} placeholder="UUID сценария" />
        <br /><br />
        <button className="btn" onClick={doImport}>Импортировать</button>
        {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
      </div>
    </div>
  );
}
