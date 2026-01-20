# Mode d'emploi - Gestionnaire de bâtiments

Ce document détaille l'utilisation de l'application "Gestionnaire de bâtiments", conçue pour faciliter la gestion des adresses, bâtiments et boîtes aux lettres, notamment pour les facteurs.

## Table des Matières
1. [Lancement de l'Application](#lancement-de-lapplication)
2. [Gestion des Adresses](#gestion-des-adresses)
3. [Gestion des Bâtiments](#gestion-des-bâtiments)
4. [Gestion des Boîtes aux Lettres](#gestion-des-boîtes-aux-lettres)
5. [Fonctionnalités avancées](#fonctionnalités-avancées)

---

## Lancement de l'application

### Pré-requis
- **Docker** (Recommandé) OU **Python 3.x** installé sur votre machine.

### Méthode 1 : via Docker (Recommandé)
1. Ouvrez un terminal à la racine du dossier du projet.
2. Exécutez la commande : `docker compose up --build`
3. Une fois lancé, ouvrez votre navigateur web et allez à l'adresse : `http://127.0.0.1:8080`

### Méthode 2 : sans Docker via Python
1. Créez un environnement virtuel : `python3 -m venv venv`
2. Activez l'environnement :
   - Linux/Mac : `source venv/bin/activate`
   - Windows : `venv\Scripts\activate`
3. Installez les dépendances : `pip install -r requirements.txt`
4. Lancez l'application : `python3 app.py`
5. Accédez à `http://127.0.0.1:8080` dans votre navigateur.

---

## Gestion des Adresses

### Créer une nouvelle adresse
1. Sur la page d'accueil, cliquez sur **"Nouvelle Adresse"**.
2. Entrez l'adresse complète dans le champ prévu (ex: "10 Rue de la Paix, 75000 Paris").
3. Validez. L'adresse est créée et vous êtes redirigé vers la liste des adresses.

### Modifier une adresse
1. Cliquez sur le nom d'une adresse pour voir ses détails.
2. Cliquez sur le bouton **"Modifier l'adresse"** (souvent une icône de crayon ou un lien "Éditer").
3. Modifiez le nom et validez.
   * *Note : Cela renommera également le fichier de sauvegarde interne.*

### Supprimer une adresse
1. Sur la page de détail d'une adresse, cliquez sur **"Supprimer l'adresse"** (en rouge).
2. **Attention** : Cette action est irréversible et supprime également tout l'historique associé à cette adresse.

---

## Gestion des Bâtiments

Une adresse peut comporter plusieurs bâtiments (ex: Bâtiment A, Bâtiment B).

### Ajouter un bâtiment
1. Sur la page de détail d'une adresse, cliquez sur **"Ajouter un bâtiment"**.
2. Donnez un nom au bâtiment (ex: "Bâtiment A") et validez.

### Modifier ou supprimer un bâtiment
1. Dans la liste des bâtiments de l'adresse, repérez le bâtiment concerné.
2. Utilisez les boutons d'action à côté du nom du bâtiment pour le **renommer** ou le **supprimer**.
   * La suppression d'un bâtiment supprime toutes les boîtes aux lettres qu'il contient.

---

## Gestion des Boîtes aux Lettres

### Ajouter une boîte aux lettres (Individuel)
1. Dans un bâtiment, cliquez sur **"Ajouter une boîte"**.
2. Renseignez le **Numéro** de la boîte (optionnel, doit être un entier unique dans le bâtiment).
3. Ajoutez le ou les **Noms des résidents** (un par ligne).
4. Validez.

### Ajout en masse (Bulk Add)
Pour ajouter rapidement plusieurs boîtes :
1. Cliquez sur **"Ajout en masse"** pour un bâtiment donné.
2. Vous avez deux options :
   - **Texte** : Saisissez une ligne par boîte au format `Numéro: Résident1, Résident2`.
   - **Fichier CSV** : Importez un fichier CSV avec deux colonnes (Numéro, Résidents).
3. Validez pour importer.

### Modifier une boîte
1. Cliquez sur l'icône d'édition à côté d'une boîte aux lettres.
2. Vous pouvez changer son numéro ou la liste des résidents.

---

## Fonctionnalités avancées

### Import des données par IA
Il est possible d'automatiser l'OCR des batteries de boîtes grâce à un LLM multimodal (ChatGPT, Mistral, Gemini, Claude, etc.) afin de ne pas avoir à remplir chaque nom à la main.

À ce moment là, il faut fournir au LLM des photos d'une résolution suffisamment élevée pour pouvoir lire les noms sur les boîtes, ainsi que le fichier `example_format.json` pour qu'il puisse les formater correctement. 

Voici un exemple de prompt :
```
Je t'ai joint un fichier "example_format.json" indiquant le format de données désiré. Également, je t'ai joint des photos de batteries de boîte à lettre. Chaque image est un
batiment différent. La résidence s'appelle le "123 avenue de la République". Je remplirai les noms de batiments plus tard. Je te demande d'extraire les noms des boîtes aux lettres (noms de famille, sociétés, etc.) et les numéros s'il y en a et de créer un fichier json avec les informations extraites dans le même format en exemple.
```
Tout de même, il faudra repasser manuellement sur le JSON extrait pour
* nommer les bâtiments ;
* corriger les erreurs de l'OCR ;
* corriger l'assocition des noms de famille d'une même boite aux lettres 
  * ex. : `["DURAND-DUPONT"]` doit devenir `["DURAND", "DUPONT"]`;
* vérifier que les noms de famille apparaissent avant les prénoms.

Une fois cela fait, il faut placer le fichier JSON créé dans le dossier `data/`, en veillant que celui-ci se termine bien par l'extension `.json`

Voici un exemple de prompt dans Gemini.

 ![Exemple de prompt](screenshots\unnamed.png)

### Export des données
Vous pouvez exporter les données d'une adresse sous format CSV (Excel).
1. Sur la page de l'adresse, cliquez sur **"Exporter"**.
2. Choisissez le mode de tri :
   - **Par Bâtiment** : Liste hiérarchique (Bâtiment > Boîte > Résident).
   - **Alphabétique** : Liste alphabétique de tous les résidents de l'adresse.
3. Le téléchargement se lance automatiquement.

### Historique et Restauration
L'application sauvegarde automatiquement une version précédente à chaque modification.
1. Cliquez sur **"Historique"** depuis la page d'une adresse.
2. Vous verrez la liste des modifications avec la date et l'heure.
3. Cliquez sur l'icône de restauration (flèche) pour remettre l'adresse dans l'état de cette date.

### Éditeur JSON
Pour les utilisateurs avancés souhaitant modifier directement les données brutes :
1. Cliquez sur **"Éditeur JSON"**.
2. Modifiez le structure JSON directement.
3. **Attention** : Une erreur de syntaxe empêchera la sauvegarde.
