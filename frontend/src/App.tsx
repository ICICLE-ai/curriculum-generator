import React, { useState } from 'react';
import { TokenPage } from './pages/TokenPage';
import { ConfigPage } from './pages/ConfigPage';
import { MonitorPage } from './pages/MonitorPage';
import { PlaygroundPage } from './pages/PlaygroundPage';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'tokens' | 'config' | 'monitor' | 'playground'>('tokens');

  return (
    <div className="app-layout">
      {/* Top Navigation Bar */}
      <header className="top-navbar">
        <div className="brand-section">
          
          <div>
            <div className="brand-title">DigitalAgEdu</div>
            <div className="brand-subtitle">AI Curriculum Generator & Interactive Portal</div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-links">
          <button
            type="button"
            className={`nav-tab ${activeTab === 'tokens' ? 'active' : ''}`}
            onClick={() => setActiveTab('tokens')}
          >
            Tapis Tokens
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
            className={`nav-tab ${activeTab === 'monitor' ? 'active' : ''}`}
            onClick={() => setActiveTab('monitor')}
          >
            Live Monitor
          </button>
          
        </nav>

        
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'tokens' && <TokenPage />}
        {activeTab === 'config' && <ConfigPage />}
        {activeTab === 'monitor' && <MonitorPage />}
        {activeTab === 'playground' && <PlaygroundPage />}
      </main>
    </div>
  );
};

export default App;
