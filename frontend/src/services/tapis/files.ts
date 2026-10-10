import { getTapisApiUrl, getTapisHeaders } from './client';
import type { TapisFileItem, TapisDatasetItem } from './types';

export const TAPIS_CONFIGS_DIR = 'smart_curriculum_designer_configs';
export const TAPIS_DATASETS_DIR = 'smart_curriculum_designer_datasets';
export const EXPANSE_SHARED_DATASETS_DIR = 'shared/smart_curriculum_designer_datasets';

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
    const cleanUser = username.includes('@') ? username.split('@')[0] : username;
    
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
  let safeName = filename.trim().replace(/[^a-zA-Z0-9_\-.]/g, '_');
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
      headers: getHeaders(token),
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
    const cleanUser = username.includes('@') ? username.split('@')[0] : username;
    
    try {
      const userDatasetsUrl = getTapisApiUrl(`/v3/files/ops/${systemId}/users/${cleanUser}/${TAPIS_DATASETS_DIR}`);
      const resp = await fetch(userDatasetsUrl, {
        method: 'GET',
        headers: getHeaders(token),
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
        headers: getHeaders(token),
      });
      if (resp.ok) {
        const data = await resp.json();
        for (const item of (data.result || [])) {
          if (
            item.type === 'dir' &&
            item.name !== TAPIS_DATASETS_DIR &&
            item.name !== TAPIS_CONFIGS_DIR &&
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

function getHeaders(token: string) {
  return getTapisHeaders(token);
}

/**
 * Upload a local dataset archive file (.zip, .tar.gz, etc.) directly into the user's
 * smart_curriculum_designer_datasets folder in Tapis storage.
 */
export async function uploadDatasetFileToTapis(
  token: string,
  username: string,
  file: File,
  customName?: string,
  systemId = 'expanse-tapis-static'
): Promise<{ path: string; clusterPath: string; filename: string }> {
  const cleanUser = username.includes('@') ? username.split('@')[0] : username;
  const rootDir = await fetchSystemRootDir(token, systemId);

  let safeName = (customName || file.name).trim().replace(/[^a-zA-Z0-9_\-.]/g, '_');
  if (!safeName) {
    safeName = `dataset_${Date.now()}.zip`;
  }

  const formData = new FormData();
  formData.append('file', file, safeName);

  const targetPath = `users/${cleanUser}/${TAPIS_DATASETS_DIR}/${safeName}`;
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
    throw new Error(`Failed to upload dataset file (${resp.status}): ${errorText}`);
  }

  const clusterPath = rootDir ? `${rootDir}${targetPath}` : `/${targetPath}`;
  return {
    path: targetPath,
    clusterPath,
    filename: safeName,
  };
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

/**
 * Delete a file or directory from Tapis storage.
 */
export async function deleteTapisPath(
  token: string,
  targetRelativePath: string,
  systemId = 'expanse-tapis-static'
): Promise<void> {
  const cleanPath = targetRelativePath.replace(/^\/+/, '');
  const deleteUrl = getTapisApiUrl(`/v3/files/ops/${systemId}/${cleanPath}`);

  const resp = await fetch(deleteUrl, {
    method: 'DELETE',
    headers: {
      'X-Tapis-Token': token.trim(),
    },
  });

  if (!resp.ok && resp.status !== 404) {
    console.warn(`[Tapis] Delete ${cleanPath} returned status ${resp.status}`);
  }
}
