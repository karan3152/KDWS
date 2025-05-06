from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import User, EmployeeProfile, EmployerProfile, NewsUpdate, Image, db, PasswordResetToken, OTP
from forms import RegistrationForm, PasswordResetForm, TwoFactorForm, Enable2FAForm, LoginForm
from . import auth
import time
import pyotp
import logging
from utils.otp_utils import send_otp

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@auth.route('/register/employee', methods=['GET', 'POST'])
def register_employee():
    """Employee registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Create user
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            role='employee'
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()

        flash('Registration successful', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_employee.html')

@auth.route('/register/employer', methods=['GET', 'POST'])
def register_employer():
    """Employer registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Create user
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            role='employer'
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()

        # Create employer profile
        profile = EmployerProfile(
            user_id=user.id,
            company_name=request.form['company_name']
        )
        db.session.add(profile)
        db.session.commit()

        flash('Registration successful', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_employer.html')

# @auth.route('/login', methods=['GET', 'POST'])
# def login():
#     """User login route."""
#     if current_user.is_authenticated:
#         return redirect(url_for('main.index'))
#
#     if request.method == 'POST':
#         logging.debug('Login attempt for email: %s', request.form['email'])
#         user = User.query.filter_by(email=request.form['email']).first()
#         if user:
#             logging.debug('User found: %s', user.email)
#             if user.check_password(request.form['password']):
#                 logging.debug('Password check passed for user: %s', user.email)
#                 login_user(user)
#                 flash('Login successful', 'success')
#                 return redirect(url_for('main.index'))
#             else:
#                 logging.debug('Password check failed for user: %s', user.email)
#         else:
#             logging.debug('No user found with email: %s', request.form['email'])
#         flash('Invalid email or password', 'danger')
#
#     return render_template('auth/login.html')

# @auth.route('/logout')
# @login_required
# def logout():
#     """User logout route."""
#     logout_user()
#     flash('You have been logged out', 'info')
#     return redirect(url_for('main.index'))

@auth.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    """Password reset request route."""
    logger.debug("Password reset request route called")

    if current_user.is_authenticated:
        logger.debug(f"Authenticated user tried to access password reset: user_id={current_user.id}")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        logger.debug(f"Password reset requested for email: {email}, phone: {phone_number}")

        user = User.query.filter_by(email=email).first()

        if user:
            logger.debug(f"User found for password reset: user_id={user.id}, email={user.email}")
            # Generate OTP for password reset
            logger.debug(f"Generating OTP for password reset: user_id={user.id}")
            otp = OTP.generate_otp(user.id, 'password_reset')
            logger.debug(f"Generated OTP: {otp.otp_code}")

            # Send OTP via email and WhatsApp using the provided phone number
            logger.debug(f"Sending OTP to user: email={user.email}, phone={phone_number}")
            email_sent, whatsapp_sent = send_otp(user, otp.otp_code, 'password_reset', phone_number)
            logger.debug(f"OTP send results: email_sent={email_sent}, whatsapp_sent={whatsapp_sent}")

            # Show loading page first, then redirect to OTP verification
            logger.info(f"Showing OTP loading page for user_id={user.id}")
            return render_template('auth/otp_loading.html', user_id=user.id, purpose='password_reset')

            # The actual OTP sending will happen, and the JavaScript in the loading page
            # will redirect to the verify_otp page after a delay
        else:
            logger.warning(f"Password reset attempted for non-existent email: {email}")
            # Don't reveal that the email doesn't exist
            flash('If your email is registered, you will receive an OTP shortly.', 'info')
            return redirect(url_for('main.login'))

    return render_template('auth/reset_password_request.html')

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    if not reset_token or reset_token.is_expired():
        flash('Invalid or expired reset token', 'danger')
        return redirect(url_for('auth.reset_password_request'))

    if request.method == 'POST':
        # Get the user from the token's user_id
        user = User.query.get(reset_token.user_id)
        if not user:
            flash('User not found. Please try again or contact support.', 'danger')
            return redirect(url_for('auth.reset_password_request'))

        # Set the password and mark it as non-temporary
        user.set_password(request.form['password'], is_temporary=False)

        # If this is a first-time login, mark the account as activated
        if user.first_login:
            user.first_login = False
            flash('Your account has been activated successfully!', 'success')
        else:
            flash('Your password has been reset successfully!', 'success')

        db.session.delete(reset_token)
        db.session.commit()
        return redirect(url_for('main.login'))

    return render_template('auth/reset_password.html')

@auth.route('/verify-2fa', methods=['GET', 'POST'])
@login_required
def verify_2fa():
    """Route for 2FA verification."""
    if not current_user.two_factor_enabled:
        return redirect(url_for('main.index'))

    form = TwoFactorForm()
    if form.validate_on_submit():
        if current_user.verify_2fa(form.token.data):
            session['2fa_verified'] = True
            next_page = session.get('next')
            if next_page:
                session.pop('next')
                return redirect(next_page)
            return redirect(url_for('main.index'))
        flash('Invalid verification code. Please try again.', 'danger')
    return render_template('verify_2fa.html', form=form)

@auth.route('/enable-2fa', methods=['GET', 'POST'])
@login_required
def enable_2fa():
    """Route for enabling 2FA."""
    if current_user.two_factor_enabled:
        return redirect(url_for('main.index'))

    if not current_user.two_factor_secret:
        current_user.enable_2fa()

    form = Enable2FAForm()
    if form.validate_on_submit():
        if current_user.verify_2fa(form.token.data):
            current_user.two_factor_enabled = True
            db.session.commit()
            flash('Two-factor authentication has been enabled successfully.', 'success')
            return redirect(url_for('main.index'))
        flash('Invalid verification code. Please try again.', 'danger')

    qr_code = current_user.get_2fa_qr_code()
    return render_template('enable_2fa.html', form=form, qr_code=qr_code)

@auth.route('/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    """Route for disabling 2FA."""
    if not current_user.two_factor_enabled:
        return redirect(url_for('main.index'))

    current_user.disable_2fa()
    db.session.commit()
    flash('Two-factor authentication has been disabled.', 'success')
    return redirect(url_for('main.index'))

@auth.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Route for OTP verification."""
    user_id = request.args.get('user_id') or request.form.get('user_id')
    purpose = request.args.get('purpose') or request.form.get('purpose')

    logger.debug(f"Verify OTP route called with user_id={user_id}, purpose={purpose}")

    if not user_id or not purpose:
        logger.error("Missing parameters in verify_otp route")
        flash('Invalid request. Missing parameters.', 'danger')
        return redirect(url_for('main.login'))

    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        logger.debug(f"OTP verification attempt: entered_otp={entered_otp}")

        # Find the latest OTP for this user and purpose
        otp = OTP.query.filter_by(
            user_id=user_id,
            purpose=purpose,
            is_verified=False
        ).order_by(OTP.created_at.desc()).first()

        if not otp:
            logger.warning(f"No active OTP found for user_id={user_id}, purpose={purpose}")
            flash('No active OTP found. Please request a new one.', 'danger')
            if purpose == 'password_reset':
                return redirect(url_for('auth.reset_password_request'))
            else:
                return redirect(url_for('auth.activate_account'))

        if otp.is_expired():
            logger.warning(f"OTP has expired for user_id={user_id}, purpose={purpose}, created_at={otp.created_at}, expires_at={otp.expires_at}")
            flash('OTP has expired. Please request a new one.', 'danger')
            if purpose == 'password_reset':
                return redirect(url_for('auth.reset_password_request'))
            else:
                return redirect(url_for('auth.activate_account'))

        logger.debug(f"Verifying OTP: entered={entered_otp}, actual={otp.otp_code}")
        if otp.verify(entered_otp):
            logger.info(f"OTP verified successfully for user_id={user_id}, purpose={purpose}")
            if purpose == 'password_reset':
                # Generate a password reset token
                token = user.create_reset_token()
                flash('OTP verified successfully! Please set your new password.', 'success')
                return redirect(url_for('auth.reset_password', token=token))
            else:  # account_activation
                # Generate a password reset token for account activation
                token = user.create_reset_token()
                flash('OTP verified successfully! Please set your password to activate your account.', 'success')
                return redirect(url_for('auth.reset_password', token=token))
        else:
            logger.warning(f"Invalid OTP entered: entered={entered_otp}, actual={otp.otp_code}")
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('auth/verify_otp.html', user_id=user_id, purpose=purpose)

@auth.route('/resend-otp')
def resend_otp():
    """Route for resending OTP."""
    user_id = request.args.get('user_id')
    purpose = request.args.get('purpose')

    logger.debug(f"Resend OTP route called with user_id={user_id}, purpose={purpose}")

    if not user_id or not purpose:
        logger.error("Missing parameters in resend_otp route")
        flash('Invalid request. Missing parameters.', 'danger')
        return redirect(url_for('main.login'))

    user = User.query.get(user_id)
    if not user:
        logger.error(f"User not found in resend_otp route: user_id={user_id}")
        flash('User not found.', 'danger')
        return redirect(url_for('main.login'))

    # Generate a new OTP
    logger.debug(f"Generating new OTP for user_id={user.id}, purpose={purpose}")
    otp = OTP.generate_otp(user.id, purpose)
    logger.debug(f"Generated OTP: {otp.otp_code}")

    # Send OTP via email and WhatsApp
    logger.debug(f"Sending OTP to user: email={user.email}")
    email_sent, whatsapp_sent = send_otp(user, otp.otp_code, purpose)
    logger.debug(f"OTP send results: email_sent={email_sent}, whatsapp_sent={whatsapp_sent}")

    # Show loading page first, then redirect to OTP verification
    logger.info(f"Showing OTP loading page for resend to user_id={user.id}")
    return render_template('auth/otp_loading.html', user_id=user_id, purpose=purpose)

@auth.route('/activate-account', methods=['GET', 'POST'])
def activate_account():
    """Route for first-time employee account activation."""
    logger.debug("Account activation route called")

    if current_user.is_authenticated:
        logger.debug(f"Authenticated user tried to access account activation: user_id={current_user.id}")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        logger.debug(f"Account activation requested for employee_id={employee_id}, email={email}, phone={phone_number}")

        # Find the user by email
        logger.debug(f"Looking up user by email: {email}")
        user = User.query.filter_by(email=email).first()

        if user and user.is_employee() and user.first_login:
            logger.debug(f"User found for account activation: user_id={user.id}, email={user.email}, username={user.username}")
            # Check if the employee ID matches (assuming employee ID is stored in username)
            if user.username == employee_id:
                logger.debug(f"Employee ID matches for user_id={user.id}")
                # Generate OTP for account activation
                logger.debug(f"Generating OTP for account activation: user_id={user.id}")
                otp = OTP.generate_otp(user.id, 'account_activation')
                logger.debug(f"Generated OTP: {otp.otp_code}")

                # Send OTP via email and WhatsApp using the provided phone number
                logger.debug(f"Sending OTP to user: email={user.email}, phone={phone_number}")
                email_sent, whatsapp_sent = send_otp(user, otp.otp_code, 'account_activation', phone_number)
                logger.debug(f"OTP send results: email_sent={email_sent}, whatsapp_sent={whatsapp_sent}")

                # Show loading page first, then redirect to OTP verification
                logger.info(f"Showing OTP loading page for user_id={user.id}")
                return render_template('auth/otp_loading.html', user_id=user.id, purpose='account_activation')

                # The actual OTP sending will happen, and the JavaScript in the loading page
                # will redirect to the verify_otp page after a delay
            else:
                logger.warning(f"Employee ID mismatch for account activation: provided={employee_id}, actual={user.username}")
                flash('Employee ID does not match the email address.', 'danger')
        else:
            logger.warning(f"Account activation failed: email={email}, user_exists={user is not None}, is_employee={user.is_employee() if user else False}, first_login={user.first_login if user else False}")
            flash('No account found with these credentials or account is already activated.', 'danger')

    return render_template('auth/activate_account.html')