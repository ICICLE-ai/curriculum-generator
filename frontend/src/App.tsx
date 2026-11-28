import React, { useState, useEffect } from 'react';
import { GraduationCap } from 'lucide-react';
import { LoginPage } from './pages/LoginPage';
import { WelcomePage } from './pages/WelcomePage';
import { ConfigPage } from './pages/ConfigPage';
import { SubmitJobPage } from './pages/SubmitJobPage';
import { MonitorPage } from './pages/MonitorPage';
import { AssistantPage } from './pages/AssistantPage';
import { UserTokenDropdown } from './components/UserTokenDropdown';
import { getStoredToken } from './utils/storage';
import { parseJwt } from './utils/jwt';

const App: React.FC = () => {
  const [activeToken, setActiveToken] = useState<string | null>(getStoredToken());
  const [activeTab, setActiveTab] = useState<'welcome' | 'config' | 'submit' | 'monitor' | 'assistant'>('welcome');
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

  if (!activeToken) {
    return <LoginPage onLoginSuccess={(tok) => setActiveToken(tok)} />;
  }

  return (
    <div className="app-layout">
      <header className="top-navbar">
        <div className="brand-section">
          <button
            type="button"
            className="brand-btn"
            onClick={() => setActiveTab('welcome')}
          >
            <span className="brand-mark" aria-hidden="true">
              <GraduationCap size={16} />
            </span>
            <span>Smart Curriculum Designer</span>
          </button>
        </div>

        <nav className="nav-links" aria-label="Primary Navigation">
          <button
            type="button"
            className={`nav-tab ${activeTab === 'welcome' ? 'active' : ''}`}
            onClick={() => setActiveTab('welcome')}
          >
            Overview
          </button>
          <button
            type="button"
            className={`nav-tab ${activeTab === 'assistant' ? 'active' : ''}`}
            onClick={() => setActiveTab('assistant')}
          >
            Assistant
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

        <div className="top-navbar-right">
          <UserTokenDropdown onLogout={() => setActiveToken(null)} />
        </div>
      </header>

      <main className="main-content">
        {activeTab === 'welcome' && (
          <WelcomePage
            onNavigate={(tab, preset) => {
              if (preset) {
                setSelectedPresetKey(preset);
              }
              setActiveTab(tab);
            }}
            onOpenJob={(jobUuid) => {
              setSubmittedJobId(jobUuid);
              setActiveTab('monitor');
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
        {activeTab === 'assistant' && <AssistantPage />}
        {activeTab === 'monitor' && (
          <MonitorPage initialJobId={submittedJobId || undefined} />
        )}
      </main>
    </div>
  );
};

export default App;
