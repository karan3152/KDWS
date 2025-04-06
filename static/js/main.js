// Main JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    // Initialize progress circles
    const progressCircles = document.querySelectorAll('.progress-circle');
    if (progressCircles.length > 0) {
        progressCircles.forEach(circle => {
            const percentage = circle.getAttribute('data-percentage');
            circle.style.setProperty('--percentage', percentage);
        });
    }
    
    // Initialize document form toggles
    const toggleFormBtns = document.querySelectorAll('.toggle-form-btn');
    if (toggleFormBtns.length > 0) {
        toggleFormBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const card = this.closest('.card-body');
                const form = card.querySelector('.document-upload-form');
                const info = card.querySelector('.document-info');
                
                if (form.classList.contains('d-none')) {
                    form.classList.remove('d-none');
                    if (info) info.classList.add('d-none');
                    btn.innerHTML = '<i class="fas fa-times mr-1"></i> Cancel';
                } else {
                    form.classList.add('d-none');
                    if (info) info.classList.remove('d-none');
                    btn.innerHTML = '<i class="fas fa-sync-alt mr-1"></i> Replace Document';
                }
            });
        });
    }
    
    // Initialize upload toggles
    const toggleUploadBtns = document.querySelectorAll('.toggle-upload-btn');
    if (toggleUploadBtns.length > 0) {
        toggleUploadBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const card = this.closest('.card-body');
                const form = card.querySelector('.document-upload-form');
                
                if (form.classList.contains('d-none')) {
                    form.classList.remove('d-none');
                    btn.innerHTML = '<i class="fas fa-times mr-1"></i> Hide Upload Form';
                } else {
                    form.classList.add('d-none');
                    btn.innerHTML = '<i class="fas fa-upload mr-1"></i> Upload Existing PDF';
                }
            });
        });
    }
    
    // Initialize date pickers
    const datePickers = document.querySelectorAll('input[type="date"]');
    if (datePickers.length > 0) {
        datePickers.forEach(picker => {
            // If the browser doesn't support date inputs, could initialize a datepicker library here
        });
    }
    
    // Initialize search auto-selection
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        const queryInput = searchForm.querySelector('input[name="query"]');
        const typeSelect = searchForm.querySelector('select[name="search_type"]');
        
        queryInput.addEventListener('input', function() {
            const query = this.value;
            
            // Auto-detect search type based on input format
            if (typeSelect.value === 'auto') {
                if (/^\d{12}$/.test(query)) {
                    // 12 digit Aadhar number
                    typeSelect.value = 'aadhar';
                } else if (query.startsWith('EMP')) {
                    // Employee ID starts with EMP
                    typeSelect.value = 'employee_id';
                } else if (query.includes('@')) {
                    // Email contains @
                    typeSelect.value = 'email';
                } else {
                    // Default to name search
                    typeSelect.value = 'name';
                }
            }
        });
    }
    
    // Initialize tooltips
    const tooltipElements = document.querySelectorAll('[data-toggle="tooltip"]');
    if (tooltipElements.length > 0 && typeof $ !== 'undefined') {
        $(function () {
            $('[data-toggle="tooltip"]').tooltip();
        });
    }
    
    // Initialize popovers
    const popoverElements = document.querySelectorAll('[data-toggle="popover"]');
    if (popoverElements.length > 0 && typeof $ !== 'undefined') {
        $(function () {
            $('[data-toggle="popover"]').popover();
        });
    }
});