import JSZip from 'jszip';
import * as fflate from 'fflate';
import { uploadRawFileToTapis, TAPIS_DATASETS_DIR } from '../services/tapis';

export interface ExtractedFile {
  relativePath: string;
  blob: Blob;
}

/**
 * Parse ustar / standard tar format in browser
 */
export function parseTarBuffer(buffer: Uint8Array): { name: string; data: Uint8Array }[] {
  const files: { name: string; data: Uint8Array }[] = [];
  let offset = 0;

  while (offset < buffer.length - 512) {
    const header = buffer.subarray(offset, offset + 512);
    if (header[0] === 0) break;

    let name = '';
    for (let i = 0; i < 100; i++) {
      if (header[i] === 0) break;
      name += String.fromCharCode(header[i]);
    }

    // Support ustar prefix if present
    let prefix = '';
    for (let i = 345; i < 500; i++) {
      if (header[i] === 0) break;
      prefix += String.fromCharCode(header[i]);
    }
    if (prefix) {
      name = `${prefix}/${name}`;
    }

    let sizeStr = '';
    for (let i = 124; i < 136; i++) {
      if (header[i] === 0 || header[i] === 32) break;
      sizeStr += String.fromCharCode(header[i]);
    }
    const size = parseInt(sizeStr, 8) || 0;
    const type = String.fromCharCode(header[156]);
    offset += 512;

    if (size > 0 && (type === '0' || type === '\0')) {
      const data = buffer.subarray(offset, offset + size);
      files.push({ name, data });
    }
    offset += Math.ceil(size / 512) * 512;
  }
  return files;
}

/**
 * Extract files from any supported archive format (ZIP, TAR, GZ, TGZ) in-memory
 */
export async function extractArchiveFiles(
  archiveData: ArrayBuffer | Blob,
  archiveName: string,
  onProgress: (msg: string) => void
): Promise<ExtractedFile[]> {
  onProgress('Reading archive in memory...');
  const arrayBuffer = archiveData instanceof Blob ? await archiveData.arrayBuffer() : archiveData;
  const bytes = new Uint8Array(arrayBuffer);
  const validExtensions = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.webp'];

  const isZip =
    archiveName.toLowerCase().endsWith('.zip') ||
    (bytes[0] === 0x50 && bytes[1] === 0x4b);

  const isGzip =
    archiveName.toLowerCase().endsWith('.gz') ||
    archiveName.toLowerCase().endsWith('.tgz') ||
    (bytes[0] === 0x1f && bytes[1] === 0x8b);

  const isTar =
    archiveName.toLowerCase().endsWith('.tar') ||
    (!isZip && !isGzip && bytes.length > 512);

  if (isZip) {
    onProgress('Extracting ZIP entries...');
    const zip = await JSZip.loadAsync(arrayBuffer);
    const results: ExtractedFile[] = [];

    const entries: { relPath: string; entry: JSZip.JSZipObject }[] = [];
    zip.forEach((relPath, entry) => {
      if (!entry.dir && !relPath.startsWith('__MACOSX') && !relPath.includes('/.')) {
        const lower = relPath.toLowerCase();
        if (validExtensions.some((ext) => lower.endsWith(ext))) {
          entries.push({ relPath, entry });
        }
      }
    });

    for (const { relPath, entry } of entries) {
      const blob = await entry.async('blob');
      results.push({ relativePath: relPath, blob });
    }
    return results;
  }

  if (isGzip) {
    onProgress('Decompressing GZIP stream...');
    let decompressedBytes: Uint8Array;
    try {
      decompressedBytes = fflate.gunzipSync(bytes);
    } catch (err) {
      throw new Error(`Failed to decompress GZIP archive: ${err instanceof Error ? err.message : String(err)}`);
    }

    // Check if decompressed payload is a TAR archive
    const isInnerTar =
      archiveName.toLowerCase().endsWith('.tar.gz') ||
      archiveName.toLowerCase().endsWith('.tgz') ||
      decompressedBytes.length > 512;

    if (isInnerTar) {
      onProgress('Unpacking inner TAR filesystem...');
      const tarFiles = parseTarBuffer(decompressedBytes);
      const results: ExtractedFile[] = [];
      for (const f of tarFiles) {
        const lower = f.name.toLowerCase();
        if (validExtensions.some((ext) => lower.endsWith(ext))) {
          results.push({
            relativePath: f.name,
            blob: new Blob([f.data as unknown as BlobPart]),
          });
        }
      }
      return results;
    } else {
      // Standalone decompressed file
      const cleanName = archiveName.replace(/\.gz$/i, '');
      return [
        {
          relativePath: cleanName,
          blob: new Blob([decompressedBytes as unknown as BlobPart]),
        },
      ];
    }
  }

  if (isTar) {
    onProgress('Unpacking TAR archive...');
    const tarFiles = parseTarBuffer(bytes);
    const results: ExtractedFile[] = [];
    for (const f of tarFiles) {
      const lower = f.name.toLowerCase();
      if (validExtensions.some((ext) => lower.endsWith(ext))) {
        results.push({
          relativePath: f.name,
          blob: new Blob([f.data as unknown as BlobPart]),
        });
      }
    }
    return results;
  }

  throw new Error('Unsupported format. Please upload a .zip, .tar, .tar.gz, or .tgz archive.');
}

export interface ExtractAndUploadOptions {
  archiveData: ArrayBuffer | Blob;
  archiveName: string;
  datasetFolderName: string;
  token: string;
  username: string;
  systemRootDir?: string;
  onProgress: (msg: string) => void;
}

/**
 * Helper to extract and stream archive contents directly to a Tapis directory
 */
export async function extractAndUploadArchive({
  archiveData,
  archiveName,
  datasetFolderName,
  token,
  username,
  systemRootDir = '',
  onProgress,
}: ExtractAndUploadOptions): Promise<string> {
  const cleanUsername = username.includes('@') ? username.split('@')[0] : username;
  if (!token || !cleanUsername) {
    throw new Error('You must be logged in to upload datasets.');
  }

  const fileEntries = await extractArchiveFiles(archiveData, archiveName, onProgress);

  if (fileEntries.length === 0) {
    throw new Error('Archive contains no supported image files (.jpg, .png, .tif, etc.).');
  }

  // Determine common root prefix if archive was packaged with a root wrapper folder
  let commonPrefix = '';
  const firstParts = fileEntries[0].relativePath.split('/');
  if (firstParts.length > 2) {
    const candidatePrefix = firstParts[0] + '/';
    const allShare = fileEntries.every((e) => e.relativePath.startsWith(candidatePrefix));
    if (allShare) {
      commonPrefix = candidatePrefix;
    }
  }

  onProgress(`Extracted ${fileEntries.length} images. Streaming directly to Tapis storage...`);

  const cleanFolder = datasetFolderName.replace(/[^a-zA-Z0-9_-]/g, '_');
  const baseTargetDir = `users/${cleanUsername}/${TAPIS_DATASETS_DIR}/${cleanFolder}`;

  let uploadedCount = 0;
  const batchSize = 4; // Concurrent upload streams

  for (let i = 0; i < fileEntries.length; i += batchSize) {
    const chunk = fileEntries.slice(i, i + batchSize);
    await Promise.all(
      chunk.map(async ({ relativePath, blob }) => {
        let cleanRelative = relativePath;
        if (commonPrefix && cleanRelative.startsWith(commonPrefix)) {
          cleanRelative = cleanRelative.slice(commonPrefix.length);
        }

        const parts = cleanRelative.split('/');
        const filename = parts.pop()!;
        const subDir = parts.join('/');
        const targetDir = subDir ? `${baseTargetDir}/${subDir}` : baseTargetDir;

        await uploadRawFileToTapis(token, targetDir, filename, blob);
        uploadedCount++;
      })
    );
    onProgress(`Uploaded ${uploadedCount} / ${fileEntries.length} images to Tapis...`);
  }

  const clusterPath = systemRootDir
    ? `${systemRootDir}${baseTargetDir}`
    : `/${baseTargetDir}`;

  return clusterPath;
}

