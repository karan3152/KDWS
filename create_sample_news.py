from datetime import datetime, timedelta
import random

from app import app, db
from models import User, EmployerProfile, NewsUpdate, ROLE_EMPLOYER


def create_sample_news():
    """Create sample news and update entries."""
    with app.app_context():
        # Check if we already have news updates
        if NewsUpdate.query.count() > 0:
            print("News updates already exist in the database.")
            return False
        
        # Get employer profiles
        employers = EmployerProfile.query.all()
        if not employers:
            # If no employers, create a default one
            default_user = User.query.filter_by(role=ROLE_EMPLOYER).first()
            if not default_user:
                print("No employer users found. Please run generate_sample_accounts.py first.")
                return False
            
            default_employer = EmployerProfile(
                user_id=default_user.id,
                company_name="HR Talent Solutions",
                department="Human Resources",
                contact_number="9876543210"
            )
            db.session.add(default_employer)
            db.session.commit()
            employers = [default_employer]
        
        # Sample news titles and content
        news_items = [
            {
                "title": "Welcome to HR Talent Solutions",
                "content": "We're excited to welcome you to our new employee onboarding portal. This system streamlines the document submission process and makes it easier for you to complete all necessary paperwork.",
                "link": None,
                "link_text": None
            },
            {
                "title": "Important: Document Submission Deadline",
                "content": "All new employees must complete their document submissions within 15 days of joining. Please ensure you upload all required documents and complete the online forms.",
                "link": None,
                "link_text": None
            },
            {
                "title": "Upcoming Orientation Session",
                "content": "We will be conducting an orientation session for all new employees on Thursday at 10:00 AM. Please join us to learn more about company policies and procedures.",
                "link": "https://meet.google.com/abc-defg-hij",
                "link_text": "Join Meeting"
            },
            {
                "title": "PF and ESI Registration Process",
                "content": "Your PF and ESI registration will be processed once all required documents are submitted and approved. You can track the status in your dashboard.",
                "link": None,
                "link_text": None
            },
            {
                "title": "Office Location and Transportation",
                "content": "Our office is located at 123 Business Park, Main Street. Company transportation is available from major locations in the city. Contact HR for schedule details.",
                "link": "https://maps.google.com/?q=Office+Location",
                "link_text": "View Map"
            },
            {
                "title": "HR Contact Information",
                "content": "For any queries regarding your onboarding process, please contact the HR department at hr@example.com or call 9876543210 during office hours (9 AM - 6 PM).",
                "link": "mailto:hr@example.com",
                "link_text": "Email HR"
            },
            {
                "title": "Employee Benefits Overview",
                "content": "Learn about the various benefits available to you as an employee, including health insurance, provident fund, gratuity, and more.",
                "link": None,
                "link_text": None
            }
        ]
        
        # Create news updates (some active, some inactive)
        for i, news in enumerate(news_items):
            # Randomly assign to an employer
            employer = random.choice(employers)
            
            # Set published date (some recent, some older)
            days_ago = random.randint(0, 30)
            published_date = datetime.now() - timedelta(days=days_ago)
            
            # First 5 are active, rest are inactive
            is_active = i < 5
            
            news_update = NewsUpdate(
                title=news["title"],
                content=news["content"],
                employer_id=employer.id,
                published_date=published_date,
                is_active=is_active,
                link=news["link"],
                link_text=news["link_text"]
            )
            db.session.add(news_update)
        
        db.session.commit()
        print(f"Created {len(news_items)} sample news updates successfully!")
        return True


if __name__ == "__main__":
    create_sample_news()