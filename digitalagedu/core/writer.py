import errno
import time
from pathlib import Path


class FileWriter:
    def write(self, content: str, output_path: str):
        path = Path(output_path)
        # Ensure output directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file with encoding
        path.write_text(content, encoding="utf-8")

        print(f"Generated file at {path.resolve()}")


def retry_eio(save, path, attempts=3, wait_s=5):
    """Runs save(path), retrying when Expanse's Lustre scratch fails the write with EIO (Errno 5); run
    f53b2469 lost all 4 Phase 2 weeks to it. save must rewrite the whole file, replacing any partial one."""
    for attempt in range(1, attempts + 1):
        try:
            return save(path)
        except OSError as err:
            if err.errno != errno.EIO or attempt == attempts:
                raise
            print(f"[WARN] I/O error saving {path} (attempt {attempt}/{attempts}); retrying in {wait_s}s")
            time.sleep(wait_s)


def write_file(path, fill, newline=None, **retry_kwargs):
    """Opens path for UTF-8 text writing, calls fill(f), and retries the whole write on EIO (see retry_eio)."""
    def save(p):
        with open(p, "w", encoding="utf-8", newline=newline) as f:
            fill(f)
    retry_eio(save, path, **retry_kwargs)
