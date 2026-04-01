# � Système de Signalement WiFi

Application web de gestion des signements de dérangements WiFi avec suivi en temps réel pour les clients.

## 🎯 Fonctionnalités

### Pour les Clients
- 📝 Signalement de problèmes WiFi
- 🔍 Suivi en temps réel des interventions
- 📱 Notifications SMS/Email
- 📊 Timeline visuelle du traitement

### Pour les Agents
- 👤 Gestion des signalements
- 🔧 Affectation aux techniciens
- ⏰ Définition des délais d'intervention
- 📊 Tableau de bord statistique

### Pour les Superviseurs
- 👥 Gestion des comptes agents
- 📈 Administration complète
- 🎛️ Contrôle d'accès

## 🏗️ Architecture Technique

### Backend
- **Framework**: Flask (Python)
- **Base de données**: MySQL
- **ORM**: SQLAlchemy
- **Authentification**: Sessions Flask

### Frontend
- **Framework**: Bootstrap 5
- **Icônes**: Font Awesome 6
- **Design**: Responsive et moderne

### Infrastructure
- **Conteneurisation**: Docker & Docker Compose
- **Base de données**: MySQL en conteneur
- **Web**: Application Flask en conteneur

## � CI/CD Pipeline

Le projet utilise GitHub Actions pour l'intégration continue et le déploiement continu:

### 🚀 Pipeline Automatisé

**Déclencheurs:**
- Push sur la branche `main`
- Pull Request vers `main`
- Release (tags `v*`)

**Étapes:**
1. **Tests** - Validation syntaxe et imports
2. **Build** - Construction image Docker multi-architecture
3. **Security Scan** - Analyse de vulnérabilités Trivy
4. **Deploy** - Déploiement staging/production
5. **Notify** - Notifications Slack et résumé

### 📦 Docker Hub Integration

**Images générées:**
- `mado87464/wifi-app:latest` - Dernière version main
- `mado87464/wifi-app:v1.0.0` - Version taguée
- `mado87464/wifi-app:main-sha` - Commit spécifique

**Multi-architecture:**
- ✅ Linux AMD64
- ✅ Linux ARM64

### 🔧 Configuration Requise

**Secrets GitHub:**
- `DOCKER_USERNAME` - Nom d'utilisateur Docker Hub
- `DOCKER_PASSWORD` - Token d'accès Docker Hub
- `SLACK_WEBHOOK_URL` - Webhook Slack (optionnel)

**SonarCloud:**
- Analyse de qualité de code intégrée
- `SONAR_TOKEN` configuré dans les secrets

## �🚀 Installation

### Prérequis
- Docker et Docker Compose
- Git

### Démarrage rapide
```bash
# Cloner le repository
git clone https://github.com/mado87464-sketch/WIFI.git
cd WIFI

# Démarrer avec Docker Compose
docker-compose up -d

# Accès à l'application
# Client: http://localhost:5000
# Agent: http://localhost:5000/login-agent
networks:
  wifi-network:
    driver: bridge
```

### Ports utilisés
- **App 1** : 5000 (externe) → 5000 (interne)
- **App 2** : 5001 (externe) → 5000 (interne)
- **MySQL** : 3306 (externe) → 3306 (interne)

## 📊 API Endpoints

### Signalements
- `GET /api/signalements` : Liste de tous les signalements
- `GET /api/statistiques` : Statistiques des signalements

### Format de réponse JSON
```json
{
  "id": 1,
  "client": "Jean Dupont",
  "telephone": "77 123 45 67",
  "zone": "Grand-Yoff",
  "description": "Connexion intermittente",
  "date_signalement": "2024-01-01T10:00:00",
  "statut": "en attente",
  "delai_intervention": "4 heures",
  "technicien_assigne": "Technicien Alpha"
}
```

## 🔧 Configuration

### Variables d'environnement
- `DATABASE_URL` : URL de connexion à la base de données
- `SECRET_KEY` : Clé secrète Flask

### Base de données
- **SGBD** : MySQL 8.0
- **Base** : wifi_derangement
- **Tables** : clients, signalements

## 📈 Monitoring et Déploiement

### Health checks
```yaml
healthcheck:
  test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
  timeout: 20s
  retries: 10
```

### Logs
```bash
# Voir les logs de tous les services
docker-compose logs

# Logs d'un service spécifique
docker-compose logs app
```

## 🎨 Personnalisation

### Ajouter un technicien
Modifier la liste dans `app.py` :
```python
techniciens = ["Technicien Alpha", "Technicien Beta", "Technicien Gamma", "Technicien Delta"]
```

### Modifier les délais d'intervention
```python
delai_heures = random.randint(2, 24)  # Entre 2 et 24 heures
```

## 🚀 Déploiement sur Docker Hub

### Build et push
```bash
# Build l'image
docker build -t votre-username/wifi-derangement .

# Tag et push
docker tag wifi-derangement:latest votre-username/wifi-derangement:latest
docker push votre-username/wifi-derangement:latest
```

### CI/CD avec GitHub Actions
Créer `.github/workflows/docker.yml` pour l'automatisation.

## 📝 Notes de développement

### Points forts
- ✅ Respect des contraintes techniques (Flask, Docker, MySQL, réseau)
- ✅ Interface utilisateur moderne et responsive
- ✅ API RESTful pour intégration
- ✅ Communication inter-conteneurs fonctionnelle
- ✅ Scalabilité horizontale possible

### Améliorations possibles
- Authentication des utilisateurs
- Notifications SMS/Email
- Interface mobile native
- Système de tickets avancé
- Intégration avec des outils de monitoring

## 📞 Support

Pour toute question ou problème technique :
- 📧 Email : support@wifi-derangement.com
- 📱 Téléphone : 77 000 00 00

---

**Développé par :** [Votre Nom]  
**Projet DEVNET - L3 RI - ISI Keur Massar**  
**Date :** Avril 2026
