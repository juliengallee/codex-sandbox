"""Chaîne d'orchestration reliant OCR et classification."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .classifier import CamembertClassifier, ClassificationResult
from .ocr import OCREngine, OCRPageResult


@dataclass
class DocumentPrediction:
    """Représentation d'un document enrichi par l'OCR et la classification."""

    path: Path
    ocr_pages: List[OCRPageResult]
    aggregated_text: str
    mean_confidence: Optional[float]
    prediction: ClassificationResult


class DocumentProcessingPipeline:
    """Enchaîne l'OCR puis la classification pour un fichier donné."""

    def __init__(self, ocr_engine: OCREngine, classifier: CamembertClassifier) -> None:
        self.ocr_engine = ocr_engine
        self.classifier = classifier

    def process(self, document_path: Path) -> DocumentPrediction:
        ocr_pages = self.ocr_engine.run(document_path)
        aggregated_text = self.ocr_engine.aggregate_text(ocr_pages)
        mean_confidence = self.ocr_engine.aggregate_confidence(ocr_pages)
        prediction = self.classifier.predict(aggregated_text)
        return DocumentPrediction(
            path=document_path,
            ocr_pages=ocr_pages,
            aggregated_text=aggregated_text,
            mean_confidence=mean_confidence,
            prediction=prediction,
        )

    def bulk_process(self, document_paths: Iterable[Path]) -> List[DocumentPrediction]:
        return [self.process(path) for path in document_paths]
