"""Core package for OCR and classification prototype."""

from .ocr import OCREngine
from .classifier import CamembertClassifier, ClassificationResult
from .pipeline import DocumentProcessingPipeline

__all__ = [
    "OCREngine",
    "CamembertClassifier",
    "ClassificationResult",
    "DocumentProcessingPipeline",
]
