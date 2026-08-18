import React, { useState, useEffect } from 'react';
import { LoginPage } from './pages/LoginPage';
import { ConfigPage } from './pages/ConfigPage';
import { MonitorPage } from './pages/MonitorPage';
import { PlaygroundPage } from './pages/PlaygroundPage';
import { UserTokenDropdown } from './components/UserTokenDropdown';
import { getStoredToken } from './utils/storage';
import { parseJwt } from './utils/jwt';

export const App: React.FC = () => {
  const [activeToken, setActiveToken] = useState<string | null>(getStoredToken());
  const [activeTab, setActiveTab] = useState<'config' | 'monitor' | 'playground'>('config');

  useEffect(() => {
    const checkAuth = () => {
      const token = getStoredToken();
      if (!token) {
        setActiveToken(null);
        return;
      }
      const parsed = parseJwt(token);
      if (!parsed || parsed.isExpired) {
        setActiveToken(null);
      } else {
        setActiveToken(token);
      }
    };

    checkAuth();
    const interval = setInterval(checkAuth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Show login gate if unauthenticated
  if (!activeToken) {
    return <LoginPage onLoginSuccess={(tok) => setActiveToken(tok)} />;
  }

  return (
    <div className="app-layout">
      {/* Top Navigation Bar */}
      <header className="top-navbar">
        <div className="brand-section">
          <div>
            <div className="brand-title">DigitalAgEdu</div>
            
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-links">
          <button
            type="button"
            className={`nav-tab ${activeTab === 'config' ? 'active' : ''}`}
            onClick={() => setActiveTab('config')}
          >
            Curriculum Config
          </button>
          <button
            type="button"
            className={`nav-tab ${activeTab === 'monitor' ? 'active' : ''}`}
            onClick={() => setActiveTab('monitor')}
          >
            Live Monitor
          </button>
        </nav>

        {/* User / Token Profile Dropdown */}
        <div className="top-navbar-right">
          <UserTokenDropdown onLogout={() => setActiveToken(null)} />
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'config' && <ConfigPage />}
        {activeTab === 'monitor' && <MonitorPage />}
        {activeTab === 'playground' && <PlaygroundPage />}
      </main>
    </div>
  );
};

export default App;
