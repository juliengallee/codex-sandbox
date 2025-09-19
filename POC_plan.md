## Plan d’action POC (1–2 semaines)

### Vue d’ensemble
Mettre en place une solution locale et sécurisée de tri documentaire fonctionnant sur Mac pour valider le flux de collecte, l’OCR, la classification et la validation manuelle des documents sensibles.

### Répartition des tâches par développeur

#### Dev A – Collecte & orchestrateur local
- Configurer le dossier surveillé, mettre en place `watchdog` et la gestion des déclencheurs d’ingestion (PDF/scans) sur l’environnement macOS cible.
- Normaliser le flux d’entrée (renommage, horodatage, métadonnées minimales) et journaliser les événements pour audit local.
- Intégrer les exigences de sécurité de base : stockage sur disque chiffré, documentation de la procédure de restauration et respect de l’offline-first.
- Préparer un jeu d’échantillons représentatif pour les tests croisés avec Dev B et Dev C.

#### Dev B – OCR & classification supervisée
- Automatiser l’OCR (Tesseract via Homebrew) sur les documents entrants, gérer les erreurs et la qualité de texte extraite.
- Prototyper un modèle CamemBERT (ou AutoML hors ligne) pour classer les documents dans les catégories POC, avec scripts d’entraînement et d’évaluation reproducibles.
- Fournir une API ou un module Python exposant les résultats de classification et leurs scores de confiance pour l’interface.
- Documenter les limites connues et proposer un plan de collecte de feedback pour itérer pendant le MVP.

#### Dev C – Interface de validation & feedback
- Prototyper une interface locale simple (Streamlit ou mini-app React) affichant la liste des documents, métadonnées OCR et catégories proposées.
- Implémenter les interactions de tri/validation manuelle, le filtrage et l’export local des décisions pour nourrir l’amélioration du modèle.
- Intégrer des garde-fous UX pour rappeler les bonnes pratiques de sécurité (off-line, chiffrement, confidentialité).
- Collecter les retours utilisateurs internes et consolider un rapport de pertinence métier avec Dev B.

### Jalons communs
1. **J+2 :** Périmètre fonctionnel et échantillons validés par l’équipe (kickoff commun).
2. **J+7 :** Chaîne ingestion → OCR → classification connectée bout à bout, premiers tests utilisateurs internes.
3. **J+10 :** Interface validée, collecte de feedback, liste d’améliorations pour passage en MVP.
4. **J+14 :** Démo POC, documentation sécurité et plan de montée en charge partagés.

### Tests
⚠️ Aucun test exécuté (revue en lecture seule).
