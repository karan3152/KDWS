"""
Script to fix the paths in the family_member table
"""
import os
import sys

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from utils.path_utils import fix_family_member_paths

def run_fix():
    """Run the path fixing function within the app context"""
    with app.app_context():
        print("Fixing family member paths...")
        success = fix_family_member_paths()
        if success:
            print("Successfully fixed family member paths!")
        else:
            print("Failed to fix family member paths.")

if __name__ == "__main__":
    run_fix()
