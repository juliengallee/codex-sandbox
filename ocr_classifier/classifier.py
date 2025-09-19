"""Prototype de classification supervisée basé sur CamemBERT."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import torch
from sklearn.metrics import classification_report
from torch.utils.data import DataLoader, Dataset
from transformers import CamembertModel, CamembertTokenizer


@dataclass
class ClassificationResult:
    """Résultat de classification avec score de confiance."""

    label: str
    score: float


class _TextDataset(Dataset[List[int]]):
    """Jeu de données torch minimal pour entraîner un classifieur linéaire."""

    def __init__(self, encodings: Dict[str, torch.Tensor], labels: Sequence[int]):
        self.encodings = encodings
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self) -> int:
        return self.labels.size(0)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = {key: tensor[idx] for key, tensor in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item


class CamembertClassifier:
    """Fine-tuning léger d'un modèle CamemBERT pour la classification."""

    def __init__(
        self,
        label_names: Sequence[str],
        *,
        pretrained_model: str = "camembert-base",
        device: Optional[str] = None,
    ) -> None:
        self.label_names = list(label_names)
        self.id2label = {idx: label for idx, label in enumerate(self.label_names)}
        self.label2id = {label: idx for idx, label in enumerate(self.label_names)}
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        self.tokenizer = CamembertTokenizer.from_pretrained(pretrained_model)
        self.encoder = CamembertModel.from_pretrained(pretrained_model).to(self.device)
        self.classifier_head = torch.nn.Linear(self.encoder.config.hidden_size, len(self.label_names)).to(self.device)

    def encode(self, texts: Sequence[str], *, max_length: int = 512) -> Dict[str, torch.Tensor]:
        return self.tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )

    def train(
        self,
        train_texts: Sequence[str],
        train_labels: Sequence[str],
        *,
        eval_texts: Optional[Sequence[str]] = None,
        eval_labels: Optional[Sequence[str]] = None,
        epochs: int = 3,
        batch_size: int = 8,
        learning_rate: float = 5e-5,
        weight_decay: float = 0.01,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, float]:
        train_encodings = self.encode(train_texts)
        train_dataset = _TextDataset(train_encodings, [self.label2id[label] for label in train_labels])
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        optimizer = torch.optim.AdamW(
            list(self.encoder.parameters()) + list(self.classifier_head.parameters()),
            lr=learning_rate,
            weight_decay=weight_decay,
        )
        criterion = torch.nn.CrossEntropyLoss()

        self.encoder.train()
        self.classifier_head.train()
        for _ in range(epochs):
            for batch in train_loader:
                optimizer.zero_grad()
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
                cls_embedding = outputs.last_hidden_state[:, 0, :]
                logits = self.classifier_head(cls_embedding)
                loss = criterion(logits, labels)
                loss.backward()
                optimizer.step()

        metrics: Dict[str, float] = {}
        if eval_texts and eval_labels:
            metrics = self.evaluate(eval_texts, eval_labels)

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            self.save(output_dir)

        return metrics

    def evaluate(self, texts: Sequence[str], labels: Sequence[str]) -> Dict[str, float]:
        encodings = self.encode(texts)
        dataset = _TextDataset(encodings, [self.label2id[label] for label in labels])
        loader = DataLoader(dataset, batch_size=16)

        self.encoder.eval()
        self.classifier_head.eval()
        preds: List[int] = []
        with torch.no_grad():
            for batch in loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
                cls_embedding = outputs.last_hidden_state[:, 0, :]
                logits = self.classifier_head(cls_embedding)
                preds.extend(torch.argmax(logits, dim=1).cpu().tolist())

        report = classification_report(
            [self.label2id[label] for label in labels],
            preds,
            target_names=self.label_names,
            zero_division=0,
            output_dict=True,
        )
        return {f"{label}_f1": float(values["f1-score"]) for label, values in report.items() if label in self.label_names}

    def predict(self, text: str) -> ClassificationResult:
        encodings = self.encode([text])
        input_ids = encodings["input_ids"].to(self.device)
        attention_mask = encodings["attention_mask"].to(self.device)

        self.encoder.eval()
        self.classifier_head.eval()
        with torch.no_grad():
            outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            cls_embedding = outputs.last_hidden_state[:, 0, :]
            logits = self.classifier_head(cls_embedding)
            probabilities = torch.nn.functional.softmax(logits, dim=1)

        score, label_id = torch.max(probabilities, dim=1)
        return ClassificationResult(label=self.id2label[label_id.item()], score=score.item())

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self.tokenizer.save_pretrained(directory)
        torch.save(self.encoder.state_dict(), directory / "encoder.pt")
        torch.save(self.classifier_head.state_dict(), directory / "classifier_head.pt")

    def load(self, directory: Path) -> None:
        self.tokenizer = CamembertTokenizer.from_pretrained(directory)
        self.encoder.load_state_dict(torch.load(directory / "encoder.pt", map_location=self.device))
        self.classifier_head.load_state_dict(torch.load(directory / "classifier_head.pt", map_location=self.device))
        self.encoder.to(self.device)
        self.classifier_head.to(self.device)
