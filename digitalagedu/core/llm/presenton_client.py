import os
import sys
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_PRESENTON_ENDPOINT = "http://localhost:5001"
DEFAULT_PRESENTON_TIMEOUT = 180.0


class PresentonGenerationError(Exception):
    """Raised when Presenton AI presentation generation or export fails."""
    pass


class PresentonClient:
    """
    Headless, synchronous REST client for the self-hosted Presenton AI presentation engine.
    Targets POST /api/v1/ppt/presentation/generate to one-shot slide deck synthesis.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        timeout: float = DEFAULT_PRESENTON_TIMEOUT
    ):
        self.endpoint = (endpoint or os.getenv("PRESENTON_ENDPOINT") or DEFAULT_PRESENTON_ENDPOINT).rstrip("/")
        self.timeout = timeout

    def check_health(self) -> bool:
        """Verifies connectivity to the local Presenton FastAPI daemon."""
        try:
            resp = requests.get(f"{self.endpoint}/", timeout=5.0)
            return resp.status_code < 500
        except Exception:
            return False

    def generate_presentation(
        self,
        content: str,
        output_path: str,
        slides_markdown: Optional[List[str]] = None,
        instructions: Optional[str] = None,
        n_slides: Optional[int] = 5,
        tone: str = "educational",
        verbosity: str = "standard",
        language: str = "English",
        export_as: str = "pptx"
    ) -> str:
        """
        Synchronously requests Presenton to synthesize and export a presentation deck.
        Streams the resulting .pptx binary bytes directly to output_path.
        """
        payload: Dict[str, Any] = {
            "content": content,
            "tone": tone,
            "verbosity": verbosity,
            "language": language,
            "export_as": export_as,
            "include_title_slide": True,
            "include_table_of_contents": False,
            "disable_images": True,
            "image_provider": "none"
        }

        if slides_markdown:
            payload["slides_markdown"] = slides_markdown
        if instructions:
            payload["instructions"] = instructions
        if n_slides:
            payload["n_slides"] = n_slides

        generate_url = f"{self.endpoint}/api/v1/ppt/presentation/generate"
        logger.info(f"Dispatching headless Presenton slide generation to {generate_url} (n_slides={n_slides})...")

        try:
            resp = requests.post(
                generate_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            # Self-healing: if Presenton requires initial auth setup (HTTP 428), bootstrap admin and retry
            if resp.status_code == 428:
                logger.info("Presenton returned 428 (setup required). Bootstrapping local admin and retrying...")
                try:
                    requests.post(
                        f"{self.endpoint}/api/v1/auth/setup",
                        json={"email": "admin@local.host", "password": "AdminPassword123!"},
                        timeout=10.0
                    )
                except Exception as setup_err:
                    logger.warning(f"Presenton auth setup call returned: {setup_err}")

                resp = requests.post(
                    generate_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
        except requests.exceptions.RequestException as e:
            raise PresentonGenerationError(f"Could not connect to Presenton daemon at {generate_url}: {e}") from e

        if not resp.ok:
            error_text = resp.text
            raise PresentonGenerationError(
                f"Presenton API generation failed with status {resp.status_code}: {error_text}"
            )

        try:
            result_data = resp.json()
        except Exception as e:
            raise PresentonGenerationError(f"Invalid JSON response from Presenton: {resp.text}") from e

        rel_path = result_data.get("path")
        if not rel_path:
            raise PresentonGenerationError(f"Presenton response did not return a valid export path: {result_data}")

        # Download the exported presentation artifact
        clean_rel_path = rel_path if rel_path.startswith("/") else f"/{rel_path}"
        download_url = f"{self.endpoint}{clean_rel_path}"
        logger.info(f"Downloading compiled presentation from {download_url} -> {output_path}...")

        try:
            dl_resp = requests.get(download_url, timeout=60.0)
            if not dl_resp.ok:
                raise PresentonGenerationError(
                    f"Failed to download generated presentation from {download_url} (status {dl_resp.status_code})"
                )

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(dl_resp.content)

            logger.info(f"Successfully saved AI presentation deck to {output_path} ({len(dl_resp.content)} bytes)")
            return output_path
        except Exception as e:
            raise PresentonGenerationError(f"Failed to stream and save presentation from Presenton: {e}") from e
