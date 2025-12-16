import shutil # Ajout en haut du fichier avec les autres imports
from flask import Flask, render_template, abort, request, redirect, url_for
import os
import json
import unicodedata
import re
from datetime import datetime

app = Flask(__name__)

# Configuration
DATA_DIR = 'data'
HISTORY_DIR = 'data_history'

def _write_data(filepath, data):
    """Écrit les données dans un fichier JSON tout en sauvegardant la version précédente."""
    # Créer le dossier d'historique pour l'adresse si nécessaire
    address_id = os.path.basename(filepath).replace('.json', '')
    address_history_dir = os.path.join(HISTORY_DIR, address_id)
    os.makedirs(address_history_dir, exist_ok=True)

    # Sauvegarder la version actuelle si elle existe
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            current_data = f.read()
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') # Format plus détaillé et parsable
        backup_path = os.path.join(address_history_dir, f"{timestamp}.json")
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(current_data)

    # Écrire les nouvelles données
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def slugify(value):
    """
    Convertit une chaîne de caractères en un "slug" sécurisé pour un nom de fichier.
    Ex: "1 Rue de la Paix, 75002 Paris" -> "1_rue_de_la_paix_75002_paris"
    """
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '_', value)
    return value

@app.route('/')
def index():
    """Affiche la page d'accueil avec la liste des adresses."""
    addresses = []
    try:
        for filename in sorted(os.listdir(DATA_DIR)):
            if filename.endswith('.json'):
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    addresses.append({
                        'id': filename.replace('.json', ''),
                        'name': data.get('adresse_complete', 'Adresse inconnue')
                    })
    except FileNotFoundError:
        pass
    return render_template('index.html', addresses=addresses)

@app.route('/address/<address_id>')
def show_address(address_id):
    """Affiche la page de détail pour une adresse spécifique."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    
    if not os.path.exists(filepath):
        abort(404) # Page non trouvée
        
    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)
        
    return render_template('address_detail.html', address=address_data, address_id=address_id)

@app.route('/address/new', methods=['GET', 'POST'])
def new_address():
    """Gère l'affichage du formulaire et la création d'une nouvelle adresse."""
    if request.method == 'POST':
        adresse_complete = request.form.get('adresse_complete')
        if not adresse_complete:
            return redirect(url_for('index'))

        file_id = slugify(adresse_complete)
        filepath = os.path.join(DATA_DIR, f"{file_id}.json")

        if not os.path.exists(filepath):
            new_data = {
                "adresse_complete": adresse_complete,
                "batiments": []
            }
            # Pas de sauvegarde ici car le fichier est nouveau
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)

        return redirect(url_for('index'))

    return render_template('new_address.html')


@app.route('/address/<address_id>/edit', methods=['GET', 'POST'])
def edit_address(address_id):
    """Gère l'affichage du formulaire et la modification d'une adresse existante."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)

    if request.method == 'POST':
        new_adresse_complete = request.form.get('adresse_complete')
        if not new_adresse_complete:
            # Si l'adresse complète est vide, on peut afficher une erreur ou rediriger
            return render_template('edit_address.html', address_id=address_id,
                                   address=address_data, error="L'adresse complète ne peut pas être vide.")

        # Vérifier si l'adresse complète a changé
        if new_adresse_complete != address_data.get('adresse_complete'):
            # Générer un nouveau slug pour le nom de fichier si l'adresse complète a changé
            new_file_id = slugify(new_adresse_complete)
            new_filepath = os.path.join(DATA_DIR, f"{new_file_id}.json")

            # Gérer le cas où le nouveau nom de fichier existe déjà pour une autre adresse
            if os.path.exists(new_filepath) and new_file_id != address_id:
                return render_template('edit_address.html', address_id=address_id,
                                       address=address_data, error="Une adresse avec ce nom existe déjà.")

            # Mettre à jour l'adresse complète dans les données
            address_data['adresse_complete'] = new_adresse_complete
            
            # Sauvegarder la version actuelle avant de potentiellement renommer le fichier
            _write_data(filepath, address_data) 

            # Renommer le fichier si l'ID a changé
            if new_file_id != address_id:
                # Déplacer l'historique aussi
                old_history_dir = os.path.join(HISTORY_DIR, address_id)
                new_history_dir = os.path.join(HISTORY_DIR, new_file_id)
                if os.path.exists(old_history_dir):
                    os.rename(old_history_dir, new_history_dir)
                
                os.remove(filepath) # Supprimer l'ancien fichier
                # La fonction _write_data sauvegardera déjà la nouvelle version dans le nouvel emplacement
                # Il n'est pas nécessaire de l'appeler une seconde fois ici car la modification
                # de `address_data` a déjà été écrite via _write_data(filepath, address_data)
                # si l'ID n'a pas changé, ou elle sera écrite après le renommage si l'ID a changé.
                # Pour éviter une double sauvegarde d'historique ou un comportement inattendu
                # lors du renommage, on doit s'assurer que _write_data est appelée au bon moment.
                # Ici, la logique est la suivante:
                # 1. Mise à jour de address_data['adresse_complete']
                # 2. Appel à _write_data(filepath, address_data) pour sauvegarder la version actuelle
                #    AVANT renommage. Cela crée un historique avec l'ancien ID.
                # 3. Si renommage:
                #    a. Déplacer l'historique.
                #    b. Supprimer l'ancien fichier de data/.
                #    c. Écrire le fichier JSON avec le nouveau nom.
                # Cette approche nécessite de revoir légèrement le _write_data ou son appel
                # pour bien gérer le cas de renommage.

                # Simplifions pour l'instant: si l'ID change, on écrase le nouveau fichier
                # et l'ancien est déjà sauvegardé dans l'historique sous l'ancien ID.
                # On met à jour l'ID pour la redirection.
                # Le plus propre serait de faire un os.rename(old_filepath, new_filepath)
                # après avoir fait le _write_data sur old_filepath.
                # La logique actuelle de _write_data inclut la création d'historique.
                # Donc, si l'ID change, nous avons déjà écrit l'historique pour l'ancien ID.
                # Ensuite, nous devons écrire le fichier avec le nouveau nom.
                with open(new_filepath, 'w', encoding='utf-8') as f:
                    json.dump(address_data, f, ensure_ascii=False, indent=2)
                
                address_id = new_file_id # Mettre à jour l'ID pour la redirection
            
        return redirect(url_for('show_address', address_id=address_id))

    return render_template('edit_address.html', address_id=address_id, address=address_data)


@app.route('/address/<address_id>/new-building', methods=['GET', 'POST'])
def new_building(address_id):
    """Gère l'ajout d'un nouveau bâtiment à une adresse existante."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)

    if request.method == 'POST':
        building_name = request.form.get('building_name')
        if building_name and not any(b['nom'] == building_name for b in address_data['batiments']):
            new_building_data = {"nom": building_name, "boites": []}
            address_data['batiments'].append(new_building_data)
            _write_data(filepath, address_data)

        return redirect(url_for('show_address', address_id=address_id))

    return render_template('new_building.html', address_id=address_id, address_name=address_data.get('adresse_complete'))


# Fonction d'aide pour parser les boîtes à partir du texte
def _parse_mailboxes_from_text(text_content):
    new_mailboxes = []
    
    lines = [line.strip() for line in text_content.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        parts = line.split(':', 1)
        if len(parts) < 1: # Minimum a residents part, number is optional
            raise ValueError(f"Ligne {i+1}: Format incorrect. Attendu '[numéro]: [résidents]' ou ':[résidents]'.")

        numero_str = parts[0].strip()
        residents_str = parts[1].strip() if len(parts) > 1 else ''

        numero = None
        if numero_str:
            try:
                numero = int(numero_str)
            except ValueError:
                raise ValueError(f"Ligne {i+1}: Le numéro de boîte '{numero_str}' n'est pas un entier valide.")
        
        residents = [res.strip() for res in residents_str.split(',') if res.strip()]
        new_mailboxes.append({'numero': numero, 'residents': residents})
    
    # Valider l'unicité des numéros de boîte dans la liste nouvellement parsée
    seen_numbers = set()
    for i, mailbox in enumerate(new_mailboxes):
        if mailbox['numero'] is not None:
            if mailbox['numero'] in seen_numbers:
                raise ValueError(f"Ligne {i+1}: Le numéro de boîte {mailbox['numero']} est un doublon dans la liste soumise.")
            seen_numbers.add(mailbox['numero'])

    return new_mailboxes

@app.route('/address/<address_id>/building/<building_name>/edit', methods=['GET', 'POST'])
def edit_building(address_id, building_name):
    """Gère l'affichage du formulaire et la modification d'un bâtiment existant, y compris ses boîtes aux lettres."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)

    target_building = next((b for b in address_data['batiments'] if b['nom'] == building_name), None)
    if not target_building:
        abort(404)

    # Préparer la chaîne de boîtes aux lettres pour le textarea (GET)
    mailboxes_data_str = ""
    for boite in target_building['boites']:
        numero_part = str(boite['numero']) if boite['numero'] is not None else ''
        residents_part = ", ".join(boite['residents'])
        mailboxes_data_str += f"{numero_part}: {residents_part}\n"

    if request.method == 'POST':
        new_building_name = request.form.get('building_name')
        mailboxes_text_data = request.form.get('mailboxes_data', '')

        if not new_building_name:
            return render_template('edit_building.html', address_id=address_id, building_name=building_name,
                                   address_name=address_data.get('adresse_complete'),
                                   mailboxes_data_str=mailboxes_text_data, # Passer les données soumises en cas d'erreur
                                   error="Le nom du bâtiment ne peut pas être vide.")
        
        # Vérifier si le nouveau nom existe déjà pour un autre bâtiment de la même adresse
        if new_building_name != building_name and \
           any(b['nom'] == new_building_name for b in address_data['batiments']):
            return render_template('edit_building.html', address_id=address_id, building_name=building_name,
                                   address_name=address_data.get('adresse_complete'),
                                   mailboxes_data_str=mailboxes_text_data,
                                   error=f"Un bâtiment nommé '{new_building_name}' existe déjà pour cette adresse.")

        try:
            # Parse et valider les nouvelles boîtes aux lettres
            new_mailboxes = _parse_mailboxes_from_text(mailboxes_text_data)
        except ValueError as e:
            return render_template('edit_building.html', address_id=address_id, building_name=building_name,
                                   address_name=address_data.get('adresse_complete'),
                                   mailboxes_data_str=mailboxes_text_data,
                                   error=str(e))

        # Mettre à jour le nom du bâtiment
        target_building['nom'] = new_building_name
        # Mettre à jour les boîtes aux lettres
        target_building['boites'] = new_mailboxes
        # Maintenir le tri des boîtes après modification
        target_building['boites'].sort(key=lambda x: x.get('numero') if x.get('numero') is not None else float('inf'))
        
        _write_data(filepath, address_data)

        # Rediriger vers la page de détail de l'adresse
        return redirect(url_for('show_address', address_id=address_id))

    return render_template('edit_building.html', address_id=address_id, building_name=building_name,
                           address_name=address_data.get('adresse_complete'),
                           mailboxes_data_str=mailboxes_data_str)


@app.route('/address/<address_id>/building/<building_name>/delete', methods=['POST'])
def delete_building(address_id, building_name):
    """Supprime un bâtiment spécifique."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)

    # Trouver l'index du bâtiment à supprimer
    building_index_to_delete = None
    for i, b in enumerate(address_data['batiments']):
        if b['nom'] == building_name:
            building_index_to_delete = i
            break
    
    if building_index_to_delete is None:
        abort(404)
    
    # Supprimer le bâtiment de la liste
    del address_data['batiments'][building_index_to_delete]

    _write_data(filepath, address_data)

    return redirect(url_for('show_address', address_id=address_id))


@app.route('/address/<address_id>/building/<building_name>/new-mailbox', methods=['GET', 'POST'])
def new_mailbox(address_id, building_name):
    """Gère l'ajout d'une nouvelle boîte aux lettres à un bâtiment existant."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)

    target_building = next((b for b in address_data['batiments'] if b['nom'] == building_name), None)
    if not target_building:
        abort(404)

    if request.method == 'POST':
        mailbox_number_str = request.form.get('mailbox_number')
        residents_str = request.form.get('residents', '')

        mailbox_number = None
        if mailbox_number_str:
            try:
                mailbox_number = int(mailbox_number_str)
            except (ValueError, TypeError):
                return render_template('new_mailbox.html', address_id=address_id, building_name=building_name,
                                       address_name=address_data.get('adresse_complete'), error="Le numéro de boîte doit être un entier.")
        
        if mailbox_number is not None and any(b.get('numero') == mailbox_number for b in target_building['boites']):
             return render_template('new_mailbox.html', address_id=address_id, building_name=building_name,
                                   address_name=address_data.get('adresse_complete'), error=f"La boîte n°{mailbox_number} existe déjà.")

        new_mailbox_data = {
            "numero": mailbox_number,
            "residents": [res.strip() for res in residents_str.splitlines() if res.strip()]
        }
        target_building['boites'].append(new_mailbox_data)
        target_building['boites'].sort(key=lambda x: x.get('numero') if x.get('numero') is not None else float('inf'))
        
        _write_data(filepath, address_data)

        return redirect(url_for('show_address', address_id=address_id))

    return render_template('new_mailbox.html', address_id=address_id, building_name=building_name,
                           address_name=address_data.get('adresse_complete'))


from flask import send_file, Response
import io
import csv

@app.route('/address/<address_id>/export', methods=['GET', 'POST'])
def export_address(address_id):
    """Gère l'affichage du formulaire d'export et la génération du fichier CSV."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)

    if request.method == 'POST':
        sort_order = request.form.get('sort_order', 'batiment')
        
        output = io.StringIO()
        writer = csv.writer(output)

        if sort_order == 'batiment':
            writer.writerow(['Bâtiment', 'Numéro de Boîte', 'Nom du Résident'])
            for batiment in sorted(address_data['batiments'], key=lambda x: x['nom']):
                if batiment['boites']:
                    for boite in sorted(batiment['boites'], key=lambda x: x.get('numero') if x.get('numero') is not None else float('inf')):
                        numero_boite = boite.get('numero', 'Non numérotée')
                        if boite['residents']:
                            for resident in sorted(boite['residents']):
                                writer.writerow([batiment['nom'], numero_boite, resident])
                        else:
                            writer.writerow([batiment['nom'], numero_boite, '(Boîte vide)'])
                else:
                    writer.writerow([batiment['nom'], '(Aucune boîte)', ''])
        
        elif sort_order == 'alpha':
            writer.writerow(['Nom du Résident', 'Bâtiment', 'Numéro de Boîte'])
            resident_building_list = []
            for batiment in address_data['batiments']:
                for boite in batiment['boites']:
                    numero_boite = boite.get('numero', 'Non numérotée')
                    for resident in boite['residents']:
                        resident_building_list.append((resident, batiment['nom'], numero_boite))
            
            for resident, building_name, numero_boite in sorted(resident_building_list):
                writer.writerow([resident, building_name, numero_boite])

        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers["Content-Disposition"] = f"attachment; filename=export_{address_id}.csv"
        return response

    return render_template('export_address.html', address_id=address_id, address_name=address_data.get('adresse_complete'))


def _parse_mailboxes_from_iterable(iterable, existing_boites):
    """Fonction d'aide pour parser des boîtes depuis un itérable (CSV ou texte)."""
    new_mailboxes = []
    existing_numbers = {b['numero'] for b in existing_boites if b.get('numero') is not None}

    for i, row in enumerate(iterable):
        if isinstance(row, tuple):
            if len(row) < 2: continue
            row = {'numero_boite': row[0].strip(), 'residents': row[1].strip()}
        
        numero_str = row.get('numero_boite', '').strip()
        residents_str = row.get('residents', '').strip()

        numero = None
        if numero_str:
            try:
                numero = int(numero_str)
                if numero in existing_numbers:
                    raise ValueError(f"Le numéro de boîte {numero} existe déjà.")
                existing_numbers.add(numero)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Erreur à la ligne {i+1}: '{numero_str}' n'est pas un numéro de boîte valide ou est un doublon.")

        residents = [res.strip() for res in residents_str.split(',') if res.strip()]
        new_mailboxes.append({'numero': numero, 'residents': residents})
        
    return new_mailboxes

@app.route('/address/<address_id>/building/<building_name>/mailbox/<int:mailbox_index>/edit', methods=['GET', 'POST'])
def edit_mailbox(address_id, building_name, mailbox_index):
    """Gère l'affichage du formulaire et la modification d'une boîte aux lettres existante."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)

    target_building = next((b for b in address_data['batiments'] if b['nom'] == building_name), None)
    if not target_building:
        abort(404)

    if not (0 <= mailbox_index < len(target_building['boites'])):
        abort(404)
    
    mailbox_to_edit = target_building['boites'][mailbox_index]

    if request.method == 'POST':
        new_mailbox_number_str = request.form.get('mailbox_number')
        new_residents_str = request.form.get('residents', '')

        new_mailbox_number = None
        if new_mailbox_number_str:
            try:
                new_mailbox_number = int(new_mailbox_number_str)
            except (ValueError, TypeError):
                return render_template('edit_mailbox.html', address_id=address_id, building_name=building_name,
                                       address_name=address_data.get('adresse_complete'),
                                       mailbox_index=mailbox_index, mailbox=mailbox_to_edit,
                                       error="Le numéro de boîte doit être un entier.")
        
        # Vérifier l'unicité du numéro de boîte au sein du bâtiment (ignorer la boîte actuelle)
        existing_numbers = {b.get('numero') for i, b in enumerate(target_building['boites'])
                            if b.get('numero') is not None and i != mailbox_index}
        
        if new_mailbox_number is not None and new_mailbox_number in existing_numbers:
            return render_template('edit_mailbox.html', address_id=address_id, building_name=building_name,
                                   address_name=address_data.get('adresse_complete'),
                                   mailbox_index=mailbox_index, mailbox=mailbox_to_edit,
                                   error=f"La boîte n°{new_mailbox_number} existe déjà dans ce bâtiment.")

        mailbox_to_edit['numero'] = new_mailbox_number
        mailbox_to_edit['residents'] = [res.strip() for res in new_residents_str.splitlines() if res.strip()]
        
        # Maintenir le tri des boîtes après modification
        target_building['boites'].sort(key=lambda x: x.get('numero') if x.get('numero') is not None else float('inf'))

        _write_data(filepath, address_data)

        return redirect(url_for('show_address', address_id=address_id))

    # Préparer les résidents pour l'affichage dans le textarea
    mailbox_to_edit['residents_str'] = "\n".join(mailbox_to_edit['residents'])

    return render_template('edit_mailbox.html', address_id=address_id, building_name=building_name,
                           address_name=address_data.get('adresse_complete'),
                           mailbox_index=mailbox_index, mailbox=mailbox_to_edit)

@app.route('/address/<address_id>/building/<building_name>/mailbox/<int:mailbox_index>/delete', methods=['POST'])
def delete_mailbox(address_id, building_name, mailbox_index):
    """Supprime une boîte aux lettres spécifique."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)

    target_building = next((b for b in address_data['batiments'] if b['nom'] == building_name), None)
    if not target_building:
        abort(404)

    if not (0 <= mailbox_index < len(target_building['boites'])):
        abort(404)
    
    # Supprimer la boîte aux lettres de la liste
    del target_building['boites'][mailbox_index]

    _write_data(filepath, address_data)

    return redirect(url_for('show_address', address_id=address_id))

@app.route('/address/<address_id>/building/<building_name>/bulk-add', methods=['GET', 'POST'])
def bulk_add_mailboxes(address_id, building_name):
    """Gère l'ajout en masse de boîtes aux lettres via texte ou CSV."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)

    target_building = next((b for b in address_data['batiments'] if b['nom'] == building_name), None)
    if not target_building:
        abort(404)

    if request.method == 'POST':
        try:
            new_mailboxes = []
            if 'csv_file' in request.files and request.files['csv_file'].filename != '':
                file = request.files['csv_file']
                if not file.filename.lower().endswith('.csv'):
                    raise ValueError("Le fichier doit être au format CSV.")
                
                stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
                csv_reader = csv.DictReader(stream)
                new_mailboxes = _parse_mailboxes_from_iterable(csv_reader, target_building['boites'])
            elif 'bulk_text' in request.form and request.form['bulk_text'].strip() != '':
                text_content = request.form['bulk_text'].splitlines()
                text_iterable = (line.split(':', 1) for line in text_content if ':' in line)
                new_mailboxes = _parse_mailboxes_from_iterable(text_iterable, target_building['boites'])

            if new_mailboxes:
                target_building['boites'].extend(new_mailboxes)
                target_building['boites'].sort(key=lambda x: x.get('numero') if x.get('numero') is not None else float('inf'))
                
                _write_data(filepath, address_data)

            return redirect(url_for('show_address', address_id=address_id))

        except ValueError as e:
            return render_template('bulk_add_mailboxes.html', address_id=address_id, building_name=building_name,
                                   address_name=address_data.get('adresse_complete'), error=str(e))

    return render_template('bulk_add_mailboxes.html', address_id=address_id, building_name=building_name,
                           address_name=address_data.get('adresse_complete'))


@app.route('/address/<address_id>/delete', methods=['POST'])
def delete_address(address_id):
    """Supprime une adresse complète et tout son historique."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    history_dir_path = os.path.join(HISTORY_DIR, address_id)

    if not os.path.exists(filepath):
        abort(404)

    os.remove(filepath) # Supprimer le fichier JSON de l'adresse

    # Supprimer le répertoire d'historique si il existe
    if os.path.exists(history_dir_path):
        shutil.rmtree(history_dir_path) # Supprime le répertoire et son contenu

    return redirect(url_for('index'))

@app.route('/address/<address_id>/history')
def address_history(address_id):
    """Affiche la liste des versions sauvegardées pour une adresse."""
    filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    if not os.path.exists(filepath):
        abort(404)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        address_data = json.load(f)

    address_history_dir = os.path.join(HISTORY_DIR, address_id)
    versions = []
    if os.path.exists(address_history_dir):
        for filename in sorted(os.listdir(address_history_dir), reverse=True):
            if filename.endswith('.json'):
                try:
                    timestamp_str = filename.replace('.json', '')
                    dt_obj = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
                    display_time = dt_obj.strftime('%d/%m/%Y à %Hh%Mmin%Ss')
                    versions.append({'filename': filename, 'display_time': display_time})
                except (ValueError, IndexError):
                    continue # Ignorer les fichiers mal formés

    return render_template('address_history.html', address_id=address_id, 
                           address_name=address_data.get('adresse_complete'), versions=versions)


@app.route('/address/<address_id>/restore/<version_id>', methods=['POST'])
def restore_version(address_id, version_id):
    """Restaure une version spécifique d'une adresse."""
    live_filepath = os.path.join(DATA_DIR, f"{address_id}.json")
    backup_filepath = os.path.join(HISTORY_DIR, address_id, version_id)

    if not os.path.exists(live_filepath) or not os.path.exists(backup_filepath):
        abort(404)

    with open(backup_filepath, 'r', encoding='utf-8') as f:
        restored_data = json.load(f)
    
    _write_data(live_filepath, restored_data)

    return redirect(url_for('show_address', address_id=address_id))


if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)

