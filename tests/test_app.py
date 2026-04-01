import unittest
import sys
import os

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, Signalement, Client, Agent, Technicien

class TestWiFiApp(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after each test method."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_index_page(self):
        """Test that the index page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Signalement WiFi', response.data)
    
    def test_signaler_page(self):
        """Test that the signalement form page loads correctly."""
        response = self.client.get('/signaler')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Signaler un d\xc3\xa9rangement', response.data)
    
    def test_models_creation(self):
        """Test that models can be created successfully."""
        with self.app.app_context():
            # Create a client
            client = Client(
                nom='Test',
                prenom='Client',
                telephone='771234567',
                zone='Dakar'
            )
            db.session.add(client)
            db.session.commit()
            
            # Create a signalement
            signalement = Signalement(
                client_id=client.id,
                description='Test signalement'
            )
            db.session.add(signalement)
            db.session.commit()
            
            # Verify creation
            self.assertIsNotNone(client.id)
            self.assertIsNotNone(signalement.id)
            self.assertEqual(signalement.client_id, client.id)
    
    def test_technicien_model(self):
        """Test that Technicien model works correctly."""
        with self.app.app_context():
            technicien = Technicien(
                nom='Test',
                prenom='Technicien',
                telephone='771234567',
                email='test@technicien.com',
                specialite='Réseau',
                zone_couverture='Dakar',
                disponibilite='disponible'
            )
            db.session.add(technicien)
            db.session.commit()
            
            # Test properties
            self.assertEqual(technicien.nom_complet, 'Test Technicien')
            self.assertEqual(technicien.statut_display, '✅ Disponible')
    
    def test_agent_model(self):
        """Test that Agent model works correctly."""
        with self.app.app_context():
            agent = Agent(
                nom='Test',
                prenom='Agent',
                email='test@agent.com',
                role='agent'
            )
            agent.set_password('test123')
            db.session.add(agent)
            db.session.commit()
            
            # Test password
            self.assertTrue(agent.check_password('test123'))
            self.assertFalse(agent.check_password('wrong'))
    
    def test_signalement_properties(self):
        """Test Signalement model properties."""
        with self.app.app_context():
            client = Client(
                nom='Test',
                prenom='Client',
                telephone='771234567',
                zone='Dakar'
            )
            db.session.add(client)
            db.session.commit()
            
            signalement = Signalement(
                client_id=client.id,
                description='Test signalement',
                statut='nouveau'
            )
            db.session.add(signalement)
            db.session.commit()
            
            # Test properties
            self.assertEqual(signalement.statut_display, '🆕 Nouveau')
            self.assertIsNone(signalement.technicien_obj)
    
    def test_database_connection(self):
        """Test that database connection works."""
        with self.app.app_context():
            # This should not raise an exception
            result = db.engine.execute('SELECT 1')
            self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()
