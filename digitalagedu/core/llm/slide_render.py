"""Renders a deck to one PNG per slide (LibreOffice -> PDF -> pdftoppm) so a vision model can review the slides."""
import glob
import logging
import os
import shutil
import subprocess
import tempfile
from typing import List

logger = logging.getLogger(__name__)

SOFFICE_TIMEOUT_S = 45  # a good 16-slide render takes ~10 s; failing ones hung until a 180 s timeout (run 49088b7e)
_disabled_reason = None  # set by the first failed render: every later one would fail the same way, 45 s each


def render_deck_pngs(pptx_path: str, out_dir: str, dpi: int = 72) -> List[str]:
    """PNG paths in slide order; [] when LibreOffice or pdftoppm is missing (e.g. local dev) or rendering fails,
    so callers skip the visual review instead of failing the deck."""
    global _disabled_reason
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if _disabled_reason or not soffice or not shutil.which("pdftoppm"):
        return []
    # A private profile next to the output: concurrent or stale soffice runs block each other, and the node's /tmp
    # was not writable for LibreOffice on Expanse
    profile = tempfile.mkdtemp(prefix="lo_profile_", dir=out_dir)
    try:
        # Under Singularity HOME and /run/user are read-only or shared; LibreOffice writes config and dconf state
        # there even with a private profile
        env = {**os.environ, "HOME": profile, "XDG_RUNTIME_DIR": profile}
        subprocess.run([soffice, f"-env:UserInstallation=file://{profile}", "--headless", "--norestore",
                        "--convert-to", "pdf", "--outdir", out_dir, pptx_path],
                       check=True, timeout=SOFFICE_TIMEOUT_S, capture_output=True, env=env)
        pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(pptx_path))[0] + ".pdf")
        prefix = os.path.join(out_dir, "slide")
        for old in glob.glob(prefix + "-*.png"):
            os.remove(old)
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, prefix], check=True, timeout=120, capture_output=True)
        # pdftoppm names pages slide-1.png or slide-01.png depending on page count; sort by the number
        return sorted(glob.glob(prefix + "-*.png"), key=lambda p: int(p.rsplit("-", 1)[1][:-4]))
    except (subprocess.SubprocessError, OSError) as err:
        output = b" ".join(x for x in (getattr(err, "stdout", None), getattr(err, "stderr", None)) if x)
        _disabled_reason = f"{err} | output: {output.decode(errors='replace')[-800:]}"
        logger.warning(f"Slide rendering failed; screenshot review disabled for this run (geometry checks continue): {_disabled_reason}")
        return []
    finally:
        shutil.rmtree(profile, ignore_errors=True)
