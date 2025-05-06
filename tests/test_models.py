import pytest
from app import create_app, db
from models import User, EmployeeProfile, EmployerProfile, Document, FamilyMember

@pytest.fixture
def app():
    app = create_app('config.TestConfig')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_user_creation(app):
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            role='employee'
        )
        db.session.add(user)
        db.session.commit()

        retrieved_user = User.query.filter_by(email='test@example.com').first()
        assert retrieved_user is not None
        assert retrieved_user.username == 'testuser'
        assert retrieved_user.role == 'employee'

def test_employee_profile_creation(app):
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            role='employee'
        )
        db.session.add(user)
        db.session.commit()

        profile = EmployeeProfile(
            user_id=user.id,
            first_name='John',
            last_name='Doe',
            phone_number='1234567890',
            address='123 Test St',
            date_of_birth='1990-01-01',
            gender='Male',
            marital_status='Single',
            nationality='American',
            emergency_contact='Jane Doe',
            emergency_phone='0987654321'
        )
        db.session.add(profile)
        db.session.commit()

        retrieved_profile = EmployeeProfile.query.filter_by(user_id=user.id).first()
        assert retrieved_profile is not None
        assert retrieved_profile.first_name == 'John'
        assert retrieved_profile.last_name == 'Doe'

def test_employer_profile_creation(app):
    with app.app_context():
        user = User(
            username='testemployer',
            email='employer@example.com',
            password_hash='hashed_password',
            role='employer'
        )
        db.session.add(user)
        db.session.commit()

        profile = EmployerProfile(
            user_id=user.id,
            company_name='Test Company',
            company_address='456 Business Ave',
            company_phone='1234567890',
            company_email='contact@testcompany.com',
            industry='Technology',
            company_size='50-100',
            company_website='https://testcompany.com'
        )
        db.session.add(profile)
        db.session.commit()

        retrieved_profile = EmployerProfile.query.filter_by(user_id=user.id).first()
        assert retrieved_profile is not None
        assert retrieved_profile.company_name == 'Test Company'
        assert retrieved_profile.industry == 'Technology'

def test_document_creation(app):
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            role='employee'
        )
        db.session.add(user)
        db.session.commit()

        document = Document(
            user_id=user.id,
            title='Test Document',
            description='Test Description',
            file_path='/test/path.pdf',
            document_type='resume',
            status='pending'
        )
        db.session.add(document)
        db.session.commit()

        retrieved_document = Document.query.filter_by(user_id=user.id).first()
        assert retrieved_document is not None
        assert retrieved_document.title == 'Test Document'
        assert retrieved_document.status == 'pending'

def test_family_member_creation(app):
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            role='employee'
        )
        db.session.add(user)
        db.session.commit()

        family_member = FamilyMember(
            user_id=user.id,
            name='Jane Doe',
            relationship='Spouse',
            date_of_birth='1992-01-01',
            occupation='Teacher',
            phone_number='1234567890'
        )
        db.session.add(family_member)
        db.session.commit()

        retrieved_member = FamilyMember.query.filter_by(user_id=user.id).first()
        assert retrieved_member is not None
        assert retrieved_member.name == 'Jane Doe'
        assert retrieved_member.relationship == 'Spouse'

def test_user_deletion_cascades(app):
    with app.app_context():
        # Create user with profile and documents
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            role='employee'
        )
        db.session.add(user)
        db.session.commit()

        profile = EmployeeProfile(
            user_id=user.id,
            first_name='John',
            last_name='Doe'
        )
        db.session.add(profile)

        document = Document(
            user_id=user.id,
            title='Test Document',
            file_path='/test/path.pdf'
        )
        db.session.add(document)

        family_member = FamilyMember(
            user_id=user.id,
            name='Jane Doe',
            relationship='Spouse'
        )
        db.session.add(family_member)
        db.session.commit()

        # Delete user
        db.session.delete(user)
        db.session.commit()

        # Verify cascading delete
        assert User.query.get(user.id) is None
        assert EmployeeProfile.query.filter_by(user_id=user.id).first() is None
        assert Document.query.filter_by(user_id=user.id).first() is None
        assert FamilyMember.query.filter_by(user_id=user.id).first() is None 