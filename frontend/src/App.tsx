import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes, NavLink, useNavigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ScenariosPage from './pages/ScenariosPage';
import ScenarioGridPage from './pages/ScenarioGridPage';
import ComparePage from './pages/ComparePage';
import ReportsPage from './pages/ReportsPage';
import ObjectsPage from './pages/ObjectsPage';
import ImportPage from './pages/ImportPage';
import FactLoadingPage from './pages/FactLoadingPage';
import { authApi } from './api/client';

function Layout({ children, onLogout }: { children: React.ReactNode; onLogout: () => void }) {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <h1>Бюджетирование строительных объектов</h1>
        <nav>
          <NavLink to="/dashboard">Консолидация</NavLink>
          <NavLink to="/scenarios">Сценарии</NavLink>
          <NavLink to="/scenarios/compare">Сравнение версий</NavLink>
          <NavLink to="/reports">Отчёты</NavLink>
          <NavLink to="/objects">Объекты</NavLink>
          <NavLink to="/import">Импорт из Excel</NavLink>
          <NavLink to="/admin/fact-loading">Загрузка факта</NavLink>
        </nav>
        <button className="btn btn-secondary" style={{ marginTop: '2rem' }} onClick={onLogout}>Выход</button>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

function AppRoutes() {
  const [authed, setAuthed] = useState(!!localStorage.getItem('token'));
  const navigate = useNavigate();

  useEffect(() => {
    if (authed) authApi.me().catch(() => { localStorage.removeItem('token'); setAuthed(false); });
  }, [authed]);

  if (!authed) return <LoginPage onLogin={() => { setAuthed(true); navigate('/dashboard'); }} />;

  const logout = () => { localStorage.removeItem('token'); setAuthed(false); };

  return (
    <Layout onLogout={logout}>
      <Routes>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/scenarios" element={<ScenariosPage />} />
        <Route path="/scenarios/:scenarioId/grid" element={<ScenarioGridPage />} />
        <Route path="/scenarios/compare" element={<ComparePage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/objects" element={<ObjectsPage />} />
        <Route path="/import" element={<ImportPage />} />
        <Route path="/admin/fact-loading" element={<FactLoadingPage />} />
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
