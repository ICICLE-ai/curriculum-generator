"""Renders a deck to one PNG per slide (LibreOffice -> PDF -> pdftoppm) so a vision model can review the slides."""
import glob
import logging
import os
import shutil
import subprocess
import tempfile
from typing import List

logger = logging.getLogger(__name__)


def render_deck_pngs(pptx_path: str, out_dir: str, dpi: int = 72) -> List[str]:
    """PNG paths in slide order; [] when LibreOffice or pdftoppm is missing (e.g. local dev) or rendering fails,
    so callers skip the visual review instead of failing the deck."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice or not shutil.which("pdftoppm"):
        return []
    profile = tempfile.mkdtemp(prefix="lo_profile_")  # a private profile: concurrent or stale soffice runs block each other
    try:
        subprocess.run([soffice, f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", "pdf",
                        "--outdir", out_dir, pptx_path], check=True, timeout=180, capture_output=True)
        pdf = os.path.join(out_dir, os.path.splitext(os.path.basename(pptx_path))[0] + ".pdf")
        prefix = os.path.join(out_dir, "slide")
        for old in glob.glob(prefix + "-*.png"):
            os.remove(old)
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, prefix], check=True, timeout=120, capture_output=True)
        # pdftoppm names pages slide-1.png or slide-01.png depending on page count; sort by the number
        return sorted(glob.glob(prefix + "-*.png"), key=lambda p: int(p.rsplit("-", 1)[1][:-4]))
    except (subprocess.SubprocessError, OSError) as err:
        logger.warning(f"Slide rendering failed, skipping visual review: {err}")
        return []
    finally:
        shutil.rmtree(profile, ignore_errors=True)
