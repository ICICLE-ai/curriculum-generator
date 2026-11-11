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
# Ways to run LibreOffice, tried in order until one renders. Saving the PDF failed with 0x507 Io Access in the job's
# Lustre folder (runs 0ffa9ff2, f73310e1, ee09eaac) and in the node's /tmp (49088b7e), and it cannot be tested by
# hand on Expanse, so the first run's log names the mode that works (or every mode's error):
#   job_folder_tmpdir: profile, PDF and LibreOffice's temp files in the job folder; job_folder: same but the default
#   TMPDIR; node_tmp: deck, profile, temp files and PDF all in a fresh folder in the node's /tmp (PNGs still go to out_dir)
# job_folder_tmpdir goes first: job_folder crashed (exit 134) on every week's first render in run 87a6f1f8
RENDER_MODES = ("job_folder_tmpdir", "job_folder", "node_tmp")
# Once a mode has rendered, a failure is one slow or stuck render (a 45 s timeout in run 87a6f1f8 used to end every
# later review of that week): only that slide's screenshot is skipped, until this many fail in a row
MAX_CONSECUTIVE_FAILURES = 3
_disabled_reason = None  # set when rendering is given up: every mode failed, or the working one kept failing
_mode = None  # the first mode that rendered in this process; later renders use only it
_profiles = {}  # one LibreOffice profile per mode and process, so only the first render pays the start-up cost
_failures = 0  # failed renders in a row since the last success


def render_deck_pngs(pptx_path: str, out_dir: str, dpi: int = 72) -> List[str]:
    """PNG paths in slide order; [] when LibreOffice or pdftoppm is missing (e.g. local dev) or rendering fails,
    so callers skip the visual review instead of failing the deck."""
    global _disabled_reason, _mode, _failures
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if _disabled_reason or not soffice or not shutil.which("pdftoppm"):
        return []
    errors = []
    for mode in ([_mode] if _mode else RENDER_MODES):
        try:
            pngs = _render(soffice, mode, pptx_path, out_dir, dpi)
        except (subprocess.SubprocessError, OSError) as err:
            output = b" ".join(x for x in (getattr(err, "stdout", None), getattr(err, "stderr", None)) if x)
            errors.append(f"[{mode}] {err} | output: {output.decode(errors='replace')[-600:]}")
            # A timed-out run's soffice.bin can outlive the killed launcher and keep its profile locked;
            # the next render starts a fresh one (with the cold-start timeout).
            # shortcut: the stray process itself is left running; kill its process group if strays pile up on nodes
            _profiles.pop(mode, None)
            continue
        if _mode is None:
            logger.warning(f"Slide rendering works in mode '{mode}'" + (f" after: {' || '.join(errors)}" if errors else ""))
        _mode, _failures = mode, 0
        return pngs
    if _mode:
        _failures += 1
        if _failures < MAX_CONSECUTIVE_FAILURES:
            logger.warning(f"Slide rendering failed ({_failures} in a row); skipping this slide's screenshot review: "
                           + " || ".join(errors))
            return []
    _disabled_reason = " || ".join(errors)
    logger.warning(f"Slide rendering failed; screenshot review disabled for this run (geometry checks continue): {_disabled_reason}")
    return []


def _render(soffice: str, mode: str, pptx_path: str, out_dir: str, dpi: int) -> List[str]:
    node_tmp = mode == "node_tmp"
    profile = _profiles.get(mode)
    first = profile is None or not os.path.isdir(profile)
    if first:
        # A private profile per process: week workers render at once and would block each other on a shared one
        profile = _profiles[mode] = tempfile.mkdtemp(prefix="lo_profile_", dir=None if node_tmp else out_dir)
    # Under Singularity HOME and /run/user are read-only or shared; LibreOffice writes config and dconf state
    # there even with a private profile
    env = {**os.environ, "HOME": profile, "XDG_RUNTIME_DIR": profile}
    if mode != "job_folder":
        env["TMPDIR"] = profile
    src, pdf_dir = pptx_path, out_dir
    if node_tmp:
        pdf_dir = os.path.join(profile, "render")
        os.makedirs(pdf_dir, exist_ok=True)
        src = shutil.copy(pptx_path, pdf_dir)
    subprocess.run([soffice, f"-env:UserInstallation=file://{profile}", "--headless", "--norestore",
                    "--convert-to", "pdf", "--outdir", pdf_dir, src],
                   check=True, timeout=FIRST_SOFFICE_TIMEOUT_S if first else SOFFICE_TIMEOUT_S, capture_output=True, env=env)
    pdf = os.path.join(pdf_dir, os.path.splitext(os.path.basename(pptx_path))[0] + ".pdf")
    prefix = os.path.join(out_dir, "slide")
    for old in glob.glob(prefix + "-*.png"):
        os.remove(old)
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, prefix], check=True, timeout=120, capture_output=True)
    # pdftoppm names pages slide-1.png or slide-01.png depending on page count; sort by the number
    return sorted(glob.glob(prefix + "-*.png"), key=lambda p: int(p.rsplit("-", 1)[1][:-4]))
