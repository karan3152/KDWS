from flask import Flask
from extensions import db
from models import Document

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)

with app.app_context():
    docs = Document.query.all()
    print('All documents:')
    for doc in docs:
        print(f'ID: {doc.id}, Type: {doc.document_type}, Status: {doc.status}, Employee ID: {doc.employee_id}')
