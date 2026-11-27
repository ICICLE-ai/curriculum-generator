import { getTapisApiUrl, getTapisHeaders } from './client';
import { TAPIS_DATASETS_DIR } from './files';
import type { TapisTransferResponse } from './types';

/**
 * Trigger an asynchronous server-to-server URL transfer via Tapis Transfers API
 * directly into the user's smart_curriculum_designer_datasets folder.
 */
export async function createTapisDatasetTransfer(
  token: string,
  username: string,
  sourceUrl: string,
  targetFilename: string,
  systemId = 'expanse-tapis-static'
): Promise<TapisTransferResponse> {
  const cleanUser = username.includes('@') ? username.split('@')[0] : username;
  let safeName = targetFilename.trim().replace(/[^a-zA-Z0-9_\-.]/g, '_');
  if (!safeName) {
    safeName = `dataset_${Date.now()}`;
  }

  const destinationURI = `tapis://${systemId}/users/${cleanUser}/${TAPIS_DATASETS_DIR}/${safeName}`;
  const url = getTapisApiUrl('/v3/files/transfers');

  const payload = {
    tag: `dataset-transfer-${safeName}`,
    elements: [
      {
        sourceURI: sourceUrl.trim(),
        destinationURI,
      },
    ],
  };

  const resp = await fetch(url, {
    method: 'POST',
    headers: getTapisHeaders(token),
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    const errorText = await resp.text();
    throw new Error(`Failed to initiate dataset transfer (${resp.status}): ${errorText}`);
  }

  const json = await resp.json();
  const res = json.result || json;
  return {
    uuid: res.uuid || res.id,
    status: res.status || 'ACCEPTED',
    tag: res.tag,
  };
}

/**
 * Trigger a server-to-server Tapis-to-Tapis transfer from any accessible source system
 * into the user's smart_curriculum_designer_datasets folder on the destination system
 * (defaults to expanse-tapis-static).
 */
export async function createTapisToTapisTransfer(
  token: string,
  sourceSystemId: string,
  sourcePath: string,
  username: string,
  targetFolderName: string,
  destSystemId = 'expanse-tapis-static'
): Promise<TapisTransferResponse> {
  const cleanUser = username.includes('@') ? username.split('@')[0] : username;
  let safeName = targetFolderName.trim().replace(/[^a-zA-Z0-9_\-.]/g, '_');
  if (!safeName) {
    safeName = `dataset_${Date.now()}`;
  }

  const cleanSourcePath = sourcePath.replace(/^\/+/, '');
  const sourceURI = cleanSourcePath
    ? `tapis://${sourceSystemId}/${cleanSourcePath}`
    : `tapis://${sourceSystemId}/`;
  const destinationURI = `tapis://${destSystemId}/users/${cleanUser}/${TAPIS_DATASETS_DIR}/${safeName}`;

  const resp = await fetch(getTapisApiUrl('/v3/files/transfers'), {
    method: 'POST',
    headers: getTapisHeaders(token),
    body: JSON.stringify({
      tag: `tapis-sync-${sourceSystemId}-${safeName}`,
      elements: [{ sourceURI, destinationURI }],
    }),
  });

  if (!resp.ok) {
    const errorText = await resp.text().catch(() => '');
    throw new Error(`Failed to start Tapis transfer (${resp.status}): ${errorText}`);
  }

  const json = await resp.json();
  const res = json.result || json;
  return {
    uuid: res.uuid || res.id,
    status: res.status || 'ACCEPTED',
    tag: res.tag,
  };
}

/**
 * Poll the status of an ongoing Tapis Transfer task.
 */
export async function fetchTransferStatus(
  token: string,
  transferUuid: string
): Promise<TapisTransferResponse> {
  const url = getTapisApiUrl(`/v3/files/transfers/${transferUuid}`);
  const resp = await fetch(url, {
    method: 'GET',
    headers: getTapisHeaders(token),
  });

  if (!resp.ok) {
    throw new Error(`Failed to query transfer status (${resp.status})`);
  }

  const json = await resp.json();
  const res = json.result || json;
  return {
    uuid: res.uuid || transferUuid,
    status: res.status,
    tag: res.tag,
    estimatedTotalBytes: res.estimatedTotalBytes,
    totalBytesTransferred: res.totalBytesTransferred,
    errorMessage: res.errorMessage || res.message,
  };
}
