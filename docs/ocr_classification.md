# Prototype OCR & classification (Dev B)

## 1. Vue d'ensemble
Ce dossier décrit le flux OCR → classification supervisée développé pour le POC. Il expose :

- l'automatisation de l'OCR via Tesseract et `pytesseract` ;
- le prototypage d'un classifieur basé sur CamemBERT ;
- le module Python permettant de requêter les prédictions ;
- les limites actuelles et le plan de collecte de feedback pour itérer vers le MVP.

## 2. Dépendances locales
Le pipeline repose sur les outils installables en local sur macOS :

- [Tesseract OCR](https://tesseract-ocr.github.io/) (`brew install tesseract`)
- Python ≥ 3.9 avec les dépendances listées dans `requirements.txt`
- Pour les PDF : `brew install poppler` afin de permettre la conversion via `pdf2image`

## 3. Utilisation
### 3.1 OCR automatisé
```python
from pathlib import Path
from ocr_classifier import OCREngine

engine = OCREngine(language="fra")
results = engine.run(Path("/chemin/vers/document.pdf"))
text = OCREngine.aggregate_text(results)
```

### 3.2 Entraînement du classifieur
Un dataset d'exemple est fourni dans `data/sample_dataset.jsonl` (format JSONL `{ "text": ..., "label": ... }`).
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/train_classifier.py data/sample_dataset.jsonl models/camembert --labels facture note courrier --epochs 1
```

### 3.3 Inférence
```python
from pathlib import Path
from ocr_classifier import CamembertClassifier, DocumentProcessingPipeline, OCREngine

ocr = OCREngine(language="fra")
classifier = CamembertClassifier(label_names=["facture", "note", "courrier"])
pipeline = DocumentProcessingPipeline(ocr, classifier)

prediction = pipeline.process(Path("/chemin/vers/fichier.pdf"))
print(
    prediction.prediction.label,
    prediction.prediction.score,
    prediction.mean_confidence,
)
```

`prediction.mean_confidence` retourne la confiance moyenne Tesseract sur l'ensemble des pages du document (ou `None` si les
scores ne sont pas disponibles).

## 4. Limites connues
- **Entraînement coûteux** : le fine-tuning CamemBERT nécessite un GPU pour des volumes supérieurs à quelques centaines de documents. Pour le POC, limiter le corpus à un échantillon réduit (≈ quelques dizaines de documents).
- **Qualité OCR** : les scans très bruités ou inclinés dégradent la précision. Prévoir une étape de pré-traitement (deskew, binarisation) pour le MVP.
- **Dépendances externes** : `pytesseract`, `pdf2image`, `transformers` et `torch` sont volumineux. Documenter l'installation hors ligne et conserver les wheels sur un disque chiffré.
- **Modèle initial** : le classifieur est volontairement simple (tête linéaire). Pour monter en charge, envisager un entraînement complet ou l'usage de techniques d'apprentissage incrémental.

## 5. Collecte de feedback
- Enregistrer pour chaque document : label prédit, label validé manuellement (depuis l'interface Dev C), score de confiance et horodatage.
- Consolider hebdomadairement les erreurs dans un tableau partagé avec Dev C pour prioriser les corrections.
- Introduire un champ "raison du rejet" dans l'interface pour catégoriser les erreurs (OCR bruité, catégorie manquante, etc.).
- À J+10, réaliser une revue conjointe avec Dev A & C pour ajuster :
  - les catégories cibles et seuils de confiance ;
  - les règles de pré-traitement OCR ;
  - les critères d'échantillonnage pour le prochain cycle d'entraînement.
