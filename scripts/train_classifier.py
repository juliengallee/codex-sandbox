"""Script de prototypage pour entraîner le classifieur CamemBERT."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from sklearn.model_selection import train_test_split

from ocr_classifier.classifier import CamembertClassifier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tuning minimal d'un classifieur CamemBERT")
    parser.add_argument("dataset", type=Path, help="Chemin vers un fichier JSONL contenant les documents annotés.")
    parser.add_argument("output_dir", type=Path, help="Répertoire où sauvegarder le modèle entraîné.")
    parser.add_argument(
        "--labels",
        nargs="+",
        required=True,
        help="Liste complète des labels possibles (ex: factures notes courrier).",
    )
    parser.add_argument("--test-size", type=float, default=0.2, help="Proportion dédiée au jeu de test.")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    return parser.parse_args()


def load_dataset(path: Path) -> List[dict]:
    records: List[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def main() -> None:
    args = parse_args()
    records = load_dataset(args.dataset)
    texts = [record["text"] for record in records]
    labels = [record["label"] for record in records]

    train_texts, eval_texts, train_labels, eval_labels = train_test_split(
        texts,
        labels,
        test_size=args.test_size,
        stratify=labels if len(set(labels)) > 1 else None,
        random_state=42,
    )

    classifier = CamembertClassifier(label_names=args.labels)
    metrics = classifier.train(
        train_texts,
        train_labels,
        eval_texts=eval_texts,
        eval_labels=eval_labels,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        output_dir=args.output_dir,
    )

    print("Evaluation:")
    for key, value in metrics.items():
        print(f" - {key}: {value:.3f}")


if __name__ == "__main__":
    main()
