// PDF Handler for the Employee Data Management System

// Wait for PDF.js to load
document.addEventListener('DOMContentLoaded', function() {
    // Load PDF.js dynamically
    const pdfJsScript = document.createElement('script');
    pdfJsScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.12.313/pdf.min.js';
    pdfJsScript.onload = function() {
        // Set worker source
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.12.313/pdf.worker.min.js';
        
        // Initialize PDF viewers
        initPdfViewers();
    };
    document.head.appendChild(pdfJsScript);
});

/**
 * Initialize PDF viewers on the page
 */
function initPdfViewers() {
    const pdfViewers = document.querySelectorAll('.pdf-viewer');
    
    pdfViewers.forEach(viewer => {
        const documentId = viewer.dataset.documentId;
        if (documentId) {
            loadPdf(documentId, viewer);
        }
    });
    
    // Also initialize the document upload area if it exists
    initDocumentUpload();
}

/**
 * Load a PDF from the server and display it in the viewer
 * @param {string} documentId - The ID of the document to load
 * @param {HTMLElement} viewerElement - The viewer element to display the PDF in
 */
function loadPdf(documentId, viewerElement) {
    // Get the document URL from the API
    fetch(`/api/document/${documentId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch document data');
            }
            return response.json();
        })
        .then(data => {
            const pdfUrl = data.path;
            
            // Get or create the content area
            let contentArea = viewerElement.querySelector('.pdf-viewer-content');
            if (!contentArea) {
                contentArea = document.createElement('div');
                contentArea.className = 'pdf-viewer-content';
                viewerElement.appendChild(contentArea);
            }
            
            // Get or create the controls area
            let controlsArea = viewerElement.querySelector('.pdf-controls');
            if (!controlsArea) {
                controlsArea = document.createElement('div');
                controlsArea.className = 'pdf-controls';
                viewerElement.appendChild(controlsArea);
                
                // Add page navigation controls
                controlsArea.innerHTML = `
                    <button class="btn btn-sm btn-primary mr-1 pdf-control prev-page">
                        <i class="fas fa-chevron-left"></i> Prev
                    </button>
                    <span class="page-info">Page <span class="current-page">0</span> of <span class="total-pages">0</span></span>
                    <button class="btn btn-sm btn-primary ml-1 pdf-control next-page">
                        <i class="fas fa-chevron-right"></i> Next
                    </button>
                `;
            }
            
            // Load and render the PDF
            const loadingTask = pdfjsLib.getDocument(pdfUrl);
            loadingTask.promise.then(pdf => {
                // Store the PDF instance and current page
                viewerElement.pdfDoc = pdf;
                viewerElement.currentPage = 1;
                
                // Update page count
                const totalPagesEl = viewerElement.querySelector('.total-pages');
                if (totalPagesEl) {
                    totalPagesEl.textContent = pdf.numPages;
                }
                
                // Render the first page
                renderPage(viewerElement, 1);
                
                // Set up page navigation
                const prevButton = viewerElement.querySelector('.prev-page');
                const nextButton = viewerElement.querySelector('.next-page');
                
                if (prevButton) {
                    prevButton.addEventListener('click', function() {
                        if (viewerElement.currentPage > 1) {
                            renderPage(viewerElement, viewerElement.currentPage - 1);
                        }
                    });
                }
                
                if (nextButton) {
                    nextButton.addEventListener('click', function() {
                        if (viewerElement.currentPage < pdf.numPages) {
                            renderPage(viewerElement, viewerElement.currentPage + 1);
                        }
                    });
                }
            }).catch(error => {
                console.error('Error loading PDF:', error);
                contentArea.innerHTML = `
                    <div class="pdf-error">
                        <div class="pdf-error-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <div class="pdf-error-message">
                            Failed to load PDF document
                        </div>
                    </div>
                `;
            });
        })
        .catch(error => {
            console.error('Error fetching document:', error);
        });
}

/**
 * Render a specific page of the PDF
 * @param {HTMLElement} viewerElement - The viewer element
 * @param {number} pageNumber - The page number to render
 */
function renderPage(viewerElement, pageNumber) {
    // Get the PDF document
    const pdf = viewerElement.pdfDoc;
    if (!pdf) return;
    
    // Update current page
    viewerElement.currentPage = pageNumber;
    
    // Update page display
    const currentPageEl = viewerElement.querySelector('.current-page');
    if (currentPageEl) {
        currentPageEl.textContent = pageNumber;
    }
    
    // Get the content area
    const contentArea = viewerElement.querySelector('.pdf-viewer-content');
    
    // Set loading state
    contentArea.innerHTML = '<div class="pdf-loading">Loading page...</div>';
    
    // Get the page
    pdf.getPage(pageNumber).then(page => {
        // Create a canvas for rendering
        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-viewer-canvas';
        const context = canvas.getContext('2d');
        
        // Calculate scale to fit the container
        const containerWidth = contentArea.clientWidth - 40; // 20px padding on each side
        const viewport = page.getViewport({ scale: 1 });
        const scale = containerWidth / viewport.width;
        const scaledViewport = page.getViewport({ scale });
        
        // Set canvas dimensions
        canvas.width = scaledViewport.width;
        canvas.height = scaledViewport.height;
        
        // Clear content area and add canvas
        contentArea.innerHTML = '';
        contentArea.appendChild(canvas);
        
        // Render the page
        const renderContext = {
            canvasContext: context,
            viewport: scaledViewport
        };
        
        page.render(renderContext);
    });
}

/**
 * Initialize document upload functionality
 */
function initDocumentUpload() {
    const uploadAreas = document.querySelectorAll('.upload-area');
    const fileInputs = document.querySelectorAll('input[type="file"][accept="application/pdf"]');
    
    uploadAreas.forEach(area => {
        // Find the related file input
        const fileInput = area.closest('form').querySelector('input[type="file"]');
        
        // Handle click on upload area
        area.addEventListener('click', function() {
            if (fileInput) {
                fileInput.click();
            }
        });
        
        // Handle drag and drop
        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('dragover');
        });
        
        area.addEventListener('dragleave', function() {
            area.classList.remove('dragover');
        });
        
        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
            
            if (fileInput && e.dataTransfer.files.length > 0) {
                const file = e.dataTransfer.files[0];
                
                // Check if file is a PDF
                if (file.type === 'application/pdf') {
                    fileInput.files = e.dataTransfer.files;
                    
                    // Trigger change event
                    const changeEvent = new Event('change', { bubbles: true });
                    fileInput.dispatchEvent(changeEvent);
                } else {
                    alert('Please upload a PDF file');
                }
            }
        });
    });
    
    // Handle file selection
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name;
            const uploadArea = this.closest('form').querySelector('.upload-area');
            
            if (fileName && uploadArea) {
                // Update the upload area to show selected file
                uploadArea.innerHTML = `
                    <div class="upload-icon">
                        <i class="far fa-file-pdf"></i>
                    </div>
                    <div class="upload-text">Selected: ${fileName}</div>
                    <div class="upload-help">Click to change file</div>
                `;
                
                // Preview the PDF if possible
                const previewArea = this.closest('form').querySelector('.pdf-preview');
                if (previewArea) {
                    previewPdf(this.files[0], previewArea);
                }
            }
        });
    });
}

/**
 * Preview a PDF file before upload
 * @param {File} file - The PDF file to preview
 * @param {HTMLElement} previewElement - The element to display the preview in
 */
function previewPdf(file, previewElement) {
    // Read the file
    const fileReader = new FileReader();
    
    fileReader.onload = function() {
        const typedArray = new Uint8Array(this.result);
        
        // Load the PDF
        pdfjsLib.getDocument(typedArray).promise.then(pdf => {
            // Get the first page
            pdf.getPage(1).then(page => {
                // Create a canvas for rendering
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                
                // Calculate scale to fit the preview area
                const containerWidth = previewElement.clientWidth - 40; // 20px padding on each side
                const viewport = page.getViewport({ scale: 1 });
                const scale = containerWidth / viewport.width;
                const scaledViewport = page.getViewport({ scale });
                
                // Set canvas dimensions
                canvas.width = scaledViewport.width;
                canvas.height = scaledViewport.height;
                
                // Clear preview area and add canvas
                previewElement.innerHTML = '';
                previewElement.appendChild(canvas);
                
                // Render the page
                const renderContext = {
                    canvasContext: context,
                    viewport: scaledViewport
                };
                
                page.render(renderContext);
            });
        }).catch(error => {
            console.error('Error previewing PDF:', error);
            previewElement.innerHTML = '<div class="pdf-preview-error">Failed to preview PDF</div>';
        });
    };
    
    fileReader.readAsArrayBuffer(file);
}
