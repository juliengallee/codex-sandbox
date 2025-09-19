"""Génère un jeu d'échantillons PNG localement pour les pipelines de test.

Ce script nettoie les dossiers `samples/incoming`, `samples/processed` et
`samples/reference`, puis recrée un petit jeu d'images synthétiques accompagné
 d'un manifeste JSON. Les fichiers produits sont ignorés par Git afin de
réduire la taille du dépôt tout en permettant de régénérer rapidement un lot de
travail après clonage.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence
import binascii
import struct
import zlib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = PROJECT_ROOT / "samples"
INCOMING_DIR = SAMPLES_DIR / "incoming"
PROCESSED_DIR = SAMPLES_DIR / "processed"
REFERENCE_DIR = SAMPLES_DIR / "reference"
MANIFEST_PATH = SAMPLES_DIR / "manifest.json"


@dataclass
class SampleDefinition:
    """Description d'un document synthétique à générer."""

    document_id: str
    stage: str
    file_name: str
    description: str
    metadata: Dict[str, str]
    accent: tuple[int, int, int]
    header: tuple[int, int, int]
    body: tuple[int, int, int]
    subfolder: str | None = None

    @property
    def target_path(self) -> Path:
        base_dir = {
            "incoming": INCOMING_DIR,
            "processed": PROCESSED_DIR,
            "reference": REFERENCE_DIR,
        }[self.stage]
        if self.subfolder:
            return base_dir / self.subfolder / self.file_name
        return base_dir / self.file_name

    @property
    def relative_path(self) -> str:
        return str(self.target_path.relative_to(PROJECT_ROOT))


SAMPLE_DEFINITIONS: Sequence[SampleDefinition] = (
    SampleDefinition(
        document_id="INV-2024-0001",
        stage="incoming",
        file_name="invoice_acme_energy.png",
        description="Facture d'énergie simulée pour tests d'ingestion.",
        metadata={
            "predicted_category": "facture",
            "supplier": "ACME Energy",
            "amount": "124.50",
            "currency": "EUR",
        },
        accent=(41, 128, 185),
        header=(234, 242, 248),
        body=(255, 255, 255),
    ),
    SampleDefinition(
        document_id="BULT-2024-0003",
        stage="incoming",
        file_name="payslip_november.png",
        description="Bulletin de paie avec zones de texte simulées.",
        metadata={
            "predicted_category": "bulletin",
            "supplier": "Entreprise Demo",
            "amount": "3 210.00",
            "currency": "EUR",
        },
        accent=(211, 84, 0),
        header=(254, 245, 231),
        body=(255, 255, 255),
    ),
    SampleDefinition(
        document_id="INV-2024-0001",
        stage="processed",
        subfolder="2024",
        file_name="invoice_acme_energy_validated.png",
        description="Facture ACME après validation manuelle.",
        metadata={
            "validated_by": "analyste_a",
            "status": "validated",
        },
        accent=(39, 174, 96),
        header=(234, 242, 248),
        body=(250, 250, 250),
    ),
    SampleDefinition(
        document_id="ID-REFERENCE-01",
        stage="reference",
        file_name="identity_card_template.png",
        description="Pièce d'identité de référence pour le matching visuel.",
        metadata={
            "document_type": "identite",
            "issuer": "Ville de Demo",
        },
        accent=(142, 68, 173),
        header=(243, 229, 245),
        body=(255, 255, 255),
    ),
)


def chunk(tag: bytes, data: bytes) -> bytes:
    """Construit un bloc PNG valide."""
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
    return length + tag + data + crc


def encode_png(width: int, height: int, rgb_bytes: bytes) -> bytes:
    """Encode une image RGB non compressée en PNG minimal."""
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = chunk(b"IHDR", ihdr_data)

    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)  # filtre Aucun
        start = y * stride
        raw.extend(rgb_bytes[start : start + stride])
    compressed = zlib.compress(bytes(raw), level=9)
    idat_chunk = chunk(b"IDAT", compressed)
    iend_chunk = chunk(b"IEND", b"")
    return signature + ihdr_chunk + idat_chunk + iend_chunk


def build_document_pixels(
    width: int,
    height: int,
    header_color: tuple[int, int, int],
    accent_color: tuple[int, int, int],
    body_color: tuple[int, int, int],
) -> bytes:
    """Construit un motif simplifié rappelant un document structuré."""
    pixels = bytearray(width * height * 3)
    header_height = max(40, height // 8)
    accent_width = max(18, width // 18)
    text_band_height = max(6, height // 60)
    for y in range(height):
        for x in range(width):
            index = (y * width + x) * 3
            if y < header_height:
                color = header_color
            elif x < accent_width and y >= header_height:
                color = accent_color
            elif (y - header_height) % (text_band_height * 3) < text_band_height:
                shade = 220
                color = (shade, shade, shade)
            else:
                color = body_color
            pixels[index : index + 3] = bytes(color)
    return bytes(pixels)


def ensure_directories() -> None:
    """Prépare les dossiers de sortie en supprimant les anciens PNG."""
    for directory in (INCOMING_DIR, PROCESSED_DIR, REFERENCE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        for png_file in directory.rglob("*.png"):
            png_file.unlink()


def generate_sample(sample: SampleDefinition, width: int = 620, height: int = 877) -> Dict[str, str]:
    """Crée l'image correspondant à la définition fournie."""
    target_path = sample.target_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    pixels = build_document_pixels(
        width=width,
        height=height,
        header_color=sample.header,
        accent_color=sample.accent,
        body_color=sample.body,
    )
    png_bytes = encode_png(width, height, pixels)
    target_path.write_bytes(png_bytes)

    entry = {
        "document_id": sample.document_id,
        "stage": sample.stage,
        "file_name": sample.file_name,
        "description": sample.description,
        "relative_path": sample.relative_path,
        "metadata": sample.metadata,
    }
    if sample.subfolder:
        entry["subfolder"] = sample.subfolder
    return entry


def build_manifest(entries: Sequence[Dict[str, str]]) -> Dict[str, object]:
    """Assemble le manifeste JSON écrit sur disque."""
    sorted_entries = sorted(entries, key=lambda item: (item["stage"], item["file_name"]))
    return {
        "generated_at": datetime.utcnow().replace(microsecond=False).isoformat() + "Z",
        "sample_count": len(sorted_entries),
        "samples": sorted_entries,
    }


def run() -> None:
    """Point d'entrée principal du script."""
    ensure_directories()
    entries: List[Dict[str, str]] = []
    for definition in SAMPLE_DEFINITIONS:
        entries.append(generate_sample(definition))
    manifest = build_manifest(entries)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"✅ Génération terminée : {len(entries)} images et un manifeste mis à jour.")
    print(f"   → Manifest: {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Ne régénère que le manifeste (suppose que les images existent déjà).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.manifest_only:
        entries: List[Dict[str, str]] = []
        for definition in SAMPLE_DEFINITIONS:
            if definition.target_path.exists():
                entries.append(
                    {
                        "document_id": definition.document_id,
                        "stage": definition.stage,
                        "file_name": definition.file_name,
                        "description": definition.description,
                        "relative_path": definition.relative_path,
                        "metadata": definition.metadata,
                        **({"subfolder": definition.subfolder} if definition.subfolder else {}),
                    }
                )
        if not entries:
            raise SystemExit(
                "Aucune image existante détectée. Relancez le script sans --manifest-only pour les recréer."
            )
        manifest = build_manifest(entries)
        MANIFEST_PATH.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print("Manifeste mis à jour à partir des images existantes.")
        return

    run()


if __name__ == "__main__":  # pragma: no cover - exécution directe
    main()
