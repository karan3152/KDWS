from app import app, db
from models import NewsUpdate, EmployerProfile
from datetime import datetime, timedelta

def create_sample_news():
    """Create sample news and update entries."""
    with app.app_context():
        # Get the employer profile for the news
        employer = EmployerProfile.query.first()
        
        if not employer:
            print("No employer found in the database. Please create an employer account first.")
            return
        
        # Create a regular news update
        news1 = NewsUpdate(
            title="Welcome to HR Talent Solutions Portal",
            content="We are excited to launch our new HR Talent Solutions portal. This platform will help streamline employee onboarding and document management. Please contact the HR department if you have any questions.",
            is_active=True,
            employer_id=employer.id
        )
        
        # Create an interview notice
        interview_date = datetime.now() + timedelta(days=7)  # Interview scheduled for a week from now
        news2 = NewsUpdate(
            title="Software Developer Interview Notice",
            content="We are conducting interviews for the position of Software Developer. Candidates should bring their resume, ID proof, and educational certificates.",
            is_active=True,
            is_interview_notice=True,
            location_address="HR Talent Solutions Office, 3rd Floor, Tech Park, Bangalore - 560001",
            interview_date=interview_date,
            employer_id=employer.id
        )
        
        # Create another regular update
        news3 = NewsUpdate(
            title="New Document Upload Feature",
            content="We have added a new feature that allows employees to upload their documents directly through the portal. This includes Aadhar, PAN, bank details, and other required forms.",
            is_active=True,
            employer_id=employer.id
        )
        
        db.session.add(news1)
        db.session.add(news2)
        db.session.add(news3)
        db.session.commit()
        
        print("Created 3 sample news updates")

if __name__ == "__main__":
    create_sample_news()
    print("Sample news created successfully!")