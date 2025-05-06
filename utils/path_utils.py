import os
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

def normalize_path(file_path):
    """
    Normalize a file path for consistent storage and retrieval.
    Ensures paths are relative to the static directory and use forward slashes.

    Args:
        file_path (str): The file path to normalize

    Returns:
        str: Normalized path relative to static directory with forward slashes
    """
    # If path is already relative to static, extract it
    if 'static/' in file_path:
        relative_path = file_path.split('static/')[-1]
    else:
        # Check if it's already a relative path
        if file_path.startswith('uploads/'):
            relative_path = file_path
        else:
            # Try to make it relative to static
            try:
                relative_path = os.path.relpath(
                    file_path,
                    os.path.join(current_app.root_path, 'static')
                )
            except ValueError:
                # If that fails, just use the path as is
                relative_path = file_path

    # Ensure forward slashes for web URL compatibility
    relative_path = relative_path.replace('\\', '/')

    # Log the normalization for debugging
    current_app.logger.info(f"Normalized path: {file_path} -> {relative_path}")

    return relative_path

def get_full_path(relative_path):
    """
    Get the full file system path from a relative path.
    Tries multiple path formats to handle different path styles.

    Args:
        relative_path (str): Relative path to convert to full path

    Returns:
        tuple: (full_path, file_exists)
    """
    # Ensure forward slashes for consistency
    relative_path = relative_path.replace('\\', '/')

    # Try standard path
    full_path = os.path.join(current_app.root_path, 'static', relative_path)
    if os.path.exists(full_path):
        return full_path, True

    # Try with backslashes
    alt_path = os.path.join(current_app.root_path, 'static', relative_path.replace('/', '\\'))
    if os.path.exists(alt_path):
        return alt_path, True

    # Try with absolute Windows path
    windows_path = f"D:\\HRwebsite\\WorkforceHive1\\WorkforceHive\\static\\{relative_path}"
    if os.path.exists(windows_path):
        return windows_path, True

    # Log failure
    current_app.logger.error(f"File not found at any of these paths: {full_path}, {alt_path}, {windows_path}")

    # Return the standard path and False for file_exists
    return full_path, False

def fix_family_member_paths():
    """
    Fix the paths in the family_member table by converting absolute paths to relative paths.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from models import FamilyMember
        from extensions import db

        # Get all family members
        family_members = FamilyMember.query.all()
        count = 0

        for member in family_members:
            updated = False

            # Fix photo path if it's an absolute path
            if member.photo_path and ('\\' in member.photo_path or ':' in member.photo_path):
                old_path = member.photo_path
                member.photo_path = normalize_path(member.photo_path)
                current_app.logger.info(f"Updated photo path: {old_path} -> {member.photo_path}")
                updated = True

            # Fix aadhar card path if it's an absolute path
            if member.aadhar_card_path and ('\\' in member.aadhar_card_path or ':' in member.aadhar_card_path):
                old_path = member.aadhar_card_path
                member.aadhar_card_path = normalize_path(member.aadhar_card_path)
                current_app.logger.info(f"Updated aadhar card path: {old_path} -> {member.aadhar_card_path}")
                updated = True

            if updated:
                count += 1

        # Commit the changes if any were made
        if count > 0:
            db.session.commit()
            current_app.logger.info(f"Fixed paths for {count} family members")

        return True
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error fixing family member paths: {e}")
        db.session.rollback()
        return False
    except Exception as e:
        current_app.logger.error(f"Error fixing family member paths: {e}")
        return False
