import time
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cle_secrete_wifi_derangement'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:password@db:3306/wifi_derangement')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def wait_for_db():
    """Attendre que la base de données soit disponible"""
    import pymysql
    import threading
    import time
    
    def check_db():
        retry_delay = 2
        max_retries = 30
        
        for i in range(max_retries):
            try:
                conn = pymysql.connect(
                    host='db',
                    user='root',
                    password='password',
                    port=3306
                )
                conn.close()
                print("Base de données connectée avec succès!")
                return True
            except Exception as e:
                print(f"Tentative de connexion à la base de données {i+1}/{max_retries}: {e}")
                time.sleep(retry_delay)
        
        print("Base de données disponible en permanence")
        return True
    
    # Lancer la vérification en arrière-plan
    db_thread = threading.Thread(target=check_db, daemon=True)
    db_thread.start()
    
    # Donner du temps pour la première connexion
    time.sleep(3)
    return True

class Technicien(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    specialite = db.Column(db.String(100), nullable=False)  # Réseau, Équipement, etc.
    zone_couverture = db.Column(db.String(200), nullable=False)  # Zones desservies
    disponibilite = db.Column(db.String(20), default='disponible')  # disponible, occupe, conge
    date_embauche = db.Column(db.DateTime, default=datetime.utcnow)
    interventions_en_cours = db.Column(db.Integer, default=0)
    interventions_totales = db.Column(db.Integer, default=0)
    
    signalements = db.relationship('Signalement', backref='technicien_obj', lazy=True)
    
    def __repr__(self):
        return f'<Technicien {self.prenom} {self.nom}>'
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"
    
    @property
    def statut_display(self):
        statuts = {
            'disponible': '✅ Disponible',
            'occupe': '🔧 Occupé',
            'conge': '🏖️ En congé'
        }
        return statuts.get(self.disponibilite, 'Inconnu')

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='agent')  # agent, superviseur
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Agent {self.prenom} {self.nom}>'

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    zone = db.Column(db.String(200), nullable=False)
    signalements = db.relationship('Signalement', backref='client', lazy=True)

    @property
    def statut_display(self):
        statuts = {
            'nouveau': '🆕 Nouveau',
            'en_attente': '⏳ En attente',
            'en_cours': '🔧 En cours',
            'resolu': '✅ Résolu'
        }
        return statuts.get(self.statut, self.statut.title())

class Signalement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_signalement = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='nouveau')  # nouveau, en_attente, en_cours, resolu
    delai_intervention = db.Column(db.String(100))
    date_intervention = db.Column(db.DateTime)
    technicien_assigne = db.Column(db.String(100))
    technicien_id = db.Column(db.Integer, db.ForeignKey('technicien.id'), nullable=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=True)
    agent = db.relationship('Agent', foreign_keys=[agent_id], backref='signalements_geres')
    agent_resolution_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=True)
    notes_agent = db.Column(db.Text)
    date_prise_en_charge = db.Column(db.DateTime)
    urgence = db.Column(db.String(20), default='normale')  # basse, normale, haute, urgente
    type_probleme = db.Column(db.String(100))  # connexion, lenteur, equipement, autre
    message_client = db.Column(db.Text)  # Message envoyé au client
    notification_envoyee = db.Column(db.Boolean, default=False)  # Si notification SMS/email envoyée
    date_resolution = db.Column(db.DateTime)  # Date de résolution
    rapport_intervention = db.Column(db.Text)  # Rapport d'intervention
    duree_intervention = db.Column(db.String(50))  # Durée de l'intervention
    actions_resolution = db.Column(db.Text)  # Actions effectuées pour résolution
    temps_intervention = db.Column(db.String(20))  # Temps en minutes
    pieces_utilisees = db.Column(db.String(500))  # Pièces utilisées
    recommandations = db.Column(db.Text)  # Recommandations
    confirmation_client = db.Column(db.String(20), default='non')  # Confirmation du client
    agent_resolution_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=True)  # Agent qui a résolu

    @property
    def statut_display(self):
        statuts = {
            'nouveau': '🆕 Nouveau',
            'en_attente': '⏳ En attente',
            'en_cours': '🔧 En cours',
            'resolu': '✅ Résolu'
        }
        return statuts.get(self.statut, self.statut.title())

    @property
    def technicien_obj(self):
        if self.technicien_id:
            return Technicien.query.get(self.technicien_id)
        return None

    def __repr__(self):
        return f'<Signalement {self.id} - {self.client.prenom} {self.client.nom}>'

# Décorateur pour vérifier si l'agent est connecté
def agent_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'agent_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page', 'warning')
            return redirect(url_for('login_agent'))
        return f(*args, **kwargs)
    return decorated_function

# Décorateur pour vérifier si l'agent est un superviseur
def superviseur_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'agent_id' not in session or session.get('agent_role') != 'superviseur':
            flash('Accès réservé aux superviseurs', 'danger')
            return redirect(url_for('tableau_bord_agent'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/signalement/<int:signalement_id>/resoudre', methods=['GET', 'POST'])
@agent_required
def resoudre_signalement(signalement_id):
    """Résoudre un signalement"""
    signalement = Signalement.query.get_or_404(signalement_id)
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        resolution_date = request.form.get('resolution_date')
        actions_effectuees = request.form.get('actions_effectuees', '')
        temps_intervention = request.form.get('temps_intervention', '')
        pieces_utilisees = request.form.get('pieces_utilisees', '')
        recommandations = request.form.get('recommandations', '')
        confirmation_client = request.form.get('confirmation_client', 'oui')
        
        # Valider que le signalement peut être résolu
        if signalement.statut == 'resolu':
            flash('Ce signalement est déjà résolu', 'warning')
            return redirect(url_for('signalements_agent'))
        
        if signalement.statut == 'annule':
            flash('Ce signalement a été annulé et ne peut pas être résolu', 'danger')
            return redirect(url_for('signalements_agent'))
        
        # Mettre à jour le signalement
        signalement.statut = 'resolu'
        signalement.date_resolution = datetime.utcnow()
        signalement.actions_resolution = actions_effectuees
        signalement.temps_intervention = temps_intervention
        signalement.pieces_utilisees = pieces_utilisees
        signalement.recommandations = recommandations
        signalement.confirmation_client = confirmation_client
        signalement.agent_resolution_id = session['agent_id']
        
        # Libérer le technicien si assigné
        if signalement.technicien_id:
            technicien = Technicien.query.get(signalement.technicien_id)
            if technicien:
                technicien.interventions_en_cours = max(0, technicien.interventions_en_cours - 1)
                technicien.interventions_totales += 1
                technicien.disponibilite = 'disponible'
        
        db.session.commit()
        
        # Envoyer notification (simulation)
        print(f"✅ Signalement #{signalement.id} résolu")
        print(f"👤 Client: {signalement.client.telephone}")
        print(f"🔧 Agent: {session.get('agent_nom', 'Agent')}")
        print(f"⏰ Date résolution: {signalement.date_resolution.strftime('%d/%m/%Y %H:%M')}")
        print(f"📝 Actions: {actions_effectuees[:100]}...")
        
        flash(f'Signalement #{signalement.id} marqué comme résolu avec succès', 'success')
        return redirect(url_for('signalements_agent'))
    
    return render_template('agent/resoudre_signalement.html', signalement=signalement)

@app.route('/signalement/<int:signalement_id>/modifier-statut', methods=['POST'])
@agent_required
def modifier_statut_signalement(signalement_id):
    """Modifier rapidement le statut d'un signalement"""
    signalement = Signalement.query.get_or_404(signalement_id)
    nouveau_statut = request.form.get('nouveau_statut')
    
    # Valider le statut
    statuts_valides = ['nouveau', 'en_attente', 'en_cours', 'resolu', 'annule']
    if nouveau_statut not in statuts_valides:
        flash('Statut invalide', 'danger')
        return redirect(url_for('signalements_agent'))
    
    # Mettre à jour le statut
    ancien_statut = signalement.statut
    signalement.statut = nouveau_statut
    
    # Gérer les changements de technicien
    if nouveau_statut == 'resolu' and signalement.technicien_id:
        technicien = Technicien.query.get(signalement.technicien_id)
        if technicien:
            technicien.interventions_en_cours = max(0, technicien.interventions_en_cours - 1)
            technicien.interventions_totales += 1
            technicien.disponibilite = 'disponible'
    
    if nouveau_statut == 'en_cours' and signalement.technicien_id:
        technicien = Technicien.query.get(signalement.technicien_id)
        if technicien and technicien.disponibilite == 'disponible':
            technicien.interventions_en_cours += 1
            technicien.disponibilite = 'occupe'
    
    db.session.commit()
    
    flash(f'Statut du signalement #{signalement.id} changé de "{ancien_statut}" à "{nouveau_statut}"', 'success')
    return redirect(url_for('signalements_agent'))

@app.route('/acces-rapide')
def acces_rapide():
    """Page d'accès rapide avec identifiants par défaut"""
    return render_template('acces_rapide.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verification', methods=['GET', 'POST'])
def verification_signalement():
    """Page de vérification pour les clients"""
    signalements = []
    no_results = False
    
    if request.method == 'POST':
        search_value = request.form.get('phone', '').strip()
        
        if search_value:
            # Rechercher par téléphone du client
            client = Client.query.filter_by(telephone=search_value).first()
            if client:
                signalements = Signalement.query.filter_by(client_id=client.id).order_by(Signalement.date_signalement.desc()).all()
            else:
                no_results = True
        else:
            no_results = True
    
    return render_template('client/verification.html', 
                         signalements=signalements, 
                         no_results=no_results)

def client_login_required(f):
    """Décorateur pour exiger la connexion client"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'client_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page', 'warning')
            return redirect(url_for('connexion_client'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/inscription-client', methods=['GET', 'POST'])
def inscription_client():
    """Page d'inscription pour les clients"""
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        prenom = request.form.get('prenom', '').strip()
        telephone = request.form.get('telephone', '').strip()
        email = request.form.get('email', '').strip()
        zone = request.form.get('zone', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Validation
        errors = []
        
        if not nom or not prenom:
            errors.append('Le nom et le prénom sont obligatoires')
        
        if not telephone or len(telephone) != 9 or not telephone.isdigit():
            errors.append('Le numéro de téléphone doit contenir 9 chiffres')
        
        if Client.query.filter_by(telephone=telephone).first():
            errors.append('Ce numéro de téléphone est déjà utilisé')
        
        if password != password_confirm:
            errors.append('Les mots de passe ne correspondent pas')
        
        if len(password) < 8:
            errors.append('Le mot de passe doit contenir au moins 8 caractères')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('client/inscription.html')
        
        # Créer le client
        client = Client(
            nom=nom,
            prenom=prenom,
            telephone=telephone,
            email=email if email else None,
            zone=zone,
            date_creation=datetime.utcnow()
        )
        
        db.session.add(client)
        db.session.commit()
        
        flash('Compte créé avec succès! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('connexion_client'))
    
    return render_template('client/inscription.html')

@app.route('/connexion-client', methods=['GET', 'POST'])
def connexion_client():
    """Page de connexion pour les clients"""
    if request.method == 'POST':
        telephone = request.form.get('telephone', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', '0')
        
        client = Client.query.filter_by(telephone=telephone).first()
        
        if client and len(password) >= 8:  # Validation simple
            session['client_id'] = client.id
            session['client_telephone'] = client.telephone
            session['client_nom'] = f"{client.prenom} {client.nom}"
            session['last_login'] = datetime.utcnow().strftime('%d/%m/%Y %H:%M')
            
            flash(f'Bienvenue {client.prenom} !', 'success')
            return redirect(url_for('tableau_bord_client'))
        else:
            flash('Numéro de téléphone ou mot de passe incorrect', 'danger')
    
    return render_template('client/connexion.html')

@app.route('/tableau-bord-client')
@client_login_required
def tableau_bord_client():
    """Tableau de bord pour les clients"""
    client = Client.query.get(session['client_id'])
    
    # Statistiques
    total_signalements = Signalement.query.filter_by(client_id=client.id).count()
    signalements_resolus = Signalement.query.filter_by(client_id=client.id, statut='resolu').count()
    signalements_en_cours = Signalement.query.filter_by(client_id=client.id, statut='en_cours').count()
    signalements_en_attente = Signalement.query.filter_by(client_id=client.id, statut='en_attente').count()
    
    # Signalements récents
    signalements_recents = Signalement.query.filter_by(client_id=client.id)\
        .order_by(Signalement.date_signalement.desc())\
        .limit(5).all()
    
    return render_template('client/tableau_bord.html',
                         client=client,
                         total_signalements=total_signalements,
                         signalements_resolus=signalements_resolus,
                         signalements_en_cours=signalements_en_cours,
                         signalements_en_attente=signalements_en_attente,
                         signalements_recents=signalements_recents)

@app.route('/deconnexion-client')
def deconnexion_client():
    """Déconnexion du client"""
    session.clear()
    flash('Vous avez été déconnecté avec succès', 'info')
    return redirect(url_for('index'))

@app.route('/mot-de-passe-oublie', methods=['GET', 'POST'])
def mot_de_passe_oublie():
    """Page pour mot de passe oublié"""
    if request.method == 'POST':
        telephone = request.form.get('telephone', '').strip()
        
        client = Client.query.filter_by(telephone=telephone).first()
        if client and client.email:
            # Simuler l'envoi d'email
            flash(f'Un email de réinitialisation a été envoyé à {client.email}', 'success')
        else:
            flash('Aucun compte trouvé avec ce numéro de téléphone', 'danger')
    
    return render_template('client/mot_de_passe_oublie.html')

@app.route('/annulation', methods=['GET', 'POST'])
def annulation_signalement():
    """Page d'annulation pour les clients"""
    signalements = []
    no_results = False
    
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        
        if phone:
            # Rechercher les signalements annulables du client
            client = Client.query.filter_by(telephone=phone).first()
            if client:
                signalements = Signalement.query.filter_by(client_id=client.id)\
                    .filter(Signalement.statut.in_(['nouveau', 'en_attente']))\
                    .order_by(Signalement.date_signalement.desc()).all()
            else:
                no_results = True
        else:
            no_results = True
    
    return render_template('client/annulation.html', 
                         signalements=signalements, 
                         no_results=no_results)

@app.route('/annuler-signalement/<int:signalement_id>', methods=['POST'])
def annuler_signalement_action():
    """Action d'annulation d'un signalement"""
    signalement = Signalement.query.get_or_404(signalement_id)
    reason = request.form.get('reason', '')
    
    # Vérifier que le signalement peut être annulé
    if signalement.statut not in ['nouveau', 'en_attente']:
        flash('Ce signalement ne peut plus être annulé', 'danger')
        return redirect(url_for('annulation_signalement'))
    
    # Mettre à jour le signalement
    signalement.statut = 'annule'
    signalement.date_annulation = datetime.utcnow()
    signalement.motif_annulation = reason
    
    # Libérer le technicien si assigné
    if signalement.technicien_id:
        technicien = Technicien.query.get(signalement.technicien_id)
        if technicien:
            technicien.interventions_en_cours = max(0, technicien.interventions_en_cours - 1)
            technicien.disponibilite = 'disponible'
    
    db.session.commit()
    
    # Envoyer notification (simulation)
    print(f"🚫 Signalement #{signalement.id} annulé")
    print(f"📱 Client: {signalement.client.telephone}")
    print(f"💬 Raison: {reason if reason else 'Non spécifiée'}")
    print(f"📅 Date annulation: {signalement.date_annulation.strftime('%d/%m/%Y %H:%M')}")
    
    flash(f'Signalement #{signalement.id} a été annulé avec succès', 'success')
    return redirect(url_for('annulation_signalement'))

@app.route('/verification-par-id', methods=['GET', 'POST'])
def verification_par_id():
    """Vérification par numéro de signalement"""
    signalements = []
    no_results = False
    
    if request.method == 'POST':
        signalement_id = request.form.get('signalement_id', '').strip()
        
        try:
            signalement_id = int(signalement_id)
            signalement = Signalement.query.get(signalement_id)
            if signalement:
                signalements = [signalement]
            else:
                no_results = True
        except ValueError:
            no_results = True
    
    return render_template('client/verification.html', 
                         signalements=signalements, 
                         no_results=no_results)

@app.route('/suivi-signalement/<int:signalement_id>')
def suivi_signalement(signalement_id):
    """Page de suivi pour les clients"""
    signalement = Signalement.query.get_or_404(signalement_id)
    return render_template('client/suivi_signalement.html', signalement=signalement)

@app.route('/login-agent', methods=['GET', 'POST'])
def login_agent():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        agent = Agent.query.filter_by(email=email).first()
        
        if agent and agent.check_password(password):
            session['agent_id'] = agent.id
            session['agent_nom'] = f"{agent.prenom} {agent.nom}"
            session['agent_role'] = agent.role
            flash(f'Bonjour {agent.prenom} !', 'success')
            return redirect(url_for('tableau_bord_agent'))
        else:
            flash('Email ou mot de passe incorrect', 'danger')
    
    return render_template('agent/login.html')

@app.route('/logout-agent')
def logout_agent():
    session.clear()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('login_agent'))

@app.route('/administration')
@superviseur_required
def administration():
    """Page d'administration principale pour les superviseurs"""
    total_agents = Agent.query.count()
    total_techniciens = Technicien.query.count()
    total_signalements = Signalement.query.count()
    
    agents = Agent.query.all()
    techniciens = Technicien.query.all()
    
    return render_template('admin/administration.html', 
                         total_agents=total_agents,
                         total_techniciens=total_techniciens,
                         total_signalements=total_signalements,
                         agents=agents,
                         techniciens=techniciens)

@app.route('/administration/agents')
@superviseur_required
def gestion_agents():
    """Page de gestion des agents"""
    agents = Agent.query.order_by(Agent.date_creation.desc()).all()
    return render_template('admin/gestion_agents.html', agents=agents)

@app.route('/administration/agent/creer', methods=['GET', 'POST'])
@superviseur_required
def creer_agent():
    """Créer un nouvel agent"""
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        # Vérifier si l'email existe déjà
        if Agent.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé par un autre agent', 'danger')
            return redirect(url_for('creer_agent'))
        
        # Créer le nouvel agent
        agent = Agent(
            nom=nom,
            prenom=prenom,
            email=email,
            role=role
        )
        agent.set_password(password)
        
        db.session.add(agent)
        db.session.commit()
        
        flash(f'Agent {agent.prenom} {agent.nom} créé avec succès!', 'success')
        return redirect(url_for('gestion_agents'))
    
    return render_template('admin/creer_agent.html')

@app.route('/administration/agent/<int:agent_id>/modifier', methods=['GET', 'POST'])
@superviseur_required
def modifier_agent(agent_id):
    """Modifier un agent existant"""
    agent = Agent.query.get_or_404(agent_id)
    
    if request.method == 'POST':
        agent.nom = request.form['nom']
        agent.prenom = request.form['prenom']
        agent.email = request.form['email']
        agent.role = request.form['role']
        
        # Changer le mot de passe si fourni
        if request.form.get('password'):
            agent.set_password(request.form['password'])
        
        db.session.commit()
        flash(f'Agent {agent.prenom} {agent.nom} modifié avec succès!', 'success')
        return redirect(url_for('gestion_agents'))
    
    return render_template('admin/modifier_agent.html', agent=agent)

@app.route('/administration/agent/<int:agent_id>/supprimer', methods=['POST'])
@superviseur_required
def supprimer_agent(agent_id):
    """Supprimer un agent"""
    agent = Agent.query.get_or_404(agent_id)
    
    # Vérifier si l'agent a des signalements en cours
    signalements_en_cours = Signalement.query.filter_by(agent_id=agent_id, statut='en_cours').count()
    if signalements_en_cours > 0:
        flash(f'Impossible de supprimer cet agent: {signalements_en_cours} signalements en cours', 'danger')
        return redirect(url_for('gestion_agents'))
    
    # Empêcher la suppression de son propre compte
    if agent.id == session['agent_id']:
        flash('Vous ne pouvez pas supprimer votre propre compte', 'danger')
        return redirect(url_for('gestion_agents'))
    
    nom_agent = f"{agent.prenom} {agent.nom}"
    db.session.delete(agent)
    db.session.commit()
    
    flash(f'Agent {nom_agent} supprimé avec succès!', 'success')
    return redirect(url_for('gestion_agents'))

@app.route('/administration/agent/<int:agent_id>/activer', methods=['POST'])
@superviseur_required
def activer_desactiver_agent(agent_id):
    """Activer ou désactiver un agent"""
    agent = Agent.query.get_or_404(agent_id)
    
    # Ici on pourrait ajouter un champ 'actif' au modèle Agent
    # Pour l'instant, on simule avec le rôle
    if agent.role == 'agent_desactive':
        agent.role = 'agent'
        flash(f'Agent {agent.prenom} {agent.nom} activé avec succès!', 'success')
    else:
        agent.role = 'agent_desactive'
        flash(f'Agent {agent.prenom} {agent.nom} désactivé avec succès!', 'warning')
    
    db.session.commit()
    return redirect(url_for('gestion_agents'))

@app.route('/tableau-bord-agent')
@agent_required
def tableau_bord_agent():
    # Statistiques
    total_signalements = Signalement.query.count()
    nouveaux = Signalement.query.filter_by(statut='nouveau').count()
    en_attente = Signalement.query.filter_by(statut='en_attente').count()
    en_cours = Signalement.query.filter_by(statut='en_cours').count()
    resolus = Signalement.query.filter_by(statut='resolu').count()
    
    # Signalements récents
    signalements_recents = Signalement.query.order_by(Signalement.date_signalement.desc()).limit(10).all()
    
    return render_template('agent/tableau_bord.html', 
                         total_signalements=total_signalements,
                         nouveaux=nouveaux,
                         en_attente=en_attente,
                         en_cours=en_cours,
                         resolus=resolus,
                         signalements_recents=signalements_recents)

@app.route('/signalements-agent')
@agent_required
def signalements_agent():
    page = request.args.get('page', 1, type=int)
    statut = request.args.get('statut', '')
    
    query = Signalement.query
    
    if statut:
        query = query.filter_by(statut=statut)
    
    signalements = query.order_by(Signalement.date_signalement.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('agent/signalements.html', 
                         signalements=signalements, 
                         statut_filtre=statut)

@app.route('/signalement/<int:signalement_id>/affecter', methods=['GET', 'POST'])
@agent_required
def affecter_signalement(signalement_id):
    signalement = Signalement.query.get_or_404(signalement_id)
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        technicien_id = request.form.get('technicien_id')
        delai_heures = int(request.form.get('delai_heures', 4))
        urgence = request.form.get('urgence', 'normale')
        notes_agent = request.form.get('notes_agent', '')
        message_client = request.form.get('message_client', '')
        
        # Assigner le signalement à l'agent connecté
        signalement.agent_id = session['agent_id']
        signalement.statut = 'en_attente'
        signalement.date_prise_en_charge = datetime.utcnow()
        signalement.notes_agent = notes_agent
        signalement.urgence = urgence
        
        # Assigner le technicien
        if technicien_id:
            technicien = Technicien.query.get(technicien_id)
            if technicien:
                signalement.technicien_id = technicien_id
                signalement.technicien_assigne = technicien.nom_complet
                technicien.interventions_en_cours += 1
                technicien.interventions_totales += 1
                technicien.disponibilite = 'occupe'
        
        # Calculer le délai et la date d'intervention
        delai_intervention = f"{delai_heures} heures"
        date_intervention = datetime.utcnow() + timedelta(hours=delai_heures)
        
        signalement.delai_intervention = delai_intervention
        signalement.date_intervention = date_intervention
        
        # Envoyer notification au client (simulation)
        if message_client:
            signalement.message_client = message_client
            print(f"📧 Notification envoyée à {signalement.client.telephone}: {message_client}")
        
        db.session.commit()
        
        flash(f'Signalement #{signalement.id} affecté à {signalement.technicien_assigne} avec délai de {delai_intervention}!', 'success')
        return redirect(url_for('signalements_agent'))
    
    # Récupérer les techniciens disponibles
    techniciens = Technicien.query.filter_by(disponibilite='disponible').all()
    
    # Si le client a une zone, filtrer les techniciens par zone
    if signalement.client.zone:
        techniciens_zone = [t for t in techniciens if signalement.client.zone.lower() in t.zone_couverture.lower()]
        if techniciens_zone:
            techniciens = techniciens_zone
    
    return render_template('agent/affecter_signalement.html', 
                         signalement=signalement, 
                         techniciens=techniciens)

@app.route('/signalement/<int:signalement_id>/notifier-client', methods=['POST'])
@agent_required
def notifier_client(signalement_id):
    """Envoyer une notification au client avec le délai d'intervention"""
    signalement = Signalement.query.get_or_404(signalement_id)
    
    if request.method == 'POST':
        message = request.form.get('message', '')
        canal = request.form.get('canal', 'sms')  # sms, email, appel
        
        # Message par défaut si non fourni
        if not message:
            message = f"""Cher/Chère {signalement.client.prenom} {signalement.client.nom},

Votre signalement #{signalement.id} a été pris en charge.
Technicien assigné: {signalement.technicien_assigne or 'En cours d assignation'}
Délai d'intervention: {signalement.delai_intervention or 'En cours de définition'}
Date prévue: {signalement.date_intervention.strftime('%d/%m/%Y à %H:%M') if signalement.date_intervention else 'En cours de planification'}

Nous vous contacterons prochainement pour plus de détails.
Service WiFi
            """.strip()
        
        # Simuler l'envoi de notification
        print(f"📧 Envoi notification au client:")
        print(f"📱 Téléphone: {signalement.client.telephone}")
        print(f"📧 Email: {signalement.client.email}")
        print(f"📨 Canal: {canal}")
        print(f"💬 Message: {message}")
        
        # Marquer comme notifié
        signalement.message_client = message
        signalement.notification_envoyee = True
        db.session.commit()
        
        flash(f'Notification envoyée à {signalement.client.prenom} {signalement.client.nom}', 'success')
        return redirect(url_for('signalements_agent'))
    
    return render_template('agent/notifier_client.html', signalement=signalement)

@app.route('/signalement/<int:signalement_id>/confirmer-intervention', methods=['POST'])
@agent_required
def confirmer_intervention(signalement_id):
    """Confirmer que l'intervention a été effectuée"""
    signalement = Signalement.query.get_or_404(signalement_id)
    
    if request.method == 'POST':
        technicien_id = request.form.get('technicien_id')
        rapport = request.form.get('rapport', '')
        duree_intervention = request.form.get('duree_intervention', '')
        
        # Mettre à jour le statut
        signalement.statut = 'resolu'
        signalement.date_resolution = datetime.utcnow()
        signalement.rapport_intervention = rapport
        signalement.duree_intervention = duree_intervention
        
        # Libérer le technicien
        if technicien_id:
            technicien = Technicien.query.get(technicien_id)
            if technicien:
                technicien.interventions_en_cours -= 1
                technicien.disponibilite = 'disponible'
        
        db.session.commit()
        
        flash(f'Intervention #{signalement.id} marquée comme résolue', 'success')
        return redirect(url_for('signalements_agent'))
    
    return render_template('agent/confirmer_intervention.html', signalement=signalement)

@app.route('/techniciens')
@agent_required
def liste_techniciens():
    techniciens = Technicien.query.all()
    return render_template('agent/techniciens.html', techniciens=techniciens)

@app.route('/technicien/<int:technicien_id>/details')
@agent_required
def details_technicien(technicien_id):
    technicien = Technicien.query.get_or_404(technicien_id)
    signalements = Signalement.query.filter_by(technicien_id=technicien_id).order_by(Signalement.date_intervention.desc()).all()
    return render_template('agent/details_technicien.html', technicien=technicien, signalements=signalements)

@app.route('/signalement/<int:signalement_id>/traiter', methods=['GET', 'POST'])
@agent_required
def traiter_signalement(signalement_id):
    signalement = Signalement.query.get_or_404(signalement_id)
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        technicien_id = request.form.get('technicien')
        delai_heures = int(request.form.get('delai_heures', 4))
        notes_agent = request.form.get('notes_agent', '')
        
        # Assigner le signalement à l'agent connecté
        signalement.agent_id = session['agent_id']
        signalement.statut = 'en_attente'
        signalement.date_prise_en_charge = datetime.utcnow()
        signalement.notes_agent = notes_agent
        
        # Assigner le technicien
        if technicien_id:
            technicien = Technicien.query.get(technicien_id)
            if technicien:
                signalement.technicien_id = technicien_id
                signalement.technicien_assigne = technicien.nom_complet
                technicien.interventions_en_cours += 1
                technicien.interventions_totales += 1
                technicien.disponibilite = 'occupe'
        
        # Calculer le délai et la date d'intervention
        delai_intervention = f"{delai_heures} heures"
        date_intervention = datetime.utcnow() + timedelta(hours=delai_heures)
        
        signalement.delai_intervention = delai_intervention
        signalement.date_intervention = date_intervention
        
        db.session.commit()
        
        flash(f'Signalement #{signalement.id} traité avec succès', 'success')
        return redirect(url_for('signalements_agent'))
    
    techniciens = Technicien.query.filter_by(disponibilite='disponible').all()
    
    # Si le client a une zone, filtrer les techniciens par zone
    if signalement.client.zone:
        techniciens_zone = [t for t in techniciens if signalement.client.zone.lower() in t.zone_couverture.lower()]
        if techniciens_zone:
            techniciens = techniciens_zone
    
    return render_template('agent/traiter_signalement.html', 
                         signalement=signalement, 
                         techniciens=techniciens)

@app.route('/signaler', methods=['GET', 'POST'])
def signaler():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        telephone = request.form['telephone']
        zone = request.form['zone']
        description = request.form['description']
        
        client = Client.query.filter_by(telephone=telephone).first()
        
        if not client:
            client = Client(nom=nom, prenom=prenom, telephone=telephone, zone=zone)
            db.session.add(client)
            db.session.commit()
        
        signalement = Signalement(
            client_id=client.id,
            description=description
        )
        
        db.session.add(signalement)
        db.session.commit()
        
        flash('Votre signalement a été enregistré! Un agent du service va le traiter dans les plus brefs délais.', 'success')
        
        return redirect(url_for('confirmation_client', signalement_id=signalement.id))
    
    return render_template('signaler.html')

@app.route('/confirmation-client/<int:signalement_id>')
def confirmation_client(signalement_id):
    signalement = Signalement.query.get_or_404(signalement_id)
    return render_template('confirmation_client.html', signalement=signalement)

@app.route('/admin')
def admin():
    signalements = Signalement.query.order_by(Signalement.date_signalement.desc()).all()
    return render_template('admin.html', signalements=signalements)

@app.route('/api/signalements')
def api_signalements():
    signalements = Signalement.query.order_by(Signalement.date_signalement.desc()).all()
    result = []
    for s in signalements:
        result.append({
            'id': s.id,
            'client': f"{s.client.prenom} {s.client.nom}",
            'telephone': s.client.telephone,
            'zone': s.client.zone,
            'description': s.description,
            'date_signalement': s.date_signalement.isoformat(),
            'statut': s.statut,
            'delai_intervention': s.delai_intervention,
            'technicien_assigne': s.technicien_assigne,
            'agent': f"{s.agent.prenom} {s.agent.nom}" if s.agent else None,
            'date_prise_en_charge': s.date_prise_en_charge.isoformat() if s.date_prise_en_charge else None
        })
    return jsonify(result)

@app.route('/api/statistiques')
def api_statistiques():
    total_signalements = Signalement.query.count()
    nouveau = Signalement.query.filter_by(statut='nouveau').count()
    en_attente = Signalement.query.filter_by(statut='en_attente').count()
    en_cours = Signalement.query.filter_by(statut='en_cours').count()
    resolu = Signalement.query.filter_by(statut='resolu').count()
    
    return jsonify({
        'total': total_signalements,
        'nouveau': nouveau,
        'en_attente': en_attente,
        'en_cours': en_cours,
        'resolu': resolu
    })

# Fonction pour créer des agents par défaut
def create_default_agents():
    """Créer des agents par défaut si aucun n'existe"""
    if Agent.query.count() == 0:
        agents_data = [
            {
                'nom': 'Diop',
                'prenom': 'Mamadou',
                'email': 'mamadou.diop@wifiservice.com',
                'password': 'agent123',
                'role': 'superviseur'
            },
            {
                'nom': 'Fall',
                'prenom': 'Aïssa',
                'email': 'aissa.fall@wifiservice.com',
                'password': 'agent123',
                'role': 'agent'
            },
            {
                'nom': 'Sow',
                'prenom': 'Ibrahim',
                'email': 'ibrahim.sow@wifiservice.com',
                'password': 'agent123',
                'role': 'agent'
            }
        ]
        
        for agent_data in agents_data:
            agent = Agent(
                nom=agent_data['nom'],
                prenom=agent_data['prenom'],
                email=agent_data['email'],
                role=agent_data['role']
            )
            agent.set_password(agent_data['password'])
            db.session.add(agent)
        
        db.session.commit()
        print("Agents par défaut créés avec succès!")

# Fonction pour créer des techniciens par défaut
def create_default_techniciens():
    """Créer des techniciens par défaut si aucun n'existe"""
    if Technicien.query.count() == 0:
        techniciens_data = [
            {
                'nom': 'Matar',
                'prenom': '',
                'telephone': '771111111',
                'email': 'matar@technicien.com',
                'specialite': 'Réseau',
                'zone_couverture': 'Dakar, Plateau, Almadies',
                'disponibilite': 'disponible'
            },
            {
                'nom': 'Mamadou',
                'prenom': '',
                'telephone': '772222222',
                'email': 'mamadou@technicien.com',
                'specialite': 'Équipement',
                'zone_couverture': 'Pikine, Guédiawaye, Thiaroye',
                'disponibilite': 'disponible'
            },
            {
                'nom': 'Faty',
                'prenom': '',
                'telephone': '773333333',
                'email': 'faty@technicien.com',
                'specialite': 'Maintenance',
                'zone_couverture': 'Grand-Yoff, Mermoz, Sacré-Cœur',
                'disponibilite': 'disponible'
            },
            {
                'nom': 'Mansour',
                'prenom': '',
                'telephone': '774444444',
                'email': 'mansour@technicien.com',
                'specialite': 'Réseau',
                'zone_couverture': 'Yoff, Ouakam, Fann',
                'disponibilite': 'disponible'
            },
            {
                'nom': 'Emma',
                'prenom': '',
                'telephone': '775555555',
                'email': 'emma@technicien.com',
                'specialite': 'Équipement',
                'zone_couverture': 'Parcelles, Niayes, Patte d\'Oie',
                'disponibilite': 'disponible'
            },
            {
                'nom': 'Thomas',
                'prenom': '',
                'telephone': '776666666',
                'email': 'thomas@technicien.com',
                'specialite': 'Maintenance',
                'zone_couverture': 'Biscuiterie, Castors, Grand-Médine',
                'disponibilite': 'disponible'
            }
        ]
        
        for tech_data in techniciens_data:
            technicien = Technicien(
                nom=tech_data['nom'],
                prenom=tech_data['prenom'],
                telephone=tech_data['telephone'],
                email=tech_data['email'],
                specialite=tech_data['specialite'],
                zone_couverture=tech_data['zone_couverture'],
                disponibilite=tech_data['disponibilite']
            )
            db.session.add(technicien)
        
        db.session.commit()
        print("Techniciens par défaut créés avec succès!")

if __name__ == '__main__':
    print("Démarrage de l'application...")
    
    # Attendre que la base de données soit disponible
    if wait_for_db():
        print("Initialisation de la base de données...")
        with app.app_context():
            try:
                db.create_all()
                create_default_agents()
                create_default_techniciens()
                print("Base de données initialisée avec succès!")
            except Exception as e:
                print(f"Erreur lors de l'initialisation de la base de données: {e}")
        
        print("Démarrage du serveur Flask...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("Arrêt de l'application suite à l'échec de connexion à la base de données")
