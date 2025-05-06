"""
Migration script to add client_id and employee_code columns to the employee_profile table.
"""

from extensions import db
from flask import Flask
from config import Config

def run_migration():
    """Run the migration to add client_id and employee_code columns."""
    # Create a temporary Flask app to initialize the database connection
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        # Check if columns already exist
        conn = db.engine.connect()
        
        # Check if client_id column exists
        result = conn.execute("SHOW COLUMNS FROM employee_profile LIKE 'client_id'")
        client_id_exists = result.rowcount > 0
        
        # Check if employee_code column exists
        result = conn.execute("SHOW COLUMNS FROM employee_profile LIKE 'employee_code'")
        employee_code_exists = result.rowcount > 0
        
        # Add client_id column if it doesn't exist
        if not client_id_exists:
            print("Adding client_id column to employee_profile table...")
            conn.execute("ALTER TABLE employee_profile ADD COLUMN client_id INT NULL")
            conn.execute("ALTER TABLE employee_profile ADD CONSTRAINT fk_employee_client FOREIGN KEY (client_id) REFERENCES client(id) ON DELETE SET NULL")
            print("client_id column added successfully.")
        else:
            print("client_id column already exists.")
        
        # Add employee_code column if it doesn't exist
        if not employee_code_exists:
            print("Adding employee_code column to employee_profile table...")
            conn.execute("ALTER TABLE employee_profile ADD COLUMN employee_code VARCHAR(20) NULL")
            conn.execute("ALTER TABLE employee_profile ADD UNIQUE INDEX idx_employee_code (employee_code)")
            print("employee_code column added successfully.")
        else:
            print("employee_code column already exists.")
        
        # Create client table if it doesn't exist
        conn.execute("""
        CREATE TABLE IF NOT EXISTS client (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(10) NOT NULL,
            description TEXT NULL,
            contact_person VARCHAR(100) NULL,
            contact_email VARCHAR(100) NULL,
            contact_phone VARCHAR(20) NULL,
            address VARCHAR(255) NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            UNIQUE INDEX idx_client_code (code),
            CONSTRAINT fk_client_creator FOREIGN KEY (created_by) REFERENCES user(id) ON DELETE SET NULL
        )
        """)
        print("Client table created or already exists.")
        
        conn.close()

if __name__ == "__main__":
    run_migration()
