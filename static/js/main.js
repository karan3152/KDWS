// Main JavaScript for the Employee Data Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any interactive elements
    initializeSidebar();
    initializeFlashMessages();
    initializeTooltips();
    initializeDropdowns();
});

/**
 * Initialize sidebar functionality
 */
function initializeSidebar() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebarToggle && sidebar && mainContent) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('sidebar-collapsed');
            mainContent.classList.toggle('main-content-expanded');
            
            // Store preference in localStorage
            if (sidebar.classList.contains('sidebar-collapsed')) {
                localStorage.setItem('sidebarCollapsed', 'true');
            } else {
                localStorage.setItem('sidebarCollapsed', 'false');
            }
        });
        
        // Check for stored preference
        if (localStorage.getItem('sidebarCollapsed') === 'true') {
            sidebar.classList.add('sidebar-collapsed');
            mainContent.classList.add('main-content-expanded');
        }
    }
    
    // Mobile sidebar toggle
    const mobileSidebarToggle = document.querySelector('.mobile-sidebar-toggle');
    if (mobileSidebarToggle && sidebar) {
        mobileSidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 992 && 
                !sidebar.contains(event.target) && 
                !mobileSidebarToggle.contains(event.target) &&
                sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
            }
        });
    }
}

/**
 * Initialize flash messages with auto-dismiss
 */
function initializeFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(message => {
        // Add close button if not present
        if (!message.querySelector('.close')) {
            const closeButton = document.createElement('button');
            closeButton.className = 'close';
            closeButton.innerHTML = '&times;';
            closeButton.style.position = 'absolute';
            closeButton.style.right = '10px';
            closeButton.style.top = '10px';
            closeButton.style.background = 'none';
            closeButton.style.border = 'none';
            closeButton.style.fontSize = '1.25rem';
            closeButton.style.fontWeight = 'bold';
            closeButton.style.cursor = 'pointer';
            
            closeButton.addEventListener('click', function() {
                message.style.display = 'none';
            });
            
            message.style.position = 'relative';
            message.appendChild(closeButton);
        }
        
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.5s ease';
            
            setTimeout(function() {
                message.style.display = 'none';
            }, 500);
        }, 5000);
    });
}

/**
 * Initialize tooltips on elements with data-tooltip attribute
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.style.position = 'relative';
        
        element.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            
            // Create tooltip element
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = tooltipText;
            tooltip.style.position = 'absolute';
            tooltip.style.bottom = 'calc(100% + 10px)';
            tooltip.style.left = '50%';
            tooltip.style.transform = 'translateX(-50%)';
            tooltip.style.padding = '5px 10px';
            tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            tooltip.style.color = '#fff';
            tooltip.style.borderRadius = '4px';
            tooltip.style.fontSize = '0.875rem';
            tooltip.style.whiteSpace = 'nowrap';
            tooltip.style.zIndex = '1000';
            tooltip.style.pointerEvents = 'none';
            
            // Add arrow
            const arrow = document.createElement('div');
            arrow.style.position = 'absolute';
            arrow.style.top = '100%';
            arrow.style.left = '50%';
            arrow.style.transform = 'translateX(-50%)';
            arrow.style.borderWidth = '5px';
            arrow.style.borderStyle = 'solid';
            arrow.style.borderColor = 'rgba(0, 0, 0, 0.8) transparent transparent transparent';
            
            tooltip.appendChild(arrow);
            this.appendChild(tooltip);
        });
        
        element.addEventListener('mouseleave', function() {
            const tooltip = this.querySelector('.tooltip');
            if (tooltip) {
                this.removeChild(tooltip);
            }
        });
    });
}

/**
 * Initialize dropdown menus
 */
function initializeDropdowns() {
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const dropdown = this.nextElementSibling;
            
            // Close all other dropdowns
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                if (menu !== dropdown) {
                    menu.classList.remove('show');
                }
            });
            
            // Toggle current dropdown
            dropdown.classList.toggle('show');
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    });
}

/**
 * Format date for display
 * @param {string|Date} dateString - The date to format
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format file size for display
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size string
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Show a confirmation dialog
 * @param {string} message - The confirmation message
 * @param {function} callback - Function to call if confirmed
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Show loading state for an element
 * @param {HTMLElement} element - The element to show loading state for
 * @param {string} text - Optional loading text
 */
function showLoading(element, text = 'Loading...') {
    const originalText = element.innerHTML;
    element.disabled = true;
    element.dataset.originalText = originalText;
    element.innerHTML = `<span class="loading-spinner"></span> ${text}`;
}

/**
 * Hide loading state for an element
 * @param {HTMLElement} element - The element to hide loading state for
 */
function hideLoading(element) {
    const originalText = element.dataset.originalText;
    element.disabled = false;
    element.innerHTML = originalText;
}

/**
 * Handle form submission with AJAX
 * @param {HTMLFormElement} form - The form element
 * @param {function} successCallback - Function to call on success
 * @param {function} errorCallback - Function to call on error
 */
function handleFormSubmit(form, successCallback, errorCallback) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const submitButton = form.querySelector('button[type="submit"]');
        showLoading(submitButton);
        
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: form.method,
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            hideLoading(submitButton);
            if (typeof successCallback === 'function') {
                successCallback(data);
            }
        })
        .catch(error => {
            hideLoading(submitButton);
            if (typeof errorCallback === 'function') {
                errorCallback(error);
            } else {
                console.error('Error:', error);
            }
        });
    });
}
