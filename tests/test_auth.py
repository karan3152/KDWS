import pytest
from flask import url_for
from app import create_app, db
from models import User
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app('config.TestConfig')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

def test_register_employee(client):
    response = client.post('/register/employee', data={
        'username': 'testemployee',
        'email': 'test@example.com',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful' in response.data

def test_register_employer(client):
    response = client.post('/register/employer', data={
        'username': 'testemployer',
        'email': 'employer@example.com',
        'password': 'testpass123',
        'confirm_password': 'testpass123',
        'company_name': 'Test Company'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful' in response.data

def test_login(client):
    # Create a test user
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('testpass123'),
        role='employee'
    )
    db.session.add(user)
    db.session.commit()

    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Login successful' in response.data

def test_invalid_login(client):
    response = client.post('/login', data={
        'email': 'wrong@example.com',
        'password': 'wrongpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data

def test_logout(client):
    # First login
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('testpass123'),
        role='employee'
    )
    db.session.add(user)
    db.session.commit()

    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass123'
    })

    # Then logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' in response.data

def test_password_reset_request(client):
    # Create a test user
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('testpass123'),
        role='employee'
    )
    db.session.add(user)
    db.session.commit()

    response = client.post('/reset-password-request', data={
        'email': 'test@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Check your email for the instructions to reset your password' in response.data

def test_password_reset(client):
    # Create a test user and token
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('testpass123'),
        role='employee'
    )
    db.session.add(user)
    db.session.commit()

    # Create a reset token (in a real app, this would be generated properly)
    token = 'test-token'
    user.create_reset_token(token)

    response = client.post(f'/reset-password/{token}', data={
        'password': 'newpass123',
        'confirm_password': 'newpass123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Your password has been reset' in response.data 