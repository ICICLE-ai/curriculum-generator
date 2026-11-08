"""Renders a deck to one PNG per slide (LibreOffice -> PDF -> pdftoppm) so a vision model can review the slides."""
import glob
import logging
import os
import shutil
import subprocess
import tempfile
from typing import List

logger = logging.getLogger(__name__)

SOFFICE_TIMEOUT_S = 45  # a warm one-slide render; failing ones hung until a 180 s timeout (run 49088b7e)
# LibreOffice's first start builds its profile, which took over 45 s on Lustre and disabled every review (run 0ffa9ff2)
FIRST_SOFFICE_TIMEOUT_S = 180
_disabled_reason = None  # set by the first failed render: every later one would fail the same way
_profile = None  # one LibreOffice profile per process, so only the first render pays the start-up cost


def render_deck_pngs(pptx_path: str, out_dir: str, dpi: int = 72) -> List[str]:
    """PNG paths in slide order; [] when LibreOffice or pdftoppm is missing (e.g. local dev) or rendering fails,
    so callers skip the visual review instead of failing the deck."""
    global _disabled_reason
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if _disabled_reason or not soffice or not shutil.which("pdftoppm"):
        return []
    global _profile
    # A private profile per process (week workers render at once and would block each other on a shared one), kept
    # in the job folder: the node's /tmp was not writable for LibreOffice on Expanse
    first = _profile is None or not os.path.isdir(_profile)
    if first:
        _profile = tempfile.mkdtemp(prefix="lo_profile_", dir=out_dir)
    profile = _profile
    try:
        # Under Singularity HOME and /run/user are read-only or shared; LibreOffice writes config and dconf state
        # there even with a private profile. File locking off: saving the PDF to Lustre failed with 0x507 Io Access
        # even when Lustre was otherwise healthy (runs 0ffa9ff2, f73310e1)
        env = {**os.environ, "HOME": profile, "XDG_RUNTIME_DIR": profile, "SAL_ENABLE_FILE_LOCKING": "0"}
        subprocess.run([soffice, f"-env:UserInstallation=file://{profile}", "--headless", "--norestore",
                        "--convert-to", "pdf", "--outdir", out_dir, pptx_path],
                       check=True, timeout=FIRST_SOFFICE_TIMEOUT_S if first else SOFFICE_TIMEOUT_S, capture_output=True, env=env)
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
