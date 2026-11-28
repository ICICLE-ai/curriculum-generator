import React from 'react';
import { clearStoredTokens } from '../../utils/storage';

export const SignInCard: React.FC = () => (
  <div className="stack-sm">
    <strong>Your session has expired</strong>
    <p className="muted mb-0">Please sign in again. Your conversation will still be here.</p>
    <div>
      <button type="button" className="btn btn-primary" onClick={() => { clearStoredTokens(); window.location.reload(); }}>
        Sign in again
      </button>
    </div>
  </div>
);
