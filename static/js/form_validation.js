// Form Validation for the Employee Data Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize validation for all forms
    const forms = document.querySelectorAll('form.needs-validation');
    initFormValidation(forms);
    
    // Initialize special form handling
    initPasswordValidation();
    initFileValidation();
    initAadharValidation();
    initEmployeeIdValidation();
});

/**
 * Initialize basic form validation
 * @param {NodeList} forms - Collection of form elements to validate
 */
function initFormValidation(forms) {
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(this)) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
        
        // Add input event listeners to clear errors as user types
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearValidationError(this);
            });
            
            input.addEventListener('blur', function() {
                validateField(this);
            });
        });
    });
}

/**
 * Validate an entire form
 * @param {HTMLFormElement} form - The form to validate
 * @returns {boolean} Whether the form is valid
 */
function validateForm(form) {
    let isValid = true;
    
    // Validate all inputs, selects, and textareas
    const fields = form.querySelectorAll('input, select, textarea');
    fields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Validate a single form field
 * @param {HTMLElement} field - The field to validate
 * @returns {boolean} Whether the field is valid
 */
function validateField(field) {
    clearValidationError(field);
    
    // Get validation attributes
    const isRequired = field.hasAttribute('required');
    const minLength = field.getAttribute('minlength');
    const maxLength = field.getAttribute('maxlength');
    const pattern = field.getAttribute('pattern');
    const type = field.getAttribute('type');
    
    // Skip disabled or non-required empty fields
    if (field.disabled || (!isRequired && !field.value.trim())) {
        return true;
    }
    
    // Required validation
    if (isRequired && !field.value.trim()) {
        showValidationError(field, 'This field is required');
        return false;
    }
    
    // Min length validation
    if (minLength && field.value.length < parseInt(minLength)) {
        showValidationError(field, `Must be at least ${minLength} characters`);
        return false;
    }
    
    // Max length validation
    if (maxLength && field.value.length > parseInt(maxLength)) {
        showValidationError(field, `Must be no more than ${maxLength} characters`);
        return false;
    }
    
    // Pattern validation
    if (pattern && !new RegExp(pattern).test(field.value)) {
        showValidationError(field, 'Invalid format');
        return false;
    }
    
    // Email validation
    if (type === 'email' && !validateEmail(field.value)) {
        showValidationError(field, 'Please enter a valid email address');
        return false;
    }
    
    // File validation
    if (type === 'file' && field.files.length > 0) {
        const file = field.files[0];
        const accept = field.getAttribute('accept');
        
        if (accept && !validateFileType(file, accept)) {
            showValidationError(field, 'Invalid file type');
            return false;
        }
    }
    
    // Add more validations as needed for specific fields
    if (field.classList.contains('aadhar-id') && !validateAadharId(field.value)) {
        showValidationError(field, 'Please enter a valid 12-digit Aadhar ID');
        return false;
    }
    
    if (field.classList.contains('employee-id') && !validateEmployeeId(field.value)) {
        showValidationError(field, 'Please enter a valid Employee ID');
        return false;
    }
    
    return true;
}

/**
 * Show a validation error for a field
 * @param {HTMLElement} field - The field with the error
 * @param {string} message - The error message to display
 */
function showValidationError(field, message) {
    // Add invalid class to the field
    field.classList.add('is-invalid');
    
    // Create or update error message
    let errorElement = field.nextElementSibling;
    if (!errorElement || !errorElement.classList.contains('invalid-feedback')) {
        errorElement = document.createElement('div');
        errorElement.className = 'invalid-feedback';
        field.parentNode.insertBefore(errorElement, field.nextSibling);
    }
    
    errorElement.textContent = message;
}

/**
 * Clear validation error for a field
 * @param {HTMLElement} field - The field to clear errors for
 */
function clearValidationError(field) {
    field.classList.remove('is-invalid');
    
    const errorElement = field.nextElementSibling;
    if (errorElement && errorElement.classList.contains('invalid-feedback')) {
        errorElement.textContent = '';
    }
}

/**
 * Validate an email address
 * @param {string} email - The email to validate
 * @returns {boolean} Whether the email is valid
 */
function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

/**
 * Validate file type against accepted types
 * @param {File} file - The file to validate
 * @param {string} acceptStr - The accept attribute string
 * @returns {boolean} Whether the file type is valid
 */
function validateFileType(file, acceptStr) {
    if (!acceptStr) return true;
    
    const acceptedTypes = acceptStr.split(',').map(type => type.trim());
    const fileType = file.type;
    
    for (const type of acceptedTypes) {
        // Check for exact match or wildcard match
        if (type === fileType || 
            (type.endsWith('/*') && fileType.startsWith(type.replace('/*', '/')))) {
            return true;
        }
    }
    
    return false;
}

/**
 * Initialize password validation
 */
function initPasswordValidation() {
    const passwordForms = document.querySelectorAll('form.password-validation');
    
    passwordForms.forEach(form => {
        const passwordField = form.querySelector('input[name="password"]');
        const confirmField = form.querySelector('input[name="confirm_password"]');
        
        if (passwordField && confirmField) {
            // Add match validation on confirm field
            confirmField.addEventListener('blur', function() {
                if (this.value && this.value !== passwordField.value) {
                    showValidationError(this, 'Passwords do not match');
                }
            });
            
            // Add strength validation on password field
            passwordField.addEventListener('input', function() {
                validatePasswordStrength(this);
            });
        }
    });
}

/**
 * Validate password strength
 * @param {HTMLInputElement} passwordField - The password field
 */
function validatePasswordStrength(passwordField) {
    const password = passwordField.value;
    
    // Create strength meter if not present
    let strengthMeter = passwordField.parentNode.querySelector('.password-strength');
    if (!strengthMeter) {
        strengthMeter = document.createElement('div');
        strengthMeter.className = 'password-strength';
        passwordField.parentNode.insertBefore(strengthMeter, passwordField.nextSibling);
    }
    
    // Calculate strength
    let strength = 0;
    let feedback = [];
    
    if (password.length >= 8) {
        strength += 1;
    } else {
        feedback.push('Password should be at least 8 characters long');
    }
    
    if (/[A-Z]/.test(password)) {
        strength += 1;
    } else {
        feedback.push('Add uppercase letters');
    }
    
    if (/[a-z]/.test(password)) {
        strength += 1;
    } else {
        feedback.push('Add lowercase letters');
    }
    
    if (/[0-9]/.test(password)) {
        strength += 1;
    } else {
        feedback.push('Add numbers');
    }
    
    if (/[^A-Za-z0-9]/.test(password)) {
        strength += 1;
    } else {
        feedback.push('Add special characters');
    }
    
    // Update strength meter
    let strengthClass = '';
    let strengthText = '';
    
    if (strength === 0) {
        strengthClass = 'very-weak';
        strengthText = 'Very Weak';
    } else if (strength === 1) {
        strengthClass = 'weak';
        strengthText = 'Weak';
    } else if (strength === 2) {
        strengthClass = 'medium';
        strengthText = 'Medium';
    } else if (strength === 3) {
        strengthClass = 'strong';
        strengthText = 'Strong';
    } else {
        strengthClass = 'very-strong';
        strengthText = 'Very Strong';
    }
    
    strengthMeter.className = `password-strength ${strengthClass}`;
    strengthMeter.innerHTML = `
        <div class="strength-meter">
            <div class="strength-meter-fill" style="width: ${strength * 20}%"></div>
        </div>
        <div class="strength-text">${strengthText}</div>
        <div class="strength-feedback">${feedback.join(', ')}</div>
    `;
}

/**
 * Initialize file validation for PDF uploads
 */
function initFileValidation() {
    const fileInputs = document.querySelectorAll('input[type="file"][accept="application/pdf"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.files.length > 0) {
                const file = this.files[0];
                
                // Check file type
                if (file.type !== 'application/pdf') {
                    showValidationError(this, 'Please upload a PDF file');
                    this.value = ''; // Clear the input
                    return;
                }
                
                // Check file size (limit to 5MB)
                const maxSize = 5 * 1024 * 1024; // 5MB in bytes
                if (file.size > maxSize) {
                    showValidationError(this, 'File size should not exceed 5MB');
                    this.value = ''; // Clear the input
                    return;
                }
                
                clearValidationError(this);
            }
        });
    });
}

/**
 * Validate Aadhar ID format
 * @param {string} aadharId - The Aadhar ID to validate
 * @returns {boolean} Whether the Aadhar ID is valid
 */
function validateAadharId(aadharId) {
    // Simple validation for 12 digits
    return /^\d{12}$/.test(aadharId);
}

/**
 * Initialize Aadhar ID validation
 */
function initAadharValidation() {
    const aadharFields = document.querySelectorAll('.aadhar-id');
    
    aadharFields.forEach(field => {
        field.addEventListener('input', function() {
            // Allow only digits
            this.value = this.value.replace(/[^\d]/g, '');
            
            // Limit to 12 digits
            if (this.value.length > 12) {
                this.value = this.value.slice(0, 12);
            }
        });
    });
}

/**
 * Validate Employee ID format
 * @param {string} employeeId - The Employee ID to validate
 * @returns {boolean} Whether the Employee ID is valid
 */
function validateEmployeeId(employeeId) {
    // Employee ID format: EMP followed by numbers
    return /^EMP\d+$/.test(employeeId);
}

/**
 * Initialize Employee ID validation
 */
function initEmployeeIdValidation() {
    const employeeIdFields = document.querySelectorAll('.employee-id');
    
    employeeIdFields.forEach(field => {
        field.addEventListener('input', function() {
            // Ensure starts with EMP
            if (!this.value.startsWith('EMP')) {
                this.value = 'EMP' + this.value.replace(/^EMP/i, '');
            }
            
            // Allow only EMP followed by digits
            this.value = this.value.replace(/^EMP([^\d]*)/, 'EMP');
        });
    });
}
