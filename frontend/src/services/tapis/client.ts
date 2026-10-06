export function getTapisApiUrl(path: string): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // In local development, use the Vite dev proxy
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return cleanPath;
    }
  }
  // When deployed on Tapis Pods or any remote host, target Tapis API directly
  return `https://icicleai.tapis.io${cleanPath}`;
}

export function getTapisHeaders(token: string) {
  return {
    'X-Tapis-Token': token.trim(),
    'Content-Type': 'application/json',
  };
}

