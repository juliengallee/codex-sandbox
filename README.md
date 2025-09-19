# Roadmap personnalisée pour une plateforme de tri documentaire

## 1. Objectif général
Mettre en place une solution personnelle, sécurisée et autonome fonctionnant sur Mac pour collecter, classifier et exploiter des documents sensibles (factures, documents administratifs, notes internes, etc.).

## 2. Parcours d'évolution

### 2.1 POC local (1-2 semaines)
- Créez un dossier surveillé sur votre Mac pour déposer vos PDF ou scans et utilisez une routine Python (ex. `watchdog`) pour déclencher l'ingestion dès qu'un fichier arrive, afin de valider le flux de collecte local sans dépendances externes.
- Appliquez un OCR basique pour les contenus image/PDF (Tesseract via Homebrew) et entraînez un premier modèle de classification supervisée (CamemBERT ou service AutoML hors ligne) sur un échantillon réduit pour trier quelques catégories personnelles.
- Exposez une interface très simple (Streamlit ou petite app React lancée en local) permettant de visualiser, trier et valider les documents afin de confirmer la pertinence métier du tri automatique, tout en conservant les données sur le disque chiffré de votre Mac.

### 2.2 MVP “usage quotidien” (3-5 semaines supplémentaires)
- Étendez la chaîne précédente en ajoutant l'extraction des principaux champs (dates, montants, interlocuteurs) via spaCy, transformers et règles regex, puis stockez métadonnées et fichiers chiffrés dans une base locale (SQLite ou PostgreSQL via Docker Desktop).
- Sécurisez l'accès avec une authentification locale (mot de passe maître dans le Trousseau macOS, chiffrement TLS auto-signé) et ajoutez un historique d'actions pour tracer les manipulations sensibles ; mettez en place un pipeline de tests unitaires basiques pour fiabiliser les mises à jour.
- Organisez des sessions de tests et recueillez le feedback pour affiner catégories, règles et performances du modèle, tout en ajoutant un script de sauvegarde automatique (Time Machine chiffré, archive gpg) et un pipeline CI/CD minimal pour automatiser les mises à jour.

### 2.3 Version personnelle aboutie (V2)
- Conteneurisez vos services (FastAPI + PostgreSQL + interface web) avec Docker Desktop pour simplifier la maintenance et permettre un déploiement sur un NAS ou mini-serveur local, en renforçant notifications macOS, exports chiffrés et intégrations optionnelles avec vos outils comptables.
- Ajoutez des automatisations : alertes locales pour échéances détectées, génération d'exports chiffrés (CSV/PDF) et intégrations API, en conservant les clés dans le Trousseau macOS ; mettez en place une gouvernance légère avec sessions d'annotation périodiques et suivi de KPIs personnels.
- Renforcez la sécurité : isolation réseau (pare-feu Mac), chiffrement TLS même en local, rotation régulière des clés, vérification de l'intégrité des conteneurs et plan de purge automatique des documents sensibles après validation finale.

## 3. Feuille de route synthétique

### POC
1. Définir un flux minimal de collecte (upload manuel ou connecteur simple) pour ingérer un lot représentatif de documents.
2. Appliquer un OCR basique pour les contenus image/PDF et entraîner un premier modèle de classification supervisée sur un échantillon réduit.
3. Exposer une interface très simple (tableau ou liste) permettant de visualiser et trier les documents afin de valider la pertinence métier du tri automatique.

### MVP
1. Étendre la chaîne précédente en ajoutant l'extraction des principaux champs (date, montant, fournisseur…) via modèles de séquençage ou règles, puis stocker métadonnées et fichiers dans une base structurée sécurisée.
2. Mettre en place l'authentification des utilisateurs et une interface plus riche (filtres, validation manuelle) connectée à une API backend stable pour les premiers tests utilisateurs.
3. Organiser des sessions de tests et recueillir le feedback pour affiner catégories, règles et performances du modèle, en amorçant un pipeline CI/CD basique pour automatiser les mises à jour.

### V2 (version production avancée)
1. Intégrer la plateforme avec les systèmes métiers (ERP/comptabilité) via API ou exports, en renforçant notifications, alertes et workflows d'approbation complets.
2. Industrialiser l'infrastructure (conteneurs, monitoring, sécurité TLS/SSO) et instaurer une gouvernance data : annotation continue, KPIs de qualité, plan de support.
3. Préparer l'évolution fonctionnelle : apprentissage continu, nouveaux types de documents, multilingue ou signature électronique pour assurer la montée en puissance de la solution.

## 4. Bonnes pratiques de sécurité continue
- Gardez tout le pipeline hors ligne par défaut ; n'activez une synchronisation cloud que si elle est chiffrée de bout en bout.
- Documentez les procédures de restauration, définissez un plan de réponse en cas de fuite locale (perte/vol de Mac) et utilisez FileVault plus un mot de passe robuste pour protéger l'ensemble de la machine.

