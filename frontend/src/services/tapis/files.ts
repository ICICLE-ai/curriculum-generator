import { getTapisApiUrl, getTapisHeaders } from './client';
import { cleanTapisUsername, sanitizeTapisName } from '../../utils/format';
import type { TapisFileItem, TapisDatasetItem, TapisSystem } from './types';

export const TAPIS_CONFIGS_DIR = 'smart_curriculum_designer_configs';
export const TAPIS_DATASETS_DIR = 'smart_curriculum_designer_datasets';
export const TAPIS_ARCHIVES_DIR = 'smart_curriculum_designer_archives';
const EXPANSE_SHARED_DATASETS_DIR = 'shared/smart_curriculum_designer_datasets';

const cachedSystemRootDir: Record<string, string> = {};

/**
 * Dynamically fetch the system's root directory directly from Tapis Systems API
 * (e.g. GET /v3/systems/{systemId})
 */
export async function fetchSystemRootDir(token: string, systemId = 'expanse-tapis-static'): Promise<string> {
  if (cachedSystemRootDir[systemId]) {
    return cachedSystemRootDir[systemId];
  }
  try {
    const url = getTapisApiUrl(`/v3/systems/${systemId}`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: getTapisHeaders(token),
    });
    if (resp.ok) {
      const data = await resp.json();
      let rootDir: string = data.result?.rootDir || '';
      if (rootDir && !rootDir.endsWith('/')) {
        rootDir += '/';
      }
      if (rootDir) {
        cachedSystemRootDir[systemId] = rootDir;
        return rootDir;
      }
    }
  } catch (err) {
    console.warn(`[Tapis] Failed to query system info for ${systemId}:`, err);
  }
  return '';
}

/**
 * Fetch list of files in the user's smart_curriculum_designer_configs folder
 * with fallback to user root if folder doesn't exist yet.
 */
export async function fetchUserConfigFiles(
  token: string,
  username: string,
  systemId = 'expanse-tapis-static'
): Promise<TapisFileItem[]> {
  try {
    const rootDir = await fetchSystemRootDir(token, systemId);
    const cleanUser = cleanTapisUsername(username);
    
    // First try user's smart_curriculum_designer_configs folder
    const configsFolderUrl = getTapisApiUrl(`/v3/files/ops/${systemId}/users/${cleanUser}/${TAPIS_CONFIGS_DIR}`);
    let resp = await fetch(configsFolderUrl, {
      method: 'GET',
      headers: getTapisHeaders(token),
    });

    let files: any[] = [];
    if (resp.ok) {
      const data = await resp.json();
      files = data.result || [];
    } else {
      // Fallback to user root directory
      const userRootUrl = getTapisApiUrl(`/v3/files/ops/${systemId}/users/${cleanUser}`);
      resp = await fetch(userRootUrl, {
        method: 'GET',
        headers: getTapisHeaders(token),
      });
      if (resp.ok) {
        const data = await resp.json();
        files = data.result || [];
      }
    }

    return files
      .filter((f) => f.name.endsWith('.yaml') || f.name.endsWith('.yml'))
      .map((f) => {
        const cleanPath = (f.path || '').replace(/^\/+/, '');
        return {
          name: f.name,
          path: f.path,
          clusterPath: rootDir ? `${rootDir}${cleanPath}` : `/${cleanPath}`,
          size: f.size,
          lastModified: f.lastModified,
          type: f.type,
        };
      });
  } catch (err) {
    console.warn('[Tapis] Could not fetch user config files:', err);
    return [];
  }
}

/**
 * Upload / export a generated YAML configuration directly to the user's
 * smart_curriculum_designer_configs folder in Tapis storage.
 */
export async function exportConfigToTapis(
  token: string,
  username: string,
  filename: string,
  yamlContent: string,
  systemId = 'expanse-tapis-static'
): Promise<{ path: string; clusterPath: string }> {
  const cleanUser = username.includes('@') ? username.split('@')[0] : username;
  const rootDir = await fetchSystemRootDir(token, systemId);

  // Ensure clean filename ending in .yaml
  let safeName = sanitizeTapisName(filename);
  if (!safeName.endsWith('.yaml') && !safeName.endsWith('.yml')) {
    safeName += '.yaml';
  }

  // Create multipart/form-data payload with file
  const blob = new Blob([yamlContent], { type: 'text/yaml' });
  const formData = new FormData();
  formData.append('file', blob, safeName);

  const targetPath = `users/${cleanUser}/${TAPIS_CONFIGS_DIR}/${safeName}`;
  const uploadUrl = getTapisApiUrl(`/v3/files/ops/${systemId}/${targetPath}`);

  const resp = await fetch(uploadUrl, {
    method: 'POST',
    headers: {
      'X-Tapis-Token': token.trim(),
    },
    body: formData,
  });

  if (!resp.ok) {
    const errorText = await resp.text();
    throw new Error(`Failed to upload config to Tapis (${resp.status}): ${errorText}`);
  }

  const clusterPath = rootDir ? `${rootDir}${targetPath}` : `/${targetPath}`;
  return {
    path: targetPath,
    clusterPath,
  };
}

/**
 * Fetch archived Phase 1 job directories from the user's smart_curriculum_designer_archives folder.
 */
export async function fetchUserPhase1Archives(
  token: string,
  username: string,
  systemId = 'expanse-tapis-static'
): Promise<TapisFileItem[]> {
  try {
    const cleanUser = cleanTapisUsername(username);
    if (!cleanUser || cleanUser === 'Authorized User') return [];

    const rootDir = await fetchSystemRootDir(token, systemId);
    const archivesUrl = getTapisApiUrl(
      `/v3/files/ops/${systemId}/users/${cleanUser}/${TAPIS_ARCHIVES_DIR}`
    );
    const resp = await fetch(archivesUrl, {
      method: 'GET',
      headers: getTapisHeaders(token),
    });

    if (!resp.ok) {
      return [];
    }

    const data = await resp.json();
    const items: any[] = data.result || [];
    return items
      .filter((f) => f.type === 'dir')
      .map((f) => {
        const cleanPath = (f.path || '').replace(/^\/+/, '');
        return {
          name: f.name,
          path: f.path,
          clusterPath: rootDir ? `${rootDir}${cleanPath}` : `/${cleanPath}`,
          size: f.size,
          lastModified: f.lastModified,
          type: f.type,
        };
      })
      .sort((a, b) => {
        const timeA = a.lastModified ? Date.parse(a.lastModified) : 0;
        const timeB = b.lastModified ? Date.parse(b.lastModified) : 0;
        if (timeA !== timeB) return timeB - timeA;
        return a.name.localeCompare(b.name);
      });
  } catch (err) {
    console.warn('[Tapis] Could not fetch user Phase 1 archives:', err);
    return [];
  }
}

/**
 * Fetch available datasets by querying the shared datasets folder and
 * the user's smart_curriculum_designer_datasets folder (and user root).
 */
export async function fetchAvailableDatasets(
  token: string,
  username?: string,
  systemId = 'expanse-tapis-static'
): Promise<TapisDatasetItem[]> {
  const rootDir = await fetchSystemRootDir(token, systemId);
  const datasets: TapisDatasetItem[] = [];

  // 1. Scan shared smart curriculum designer datasets folder
  try {
    const url = getTapisApiUrl(`/v3/files/ops/${systemId}/${EXPANSE_SHARED_DATASETS_DIR}`);
    const resp = await fetch(url, {
      method: 'GET',
      headers: getTapisHeaders(token),
    });
    if (resp.ok) {
      const data = await resp.json();
      const items: any[] = data.result || [];
      for (const item of items) {
        if (item.type === 'dir' || !item.name.includes('.')) {
          const cleanItemPath = (item.path || '').replace(/^\/+/, '');
          const fullClusterPath = rootDir ? `${rootDir}${cleanItemPath}` : `/${cleanItemPath}`;
          datasets.push({
            name: item.name,
            path: item.path,
            clusterPath: fullClusterPath,
            type: item.type,
            source: 'shared',
          });
        }
      }
    }
  } catch (err) {
    console.warn('[Tapis] Could not scan shared datasets folder:', err);
  }

  // 2. Scan user's smart_curriculum_designer_datasets folder first
  if (username && username !== 'Authorized User') {
    const cleanUser = cleanTapisUsername(username);
    
    try {
      const userDatasetsUrl = getTapisApiUrl(`/v3/files/ops/${systemId}/users/${cleanUser}/${TAPIS_DATASETS_DIR}`);
      const resp = await fetch(userDatasetsUrl, {
        method: 'GET',
        headers: getTapisHeaders(token),
      });
      if (resp.ok) {
        const data = await resp.json();
        const items: any[] = data.result || [];
        for (const item of items) {
          const cleanItemPath = (item.path || '').replace(/^\/+/, '');
          const fullClusterPath = rootDir ? `${rootDir}${cleanItemPath}` : `/${cleanItemPath}`;
          datasets.push({
            name: item.name,
            path: item.path,
            clusterPath: fullClusterPath,
            type: item.type,
            source: 'user',
          });
        }
      }
    } catch {
      // Continue to check root
    }

    // Also scan user root for any directories with "data" in name
    try {
      const url = getTapisApiUrl(`/v3/files/ops/${systemId}/users/${cleanUser}`);
      const resp = await fetch(url, {
        method: 'GET',
        headers: getTapisHeaders(token),
      });
      if (resp.ok) {
        const data = await resp.json();
        for (const item of (data.result || [])) {
          if (
            item.type === 'dir' &&
            item.name !== TAPIS_DATASETS_DIR &&
            item.name !== TAPIS_CONFIGS_DIR &&
            item.name !== TAPIS_ARCHIVES_DIR &&
            (item.name.toLowerCase().includes('data') || item.name.toLowerCase().includes('dataset'))
          ) {
            const cleanItemPath = (item.path || '').replace(/^\/+/, '');
            const fullClusterPath = rootDir ? `${rootDir}${cleanItemPath}` : `/${cleanItemPath}`;
            datasets.push({
              name: item.name,
              path: item.path,
              clusterPath: fullClusterPath,
              type: item.type,
              source: 'user',
            });
          }
        }
      }
    } catch (err) {
      console.warn('[Tapis] Could not scan user datasets folder:', err);
    }
  }

  return datasets;
}

/**
 * List all enabled Tapis systems visible to the current user.
 */
export async function fetchAccessibleSystems(token: string): Promise<TapisSystem[]> {
  const url = getTapisApiUrl(
    '/v3/systems?listType=ALL&select=id,host,systemType,rootDir,canExec,enabled,owner'
  );
  const resp = await fetch(url, {
    method: 'GET',
    headers: getTapisHeaders(token),
  });

  if (!resp.ok) {
    const errText = await resp.text().catch(() => '');
    throw new Error(`Failed to fetch Tapis systems (${resp.status}): ${errText}`);
  }

  const data = await resp.json();
  const systems: TapisSystem[] = (data.result || []).filter(
    (s: TapisSystem) => s.enabled !== false
  );
  return systems.sort((a, b) => a.id.localeCompare(b.id));
}

/**
 * List files and directories at a given path on any accessible Tapis system.
 */
export async function listSystemFiles(
  token: string,
  systemId: string,
  subpath = ''
): Promise<TapisFileItem[]> {
  const cleanSubpath = subpath
    .split('/')
    .filter(Boolean)
    .map((seg) => encodeURIComponent(seg))
    .join('/');

  const urlPath = cleanSubpath
    ? `/v3/files/ops/${encodeURIComponent(systemId)}/${cleanSubpath}`
    : `/v3/files/ops/${encodeURIComponent(systemId)}/`;

  const resp = await fetch(getTapisApiUrl(urlPath), {
    method: 'GET',
    headers: getTapisHeaders(token),
  });

  if (!resp.ok) {
    if (resp.status === 401 || resp.status === 403) {
      throw new Error(`Access denied or missing Tapis credentials for "${systemId}".`);
    }
    if (resp.status === 404) {
      throw new Error(`Path not found on "${systemId}": /${subpath.replace(/^\/+/, '')}`);
    }
    const errText = await resp.text().catch(() => '');
    throw new Error(`Could not list "${systemId}" (${resp.status}): ${errText.slice(0, 200)}`);
  }

  const data = await resp.json();
  const rawItems: any[] = data.result || [];
  const items: TapisFileItem[] = rawItems
    .filter((f) => f.name && f.name !== '.' && f.name !== '..')
    .map((f) => ({
      name: f.name,
      path: f.path || (subpath ? `${subpath.replace(/\/+$/, '')}/${f.name}` : f.name),
      size: f.size,
      lastModified: f.lastModified,
      type: f.type,
    }));

  return items.sort((a, b) => {
    if (a.type === 'dir' && b.type !== 'dir') return -1;
    if (a.type !== 'dir' && b.type === 'dir') return 1;
    return a.name.localeCompare(b.name);
  });
}

/**
 * Upload an arbitrary file blob directly to a specific target path on Tapis storage.
 */
export async function uploadRawFileToTapis(
  token: string,
  targetRelativePath: string,
  filename: string,
  blob: Blob,
  systemId = 'expanse-tapis-static'
): Promise<void> {
  const cleanPath = targetRelativePath.replace(/^\/+/, '').replace(/\/+$/, '');
  const uploadUrl = getTapisApiUrl(`/v3/files/ops/${systemId}/${cleanPath}/${filename}`);

  const formData = new FormData();
  formData.append('file', blob, filename);

  const resp = await fetch(uploadUrl, {
    method: 'POST',
    headers: {
      'X-Tapis-Token': token.trim(),
    },
    body: formData,
  });

  if (!resp.ok) {
    const errorText = await resp.text();
    throw new Error(`Failed to upload ${filename} (${resp.status}): ${errorText}`);
  }
}
