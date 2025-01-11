# test_auth.py
import unittest
from app import app, db, User
from werkzeug.security import generate_password_hash
import json

class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF tokens in testing
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
        
        # Create test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(test_user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up test environment after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_signup_success(self):
        """Test successful user registration"""
        response = self.app.post('/signup', data=dict(
            username='newuser',
            email='new@example.com',
            password='newpassword123'
        ), follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'new@example.com')
    
    def test_signup_duplicate_username(self):
        """Test registration with an existing username"""
        response = self.app.post('/signup', data=dict(
            username='testuser',  # This username already exists in setup
            email='unique@example.com',
            password='password123'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Username already exists', response.data)

    # def test_signup_duplicate_email(self):
    #     """Test registration with an existing email"""
    #     response = self.app.post('/signup', data=dict(
    #         username='uniqueuser',
    #         email='kingokingsleykaah@gmail.com',  # This email already exists in setup
    #         password='password123'
    #     ), follow_redirects=True)

    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn(b'Email already exists', response.data)

    
    def test_login_success(self):
        """Test successful login"""
        response = self.app.post('/login', data=dict(
            username='testuser',
            password='password123'
        ), follow_redirects=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in successfully', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = self.app.post('/login', data=dict(
            username='testuser',
            password='wrongpassword'
        ), follow_redirects=True)
            
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent username"""
        response = self.app.post('/login', data=dict(
            username='nonexistent',
            password='password123'
        ), follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)
    
    def test_logout(self):
        """Test logout functionality"""
        # First login
        self.app.post('/login', data=dict(
            username='testuser',
            password='password123'
        ), follow_redirects=True)
        
        # Then logout
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged out successfully', response.data)
    
    def test_password_security(self):
        """Test password hashing and verification"""
        user = User.query.filter_by(username='testuser').first()
        self.assertNotEqual(user.password_hash, 'password123')  # Password should be hashed
    
    def test_form_validation(self):
        """Test form validation requirements"""
        # Test empty username
        response = self.app.post('/signup', data=dict(
            username='',
            email='unique1@example.com',  # Changed to unique email
            password='password123'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test invalid email format
        response = self.app.post('/signup', data=dict(
            username='newuser',
            email='invalid-email',  # Invalid email format
            password='password123'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email format', response.data)

    
    # def test_session_handling(self):
    #     """Test session handling after login/logout"""
    #     # Login
    #     self.app.post('/login', data=dict(
    #         username='testuser',
    #         password='password123'
    #     ), follow_redirects=True)
        
    #     # Check if session contains user_id
    #     with self.app as c:
    #         response = c.get('/')
    #         self.assertIn('user_id', session)
            
    #     # Logout
    #     self.app.get('/logout', follow_redirects=True)
        
    #     # Check if session is cleared
    #     with self.app as c:
    #         response = c.get('/')
    #         self.assertNotIn('user_id', session)

    def test_password_complexity(self):
        """Test password complexity requirements"""
        response = self.app.post('/signup', data=dict(
            username='newuser',
            email='new@example.com',
            password='weak'  # Too short/simple
        ), follow_redirects=True)
        self.assertIn(b'Password must be at least 8 characters', response.data)

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        response = self.app.post('/login', data=dict(
            username="' OR '1'='1",
            password="' OR '1'='1"
        ), follow_redirects=True)
        self.assertIn(b'Invalid username or password', response.data)

    if __name__ == '__main__':
        unittest.main()
