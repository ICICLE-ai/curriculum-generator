import React, { useEffect, useState } from 'react';
import { extractAndUploadArchive } from '../../utils/archiveExtractor';
import { sanitizeTapisName } from '../../utils/format';
import { fetchSystemRootDir, uploadRawFileToTapis, TAPIS_DATASETS_DIR } from '../../services/tapis';
import { setDataset } from '../../utils/assistant/draft';
import type { CurriculumAgent } from '../../utils/assistant/types';
import { useSession } from './session';

const IMAGE_EXT = /\.(jpe?g|png|tiff?|bmp|webp)$/i;
const folderAttr = { webkitdirectory: '' } as object; // not in React's typings

export const UploadCard: React.FC<{ agent: CurriculumAgent }> = ({ agent }) => {
  const { token, username } = useSession();
  const [root, setRoot] = useState('');
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  useEffect(() => {
    if (token) fetchSystemRootDir(token).then(setRoot);
  }, [token]);

  const run = async (job: () => Promise<{ path: string; note: string }>) => {
    setBusy(true);
    setError(null);
    try {
      const { path, note } = await job();
      agent.editDraft((d) => setDataset(d, path), note);
      setDone(note);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed.');
    } finally {
      setBusy(false);
      setProgress('');
    }
  };

  const onArchive = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file || !token) return;
    const folder = sanitizeTapisName(file.name.replace(/\.(zip|tar|gz|tgz)$/i, ''), { allowDots: false });
    run(async () => ({
      path: await extractAndUploadArchive({
        archiveData: file, archiveName: file.name, datasetFolderName: folder,
        token, username, systemRootDir: root, onProgress: setProgress,
      }),
      note: `Uploaded dataset "${folder}"`,
    }));
  };

  const onFolder = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []).filter((f) => IMAGE_EXT.test(f.name));
    e.target.value = '';
    if (!token) return;
    run(async () => {
      if (!files.length) throw new Error('No photos (.jpg, .png, ...) were found in that folder.');
      const folder = sanitizeTapisName(files[0].webkitRelativePath.split('/')[0], { allowDots: false });
      const base = `users/${username}/${TAPIS_DATASETS_DIR}/${folder}`;
      const classes = new Set<string>();
      let next = 0;
      let uploaded = 0;
      const worker = async () => {
        while (next < files.length) {
          const f = files[next++];
          const parts = f.webkitRelativePath.split('/').slice(1); // drop the folder itself
          parts.pop();
          if (parts[0]) classes.add(parts[0]);
          await uploadRawFileToTapis(token, parts.length ? `${base}/${parts.join('/')}` : base, f.name, f);
          setProgress(`Uploaded ${++uploaded} of ${files.length} photos...`);
        }
      };
      await Promise.all([worker(), worker(), worker(), worker()]);
      return {
        path: root ? `${root}${base}` : `/${base}`,
        note: `Uploaded dataset "${folder}" (${files.length} images in ${classes.size} class folders)`,
      };
    });
  };

  if (done) return <p className="assistant-note">{done}. Done.</p>;

  return (
    <div className="stack-sm">
      <strong>Upload your photos</strong>
      <p className="muted mb-0">Pick a folder with one sub-folder per category (best for big sets), or a .zip / .tar.gz file under 1.5 GB.</p>
      <div className="row-wrap">
        <label className={`btn btn-primary ${busy ? 'is-disabled' : ''}`}>
          Choose a folder
          <input type="file" multiple {...folderAttr} onChange={onFolder} disabled={busy} className="assistant-file" />
        </label>
        <label className={`btn btn-secondary ${busy ? 'is-disabled' : ''}`}>
          Choose a zip file
          <input type="file" accept=".zip,.tar,.gz,.tgz" onChange={onArchive} disabled={busy} className="assistant-file" />
        </label>
      </div>
      {progress && <div className="alert alert-info">{progress}</div>}
      {error && <div role="alert" className="alert alert-error">{error}</div>}
    </div>
  );
};
