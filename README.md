# Gestionnaire de tri de documents administratifs

Ce projet propose un outil de classification pour les contrats, factures et autres documents administratifs. Son objectif est de faciliter l'organisation automatique des documents en fonction de critères personnalisables, afin de gagner du temps et de réduire les erreurs de classement.

## Pré-requis techniques et dépendances

* Python 3.9 ou supérieur.
* `pip` pour la gestion des dépendances.
* `virtualenv` (recommandé) pour isoler l'environnement d'exécution.
* Dépendances listées dans `requirements.txt`.

## Installation

1. Cloner le dépôt :
   ```bash
   git clone <url-du-depot>
   cd codex-sandbox
   ```
2. Créer et activer un environnement virtuel :
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Sous Windows : .venv\\Scripts\\activate
   ```
3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Guide d'usage

1. Préparer un fichier de configuration décrivant les critères de tri (voir section Configuration des critères ci-dessous).
2. Lancer le script principal :
   ```bash
   python main.py --config chemin/vers/config.yml
   ```
3. Vérifier les journaux et le dossier de sortie pour s'assurer que les documents ont été triés correctement.
4. Ajuster les critères au besoin et relancer le script.

## Architecture modulaire et points d'extension

L'application est conçue de manière modulaire afin de faciliter son évolution :

* **Collecte des documents** : module responsable de la récupération des fichiers source depuis des dossiers locaux ou des services distants.
* **Analyse et classification** : composants regroupant les règles de tri (basées sur le contenu, les métadonnées ou les noms de fichiers).
* **Actions de sortie** : gestion du déplacement, de la copie ou du renommage des documents selon les catégories identifiées.

Chaque module expose des interfaces permettant d'ajouter de nouvelles sources de documents, des règles de classification supplémentaires ou des actions post-tri personnalisées.

## Configuration des critères

Les critères de tri sont définis dans un fichier YAML ou JSON. Chaque règle associe un ensemble de conditions à une action.

### Exemple de configuration YAML

```yaml
criteres:
  - nom: Factures fournisseurs
    conditions:
      - type: regex
        champ: nom_fichier
        valeur: "facture_.*"
      - type: mot_cle
        champ: contenu
        valeur: "SIRET"
    action:
      type: deplacer
      dossier_cible: ./sorties/factures

  - nom: Contrats RH
    conditions:
      - type: regex
        champ: contenu
        valeur: "Contrat de travail"
    action:
      type: copier
      dossier_cible: ./sorties/contrats
```

Ce fichier est référencé lors du lancement du script via l'option `--config`. Il est possible d'ajouter autant de règles que nécessaire pour couvrir l'ensemble des cas métiers.

## Points d'assistance

Pour toute question ou pour contribuer au projet, veuillez ouvrir une issue ou soumettre une pull request.
