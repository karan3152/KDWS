import pytest
from flask import url_for
from app import create_app, db
from models import User, Document
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
def admin_user(app):
    with app.app_context():
        user = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('adminpass123'),
            role='admin'
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def logged_in_admin(client, admin_user):
    with client:
        client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'adminpass123'
        })
        yield client

def test_admin_dashboard_access(logged_in_admin):
    response = logged_in_admin.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data

def test_admin_dashboard_unauthorized(client):
    response = client.get('/admin/dashboard')
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.location

def test_employers_list(logged_in_admin):
    # Create some test employers
    employer1 = User(
        username='employer1',
        email='employer1@example.com',
        password_hash=generate_password_hash('testpass123'),
        role='employer'
    )
    employer2 = User(
        username='employer2',
        email='employer2@example.com',
        password_hash=generate_password_hash('testpass123'),
        role='employer'
    )
    db.session.add(employer1)
    db.session.add(employer2)
    db.session.commit()

    response = logged_in_admin.get('/admin/employers')
    assert response.status_code == 200
    assert b'employer1' in response.data
    assert b'employer2' in response.data

def test_employees_list(logged_in_admin):
    # Create some test employees
    employee1 = User(
        username='employee1',
        email='employee1@example.com',
        password_hash=generate_password_hash('testpass123'),
        role='employee'
    )
    employee2 = User(
        username='employee2',
        email='employee2@example.com',
        password_hash=generate_password_hash('testpass123'),
        role='employee'
    )
    db.session.add(employee1)
    db.session.add(employee2)
    db.session.commit()

    response = logged_in_admin.get('/admin/employees')
    assert response.status_code == 200
    assert b'employee1' in response.data
    assert b'employee2' in response.data

def test_documents_list(logged_in_admin):
    # Create some test documents
    doc1 = Document(
        title='Test Document 1',
        description='Test Description 1',
        file_path='/test/path1.pdf',
        status='pending'
    )
    doc2 = Document(
        title='Test Document 2',
        description='Test Description 2',
        file_path='/test/path2.pdf',
        status='approved'
    )
    db.session.add(doc1)
    db.session.add(doc2)
    db.session.commit()

    response = logged_in_admin.get('/admin/documents')
    assert response.status_code == 200
    assert b'Test Document 1' in response.data
    assert b'Test Document 2' in response.data

def test_document_approval(logged_in_admin):
    # Create a test document
    doc = Document(
        title='Test Document',
        description='Test Description',
        file_path='/test/path.pdf',
        status='pending'
    )
    db.session.add(doc)
    db.session.commit()

    response = logged_in_admin.post(f'/admin/documents/{doc.id}/approve')
    assert response.status_code == 302  # Redirect
    assert '/admin/documents' in response.location

    # Verify document was approved
    updated_doc = Document.query.get(doc.id)
    assert updated_doc.status == 'approved'

def test_document_rejection(logged_in_admin):
    # Create a test document
    doc = Document(
        title='Test Document',
        description='Test Description',
        file_path='/test/path.pdf',
        status='pending'
    )
    db.session.add(doc)
    db.session.commit()

    response = logged_in_admin.post(f'/admin/documents/{doc.id}/reject')
    assert response.status_code == 302  # Redirect
    assert '/admin/documents' in response.location

    # Verify document was rejected
    updated_doc = Document.query.get(doc.id)
    assert updated_doc.status == 'rejected' 