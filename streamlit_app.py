"""Interface Streamlit pour la validation et le feedback des classifications documentaires.

Cette application permet de visualiser une liste de documents, filtrer par catégorie/confidence,
valider manuellement les prédictions et exporter les décisions au format CSV.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "sample_documents.json"
EXPORT_FILENAME = "validation_decisions.csv"
SECURITY_REMINDERS = [
    "Lancer l'application uniquement sur une machine de confiance protégée par FileVault.",
    "Désactiver toute synchronisation cloud automatique sur le dossier surveillé.",
    "Supprimer les exports lorsque la session de validation est terminée.",
    "Déconnecter les périphériques externes non chiffrés avant de manipuler les documents sensibles.",
]


@st.cache_data(show_spinner=False)
def load_documents(path: Path = DATA_PATH) -> pd.DataFrame:
    """Charge les métadonnées documents depuis un fichier JSON local."""
    if not path.exists():
        raise FileNotFoundError(
            "Le fichier de métadonnées est introuvable. Vérifiez la configuration locale."
        )

    with path.open("r", encoding="utf-8") as stream:
        records: List[Dict] = json.load(stream)

    df = pd.DataFrame(records)
    if "ingested_at" in df.columns:
        df["ingested_at"] = pd.to_datetime(df["ingested_at"], errors="coerce")

    return df


def filter_documents(
    documents: pd.DataFrame,
    categories: List[str],
    confidence_range: tuple[float, float],
    search_query: str,
) -> pd.DataFrame:
    """Applique les filtres utilisateur sur le tableau des documents."""
    filtered = documents.copy()

    if categories:
        filtered = filtered[filtered["predicted_category"].isin(categories)]

    min_conf, max_conf = confidence_range
    filtered = filtered[
        filtered["prediction_confidence"].between(min_conf, max_conf, inclusive="both")
    ]

    if search_query:
        query = search_query.lower()
        filtered = filtered[
            filtered.apply(
                lambda row: query in row.get("file_name", "").lower()
                or query in str(row.get("ocr_excerpt", "")).lower()
                or query in row.get("document_id", "").lower(),
                axis=1,
            )
        ]

    return filtered.sort_values(by="ingested_at", ascending=False)


def initialise_session_state():
    """Prépare l'espace de stockage des décisions dans la session Streamlit."""
    if "decisions" not in st.session_state:
        st.session_state["decisions"] = {}


def register_decision(document_id: str, payload: Dict[str, str]) -> None:
    """Enregistre ou met à jour la décision pour un document donné."""
    initialise_session_state()
    st.session_state.decisions[document_id] = payload


def decisions_dataframe() -> pd.DataFrame:
    """Retourne les décisions sous forme de DataFrame pour l'affichage/export."""
    initialise_session_state()
    if not st.session_state.decisions:
        return pd.DataFrame()

    df = pd.DataFrame.from_records(
        [
            {
                "document_id": doc_id,
                **decision,
            }
            for doc_id, decision in st.session_state.decisions.items()
        ]
    )
    df["validated_at"] = pd.to_datetime(df["validated_at"], errors="coerce")
    return df.sort_values(by="validated_at", ascending=False)


def render_sidebar(documents: pd.DataFrame) -> dict:
    """Construit la barre latérale contenant les filtres et rappels sécurité."""
    st.sidebar.header("Filtres de tri")
    available_categories = sorted(documents["predicted_category"].unique())
    selected_categories = st.sidebar.multiselect(
        "Catégories suggérées",
        options=available_categories,
        default=available_categories,
    )

    min_conf = float(documents["prediction_confidence"].min())
    max_conf = float(documents["prediction_confidence"].max())
    confidence_range = st.sidebar.slider(
        "Seuil de confiance",
        min_value=0.0,
        max_value=1.0,
        value=(min_conf, max_conf),
        step=0.01,
    )

    search_query = st.sidebar.text_input(
        "Recherche plein texte",
        placeholder="ID document, nom de fichier, extrait OCR...",
    )

    st.sidebar.divider()
    st.sidebar.subheader("Bonnes pratiques sécurité")
    for reminder in SECURITY_REMINDERS:
        st.sidebar.write(f"- {reminder}")

    return {
        "categories": selected_categories,
        "confidence_range": confidence_range,
        "search_query": search_query,
    }


def render_document_overview(documents: pd.DataFrame) -> None:
    st.subheader("Aperçu des documents entrants")
    if documents.empty:
        st.info(
            "Aucun document ne correspond aux filtres. Ajustez vos critères pour reprendre la validation."
        )
        return

    display_df = documents[
        [
            "document_id",
            "file_name",
            "ingested_at",
            "predicted_category",
            "prediction_confidence",
            "supplier",
            "amount",
            "currency",
        ]
    ].copy()
    display_df["prediction_confidence"] = (
        display_df["prediction_confidence"] * 100
    ).map("{:.0f}%".format)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


def render_validation_panel(documents: pd.DataFrame) -> None:
    st.subheader("Validation manuelle & feedback")
    if documents.empty:
        st.caption(
            "Aucun document sélectionnable tant que le filtre ne retourne pas de résultats."
        )
        return

    document_ids = documents["document_id"].tolist()
    selected_id = st.selectbox(
        "Choisissez un document à valider",
        options=document_ids,
    )
    selected_doc = documents.set_index("document_id").loc[selected_id]

    st.markdown(
        f"**Fichier :** `{selected_doc.file_name}`  \
**Chemin source :** `{selected_doc.source_path}`"
    )
    st.markdown(
        f"**Catégorie suggérée :** {selected_doc.predicted_category} (confiance {selected_doc.prediction_confidence:.0%})"
    )
    st.markdown(f"**Fournisseur / émetteur :** {selected_doc.get('supplier', 'N/A')}")
    st.markdown(f"**Montant détecté :** {selected_doc.get('amount', 'N/A')} {selected_doc.get('currency', '')}")
    st.markdown("**Extrait OCR :**")
    st.info(selected_doc.get("ocr_excerpt", "Aucun extrait disponible."))

    with st.expander("Notes de sécurité associées"):
        st.write(selected_doc.get("security_notes", "Non renseigné."))

    st.divider()
    st.markdown("### Décision")
    available_categories = sorted(documents["predicted_category"].unique())
    final_category = st.selectbox(
        "Catégorie finale",
        options=available_categories,
        index=available_categories.index(selected_doc.predicted_category)
        if selected_doc.predicted_category in available_categories
        else 0,
    )
    validation_status = st.radio(
        "Statut de validation",
        options=["Validé", "À revoir", "Rejeté"],
        index=0,
        help="""Utilisez *À revoir* si une vérification supplémentaire est nécessaire,
        et *Rejeté* si le document doit être exclu du jeu d'entraînement.""",
    )
    reviewer_comment = st.text_area(
        "Commentaires / corrections",
        placeholder="Précisez les éléments à corriger ou les champs manquants...",
    )

    if st.button("Enregistrer la décision", type="primary"):
        register_decision(
            selected_id,
            {
                "file_name": selected_doc.file_name,
                "predicted_category": selected_doc.predicted_category,
                "final_category": final_category,
                "validation_status": validation_status,
                "reviewer_comment": reviewer_comment,
                "validated_at": datetime.now().isoformat(timespec="seconds"),
            },
        )
        st.success("Décision enregistrée pour le document sélectionné.")


def render_decision_exports() -> None:
    st.subheader("Historique des validations")
    decisions_df = decisions_dataframe()
    if decisions_df.empty:
        st.caption("Aucune validation enregistrée pour le moment.")
        return

    st.dataframe(decisions_df, use_container_width=True, hide_index=True)

    csv_content = decisions_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Exporter les décisions (CSV)",
        data=csv_content,
        file_name=EXPORT_FILENAME,
        mime="text/csv",
    )
    st.caption(
        "Stockez le fichier sur un volume chiffré et supprimez-le une fois l'import réalisé dans vos outils internes."
    )


def main():
    st.set_page_config(
        page_title="Validation documentaire locale",
        layout="wide",
        page_icon="📁",
    )
    st.title("Interface de validation documentaire (POC)")
    st.caption(
        "Prototype local pour vérifier la pertinence des classifications automatiques tout en restant hors ligne."
    )

    initialise_session_state()

    try:
        documents = load_documents()
    except FileNotFoundError as error:
        st.error(str(error))
        st.stop()

    filters = render_sidebar(documents)
    filtered_docs = filter_documents(
        documents,
        categories=filters["categories"],
        confidence_range=filters["confidence_range"],
        search_query=filters["search_query"],
    )

    render_document_overview(filtered_docs)
    render_validation_panel(filtered_docs)
    render_decision_exports()

    st.divider()
    st.markdown("#### Rappels d'usage")
    st.write(
        "- Conservez l'application et les données sur le même volume chiffré.\n"
        "- Planifiez un point de revue hebdomadaire avec l'équipe OCR/ML pour partager les feedbacks consolidés.\n"
        "- Archivez les décisions validées dans un coffre-fort numérique interne (KeePassXC, coffre chiffré, etc.)."
    )


if __name__ == "__main__":
    main()
