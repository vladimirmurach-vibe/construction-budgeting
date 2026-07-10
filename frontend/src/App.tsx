import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, NavLink, Route, Routes, useNavigate } from 'react-router-dom';
import { authApi } from './api/client';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ScenariosPage from './pages/ScenariosPage';
import ScenarioGridPage from './pages/ScenarioGridPage';
import ComparePage from './pages/ComparePage';
import ReportsPage from './pages/ReportsPage';
import ObjectsPage from './pages/ObjectsPage';
import ImportPage from './pages/ImportPage';
import FactLoadingPage from './pages/FactLoadingPage';

function Shell({ children, onLogout, user }: { children: React.ReactNode; onLogout: () => void; user: { email: string; role: string } | null }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <p className="logo">СВОД</p>
          <p className="sub">Бюджетирование строительных объектов</p>
        </div>
        <nav className="nav">
          <NavLink to="/dashboard">Консолидация</NavLink>
          <NavLink to="/scenarios">Сценарии</NavLink>
          <NavLink to="/scenarios/compare">Сравнение версий</NavLink>
          <NavLink to="/reports">Отчёты</NavLink>
          <NavLink to="/objects">Объекты</NavLink>
          <NavLink to="/import">Импорт из Excel</NavLink>
          <NavLink to="/admin/fact-loading">Загрузка факта</NavLink>
        </nav>
        <div className="sidebar-foot">
          <div className="user-chip">
            {user?.email}
            <br />
            {user?.role}
          </div>
          <button className="btn btn-secondary" onClick={onLogout}>
            Выход
          </button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

function AppRoutes() {
  const [authed, setAuthed] = useState(!!localStorage.getItem('token'));
  const [user, setUser] = useState<{ email: string; role: string } | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!authed) return;
    authApi
      .me()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('token');
        setAuthed(false);
      });
  }, [authed]);

  function logout() {
    localStorage.removeItem('token');
    setAuthed(false);
    setUser(null);
    navigate('/login');
  }

  if (!authed) {
    return <LoginPage onSuccess={() => setAuthed(true)} />;
  }

  return (
    <Shell onLogout={logout} user={user}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/scenarios" element={<ScenariosPage />} />
        <Route path="/scenarios/compare" element={<ComparePage />} />
        <Route path="/scenarios/:scenarioId/grid" element={<ScenarioGridPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/objects" element={<ObjectsPage />} />
        <Route path="/import" element={<ImportPage />} />
        <Route path="/admin/fact-loading" element={<FactLoadingPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Shell>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginGate />} />
        <Route path="/*" element={<AppRoutes />} />
      </Routes>
    </BrowserRouter>
  );
}

function LoginGate() {
  const navigate = useNavigate();
  if (localStorage.getItem('token')) {
    return <Navigate to="/dashboard" replace />;
  }
  return (
    <LoginPage
      onSuccess={() => {
        navigate('/dashboard');
      }}
    />
  );
}
