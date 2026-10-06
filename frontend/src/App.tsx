import React, { useState, useEffect } from 'react';
import { LoginPage } from './pages/LoginPage';
import { WelcomePage } from './pages/WelcomePage';
import { ConfigPage } from './pages/ConfigPage';
import { SubmitJobPage } from './pages/SubmitJobPage';
import { MonitorPage } from './pages/MonitorPage';
import { UserTokenDropdown } from './components/UserTokenDropdown';
import { getStoredToken } from './utils/storage';
import { parseJwt } from './utils/jwt';

export const App: React.FC = () => {
  const [activeToken, setActiveToken] = useState<string | null>(getStoredToken());
  const [activeTab, setActiveTab] = useState<'welcome' | 'config' | 'submit' | 'monitor'>('welcome');
  const [selectedPresetKey, setSelectedPresetKey] = useState<string | undefined>(undefined);
  const [submittedJobId, setSubmittedJobId] = useState<string | null>(null);

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
          <button
            type="button"
            className="brand-title"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
              font: 'inherit',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
            }}
            onClick={() => setActiveTab('welcome')}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#fafafa',
                boxShadow: '0 0 8px rgba(255, 255, 255, 0.4)',
                display: 'inline-block',
              }}
            />
            Smart Curriculum Designer
          </button>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-links">
          <button
            type="button"
            className={`nav-tab ${activeTab === 'welcome' ? 'active' : ''}`}
            onClick={() => setActiveTab('welcome')}
          >
            Overview
          </button>
          <button
            type="button"
            className={`nav-tab ${activeTab === 'config' ? 'active' : ''}`}
            onClick={() => setActiveTab('config')}
          >
            Curriculum Config
          </button>
          <button
            type="button"
            className={`nav-tab ${activeTab === 'submit' ? 'active' : ''}`}
            onClick={() => setActiveTab('submit')}
          >
            Submit Job
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
        {activeTab === 'welcome' && (
          <WelcomePage
            onNavigate={(tab, preset) => {
              if (preset) {
                setSelectedPresetKey(preset);
              }
              setActiveTab(tab);
            }}
          />
        )}
        {activeTab === 'config' && (
          <ConfigPage
            initialPresetKey={selectedPresetKey}
            onNavigateToSubmit={() => setActiveTab('submit')}
          />
        )}
        {activeTab === 'submit' && (
          <SubmitJobPage
            onJobSubmitted={(jobUuid: string) => {
              setSubmittedJobId(jobUuid);
              setActiveTab('monitor');
            }}
          />
        )}
        {activeTab === 'monitor' && (
          <MonitorPage initialJobId={submittedJobId || undefined} />
        )}
      </main>
    </div>
  );
};

export default App;
