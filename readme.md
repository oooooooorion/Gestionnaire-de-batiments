# Gestionnaire de batiments à usage des facteurs de France et de Navarre
## Introduction
enjoy! entièrement vibe codé

## Lancement de l'Application

### Avec Docker (Recommandé)

**Pré-requis :** Docker et Docker Compose doivent être installés.
1.  Cloner le repo
2.  Ouvrir un terminal à la racine du projet.
3.  Lancer la commande : `docker compose up --build`
4.  Ouvrir un navigateur et se rendre à l'adresse : `http://127.0.0.1:8080`.

Pour éteindre l'outil : ```docker compose down```

### Sans Docker (Python direct)

**Pré-requis :** Python 3.x installé.
1.  Créer un environnement virtuel :
    ```bash
    python3 -m venv venv
    ```
2.  Activer l'environnement virtuel :
    *   **Linux/macOS :** `source venv/bin/activate`
    *   **Windows :** `venv\Scripts\activate`
3.  Installer les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
4.  Lancer l'application :
    ```bash
    python3 app.py
    ```
5.  Ouvrir un navigateur et se rendre à l'adresse : `http://127.0.0.1:8080`

Pour arrêter l'application, retourner au terminal et faire `Ctrl+C`

## Notice détaillée

Une notice détaillée est fournie dans le fichier [notice.md](notice.md).

