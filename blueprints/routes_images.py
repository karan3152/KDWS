from flask import send_from_directory, current_app, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from models import Image, db

from blueprints import images

@images.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@images.route('/profile_photos/<path:filename>')
def profile_photo(filename):
    """Serve profile photos."""
    return send_from_directory(os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_photos'), filename)

@images.route('/family_photos/<path:filename>')
def family_photo(filename):
    """Serve family member photos."""
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'uploads', 'family_photos'), filename)

@images.route('/family_documents/<path:filename>')
def family_document(filename):
    """Serve family member documents like Aadhar cards."""
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'uploads', 'family_documents'), filename)

@images.route('/manage')
@login_required
def manage_images():
    """Manage images route."""
    if not (current_user.is_employer() or current_user.is_admin()):
        flash('Access denied. Employer or admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get images uploaded by the current user
    if current_user.is_admin():
        # Admins can see all images
        images_list = Image.query.order_by(Image.upload_date.desc()).all()
    else:
        # Employers can only see their own images
        images_list = Image.query.filter_by(uploaded_by=current_user.username).order_by(Image.upload_date.desc()).all()

    return render_template('manage_images.html', images=images_list)

@images.route('/employer/upload', methods=['GET', 'POST'])
@login_required
def employer_upload_image():
    """Employer image upload route."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Check if the post request has the file part
        if 'image' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['image']

        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)

            # Create directory structure for showcase images
            showcase_dir = os.path.join(current_app.root_path, 'static', 'img', 'showcase')
            os.makedirs(showcase_dir, exist_ok=True)

            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"showcase_{timestamp}_{filename}"

            # Save the file
            file_path = os.path.join(showcase_dir, unique_filename)
            file.save(file_path)

            # Create relative path for database
            relative_path = os.path.join('img', 'showcase', unique_filename)
            # Convert backslashes to forward slashes for web URL compatibility
            relative_path = relative_path.replace('\\', '/')

            # Save image info to database
            new_image = Image(
                title=request.form['title'],
                description=request.form.get('description', ''),
                file_path=relative_path,
                uploaded_by=current_user.username,
                upload_date=datetime.now()
            )
            db.session.add(new_image)
            db.session.commit()

            flash('Image uploaded successfully!', 'success')
            return redirect(url_for('images.manage_images'))
        else:
            flash('Invalid file type. Only images are allowed.', 'danger')

    return render_template('employer/upload_image.html')

@images.route('/admin/upload', methods=['GET', 'POST'])
@login_required
def admin_upload_image():
    """Admin image upload route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Check if the post request has the file part
        if 'image' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['image']

        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)

            # Create directory structure for showcase images
            showcase_dir = os.path.join(current_app.root_path, 'static', 'img', 'showcase')
            os.makedirs(showcase_dir, exist_ok=True)

            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"showcase_{timestamp}_{filename}"

            # Save the file
            file_path = os.path.join(showcase_dir, unique_filename)
            file.save(file_path)

            # Create relative path for database
            relative_path = os.path.join('img', 'showcase', unique_filename)
            # Convert backslashes to forward slashes for web URL compatibility
            relative_path = relative_path.replace('\\', '/')

            # Save image info to database
            new_image = Image(
                title=request.form['title'],
                description=request.form.get('description', ''),
                file_path=relative_path,
                uploaded_by=current_user.username,
                upload_date=datetime.now()
            )
            db.session.add(new_image)
            db.session.commit()

            flash('Image uploaded successfully!', 'success')
            return redirect(url_for('images.manage_images'))
        else:
            flash('Invalid file type. Only images are allowed.', 'danger')

    return render_template('admin/upload_image.html')

@images.route('/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    """Delete an image."""
    if not (current_user.is_employer() or current_user.is_admin()):
        flash('Access denied. Employer or admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    image = Image.query.get_or_404(image_id)

    # Check if the current user is the uploader or an admin
    if image.uploaded_by != current_user.username and not current_user.is_admin():
        flash('Access denied. You can only delete your own images.', 'danger')
        return redirect(url_for('images.manage_images'))

    # Delete the file from the filesystem
    file_path = os.path.join(current_app.root_path, 'static', image.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete the database record
    db.session.delete(image)
    db.session.commit()

    flash('Image deleted successfully!', 'success')
    return redirect(url_for('images.manage_images'))

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS