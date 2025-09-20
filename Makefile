.PHONY: build up down shell python pip install version clean logs restart

# Variables
COMPOSE = docker-compose
SERVICE = python-app
CLI_SERVICE = python-cli

# Construction et gestion des conteneurs
build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart: down up

# Développement
shell:
	$(COMPOSE) exec $(SERVICE) bash

python:
	$(COMPOSE) exec $(SERVICE) python

# Exécution de scripts
run:
	$(COMPOSE) run --rm $(CLI_SERVICE) python $(FILE)

# Gestion des dépendances
pip:
	$(COMPOSE) exec $(SERVICE) pip $(CMD)

install:
	$(COMPOSE) run --rm $(CLI_SERVICE) pip install $(PACKAGE)

# Informations
version:
	$(COMPOSE) run --rm $(CLI_SERVICE) python --version

logs:
	$(COMPOSE) logs -f $(SERVICE)

# Nettoyage
clean:
	$(COMPOSE) down -v --remove-orphans
	docker system prune -f

# Aide
help:
	@echo "Commandes disponibles:"
	@echo "  build      - Construire l'image Docker"
	@echo "  up         - Démarrer les conteneurs"
	@echo "  down       - Arrêter les conteneurs"
	@echo "  restart    - Redémarrer les conteneurs"
	@echo "  shell      - Shell interactif dans le conteneur"
	@echo "  python     - REPL Python dans le conteneur"
	@echo "  run FILE=script.py - Exécuter un script Python"
	@echo "  pip CMD='list' - Exécuter une commande pip"
	@echo "  install PACKAGE=requests - Installer un package"
	@echo "  version    - Afficher la version Python"
	@echo "  logs       - Afficher les logs du conteneur"
	@echo "  clean      - Nettoyer les conteneurs et images"