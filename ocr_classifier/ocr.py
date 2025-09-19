"""OCR utilities leveraging Tesseract via :mod:`pytesseract`.

The goal is to provide a light-weight helper that can be executed on macOS
where Tesseract is installed via Homebrew (``brew install tesseract``).  The
module is defensive: it tries to degrade gracefully when optional dependencies
are missing so the rest of the prototype can still be exercised in dry-run
mode.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

try:  # pragma: no-cover - optional dependency
    import pytesseract
    from PIL import Image
except ModuleNotFoundError:  # pragma: no-cover - optional dependency
    pytesseract = None  # type: ignore
    Image = None  # type: ignore

try:  # pragma: no-cover - optional dependency
    from pdf2image import convert_from_path
except ModuleNotFoundError:  # pragma: no-cover - optional dependency
    convert_from_path = None  # type: ignore


@dataclass
class OCRPageResult:
    """Container describing the OCR output of a single page."""

    page_number: int
    text: str
    confidence: Optional[float] = None


class OCREngine:
    """Perform OCR on PDF or image documents using Tesseract."""

    def __init__(
        self,
        *,
        language: str = "fra",
        dpi: int = 300,
        tesseract_cmd: Optional[str] = None,
    ) -> None:
        if pytesseract is None:
            raise RuntimeError(
                "pytesseract n'est pas installé. Installez Tesseract et pytesseract"
                " pour activer l'OCR."
            )

        self.language = language
        self.dpi = dpi
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def run(self, document_path: Path) -> List[OCRPageResult]:
        """Execute OCR on the supplied document.

        Parameters
        ----------
        document_path:
            Path to a PDF, PNG or JPEG file.
        """

        if not document_path.exists():
            raise FileNotFoundError(document_path)

        suffix = document_path.suffix.lower()
        if suffix == ".pdf":
            return self._run_on_pdf(document_path)
        if suffix in {".png", ".jpg", ".jpeg", ".tiff"}:
            return [self._run_on_image(document_path, page_number=1)]

        raise ValueError(f"Format non supporté: {suffix}")

    def _run_on_pdf(self, document_path: Path) -> List[OCRPageResult]:
        if convert_from_path is None:
            raise RuntimeError(
                "Le module pdf2image est requis pour traiter les PDF."
            )

        images = convert_from_path(
            str(document_path),
            dpi=self.dpi,
            fmt="png",
        )
        return [self._run_on_pil_image(img, page_number=index + 1) for index, img in enumerate(images)]

    def _run_on_image(self, document_path: Path, *, page_number: int) -> OCRPageResult:
        if Image is None:  # pragma: no cover - optional dependency
            raise RuntimeError("Pillow est requis pour ouvrir les images.")
        image = Image.open(document_path)
        return self._run_on_pil_image(image, page_number=page_number)

    def _run_on_pil_image(self, image: "Image.Image", *, page_number: int) -> OCRPageResult:
        data = pytesseract.image_to_data(image, lang=self.language, output_type=pytesseract.Output.DICT)
        text_lines: List[str] = []
        confidences: List[float] = []
        for text, conf in zip(data.get("text", []), data.get("conf", [])):
            if text.strip():
                text_lines.append(text)
            try:
                conf_value = float(conf)
            except (TypeError, ValueError):  # pragma: no cover - robustness
                continue
            if conf_value > -1:
                confidences.append(conf_value)

        mean_confidence = sum(confidences) / len(confidences) if confidences else None
        return OCRPageResult(
            page_number=page_number,
            text="\n".join(text_lines),
            confidence=mean_confidence,
        )

    @staticmethod
    def aggregate_text(results: Iterable[OCRPageResult]) -> str:
        """Concatenate page texts with separators for downstream tasks."""

        return "\n\n".join(result.text for result in results)

    @staticmethod
    def aggregate_confidence(results: Iterable[OCRPageResult]) -> Optional[float]:
        """Compute the mean confidence across pages when available."""

        confidences = [result.confidence for result in results if result.confidence is not None]
        if not confidences:
            return None
        return sum(confidences) / len(confidences)
