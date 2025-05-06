"""
Script to run database migrations.
"""

from migrations.add_client_columns import run_migration

if __name__ == "__main__":
    print("Running database migrations...")
    run_migration()
    print("Migrations completed successfully.")
