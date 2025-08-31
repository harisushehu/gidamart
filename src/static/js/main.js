// Gidamart Main JavaScript

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Gidamart application loaded');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize property filters
    initializePropertyFilters();
    
    // Initialize image galleries
    initializeImageGalleries();
    
    // Initialize flash messages auto-dismiss
    initializeFlashMessages();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Form validation
function initializeFormValidation() {
    // Get all forms with validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// Property filters functionality
function initializePropertyFilters() {
    const filterForm = document.getElementById('property-filters');
    if (filterForm) {
        filterForm.addEventListener('change', function() {
            // Auto-submit filter form when values change
            this.submit();
        });
    }
}

// Image gallery functionality
function initializeImageGalleries() {
    const galleries = document.querySelectorAll('.property-gallery');
    galleries.forEach(function(gallery) {
        const images = gallery.querySelectorAll('img');
        images.forEach(function(img, index) {
            img.addEventListener('click', function() {
                openImageModal(img.src, img.alt);
            });
        });
    });
}

// Flash messages auto-dismiss
function initializeFlashMessages() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert.classList.contains('show')) {
                alert.classList.remove('show');
                alert.classList.add('fade');
                setTimeout(function() {
                    alert.remove();
                }, 150);
            }
        }, 5000); // Auto-dismiss after 5 seconds
    });
}

// Open image in modal
function openImageModal(src, alt) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('imageModal');
    if (!modal) {
        modal = createImageModal();
        document.body.appendChild(modal);
    }
    
    const modalImg = modal.querySelector('.modal-image');
    const modalTitle = modal.querySelector('.modal-title');
    
    modalImg.src = src;
    modalTitle.textContent = alt || 'Property Image';
    
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}

// Create image modal
function createImageModal() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'imageModal';
    modal.tabIndex = -1;
    modal.innerHTML = `
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Property Image</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="" alt="" class="modal-image img-fluid">
                </div>
            </div>
        </div>
    `;
    return modal;
}

// Property search functionality
function searchProperties(query) {
    if (query.length < 2) return;
    
    fetch(`/api/search/properties?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Search error:', error);
        });
}

// Display search results
function displaySearchResults(results) {
    const container = document.getElementById('search-results');
    if (!container) return;
    
    if (results.length === 0) {
        container.innerHTML = '<p class="text-muted">No properties found.</p>';
        return;
    }
    
    const html = results.map(property => `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card property-card h-100">
                <img src="${property.image_url || '/static/images/placeholder.jpg'}" 
                     class="card-img-top property-image" alt="${property.title}">
                <div class="card-body">
                    <h5 class="card-title">${property.title}</h5>
                    <p class="card-text">${property.description.substring(0, 100)}...</p>
                    <p class="card-text">
                        <small class="text-muted">
                            <i class="bi bi-geo-alt"></i> ${property.location}
                        </small>
                    </p>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="h5 text-primary">₦${Number(property.price).toLocaleString()}</span>
                        <a href="/property/${property.id}" class="btn btn-outline-primary btn-sm">
                            View Details
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Contact form submission
function submitContactForm(form) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // Disable submit button and show loading
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Message sent successfully!', 'success');
            form.reset();
        } else {
            showAlert(data.error || 'Failed to send message', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred. Please try again.', 'danger');
    })
    .finally(() => {
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    });
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

// Create alert container if it doesn't exist
function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Utility function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: 'NGN'
    }).format(amount);
}

// Utility function to debounce function calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
