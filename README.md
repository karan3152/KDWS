# KDWS HR Management System

Enables HR to connect with candidates quickly, efficiently, and effortlessly.

## Features

- User authentication and authorization
- Document management
- Employee profiles
- Employer profiles
- Admin dashboard
- Client management
- WhatsApp integration

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Create a `.env` file with the following variables:
   ```
   # Email Configuration
   EMAIL_USER=your_email@example.com
   EMAIL_PASSWORD=your_email_password
   SMTP_SERVER=smtp.example.com
   SMTP_PORT=587

   # WhatsApp API Configuration (if needed)
   WHATSAPP_API_URL=https://api.whatsapp.com/v1/messages
   WHATSAPP_API_KEY=your_whatsapp_api_key

   # Other Configuration
   SECRET_KEY=your_secret_key
   DATABASE_URI=sqlite:///app.db
   ```
6. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

## Running the Application

### Development

```
python run.py
```

### Production

```
gunicorn run:app
```

## Testing

```
python -m pytest
```

## Deployment

This application can be deployed to various platforms:

1. **GitHub** - For version control and CI/CD
   - Push your code to GitHub
   - Set up GitHub Actions for automated testing and deployment

2. **Heroku** - Using the Procfile included in the repository
   - Connect your GitHub repository to Heroku
   - Enable automatic deployments

3. **AWS, Azure, or Google Cloud** - Using Docker or directly on VMs
   - Deploy using a container service or directly on a VM
   - Set up a production database (PostgreSQL recommended)

4. **PythonAnywhere** - A simple platform for Python web applications
   - Upload your code and set up a WSGI configuration

## License

[MIT](LICENSE)
