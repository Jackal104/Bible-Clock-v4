/**
 * Bible Clock Web Interface - Main JavaScript Application
 */

// Global application state
const BibleClock = {
    version: '2.0.0',
    apiEndpoints: {
        verse: '/api/verse',
        status: '/api/status',
        settings: '/api/settings',
        statistics: '/api/statistics',
        backgrounds: '/api/backgrounds',
        fonts: '/api/fonts',
        refresh: '/api/refresh',
        preview: '/api/preview'
    },
    settings: {},
    isOnline: true,
    refreshInterval: null,
    charts: {}
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log(`Bible Clock Web Interface v${BibleClock.version} initialized`);
    initializeApp();
});

/**
 * Initialize the main application
 */
function initializeApp() {
    // Set up error handling
    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handlePromiseError);
    
    // Initialize components
    initializeNotifications();
    setupKeyboardShortcuts();
    
    // Check if we're on a specific page and initialize accordingly
    const path = window.location.pathname;
    
    if (path === '/' || path === '/dashboard') {
        initializeDashboard();
    } else if (path === '/settings') {
        initializeSettings();
    } else if (path === '/statistics') {
        initializeStatistics();
    }
    
    // Start global monitoring
    startStatusMonitoring();
}

/**
 * Initialize dashboard functionality
 */
function initializeDashboard() {
    console.log('Initializing dashboard...');
    // Dashboard-specific initialization is handled in dashboard.html
}

/**
 * Initialize settings functionality
 */
function initializeSettings() {
    console.log('Initializing settings...');
    // Settings-specific initialization is handled in settings.html
}

/**
 * Initialize statistics functionality
 */
function initializeStatistics() {
    console.log('Initializing statistics...');
    // Statistics-specific initialization is handled in statistics.html
}

/**
 * Set up keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Only handle shortcuts when not in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            return;
        }
        
        switch(e.key) {
            case 'r':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    refreshDisplay();
                }
                break;
            case 'p':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    generatePreview();
                }
                break;
            case 's':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    window.location.href = '/settings';
                }
                break;
            case 'd':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    window.location.href = '/';
                }
                break;
            case 't':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    window.location.href = '/statistics';
                }
                break;
        }
    });
}

/**
 * Start monitoring system status
 */
function startStatusMonitoring() {
    checkOnlineStatus();
    
    // Check every 30 seconds
    setInterval(checkOnlineStatus, 30000);
    
    // Also monitor network connectivity
    window.addEventListener('online', () => {
        BibleClock.isOnline = true;
        updateConnectionStatus(true);
    });
    
    window.addEventListener('offline', () => {
        BibleClock.isOnline = false;
        updateConnectionStatus(false);
    });
}

/**
 * Check if the API is responding
 */
function checkOnlineStatus() {
    fetch('/health', { 
        method: 'GET',
        cache: 'no-cache',
        timeout: 5000 
    })
    .then(response => {
        if (response.ok) {
            BibleClock.isOnline = true;
            updateConnectionStatus(true);
        } else {
            throw new Error('API not responding');
        }
    })
    .catch(() => {
        BibleClock.isOnline = false;
        updateConnectionStatus(false);
    });
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(isOnline) {
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');
    
    if (indicator && text) {
        if (isOnline) {
            indicator.className = 'w-3 h-3 bg-green-400 rounded-full mr-2';
            text.textContent = 'Online';
        } else {
            indicator.className = 'w-3 h-3 bg-red-400 rounded-full mr-2';
            text.textContent = 'Offline';
        }
    }
}

/**
 * Generic API request function
 */
async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };
    
    try {
        const response = await fetch(endpoint, defaultOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

/**
 * Refresh display (global function)
 */
async function refreshDisplay() {
    try {
        showLoading('Refreshing display...');
        await apiRequest('/api/refresh', { method: 'POST' });
        showNotification('Display refreshed successfully', 'success');
        
        // Reload current verse if we're on dashboard
        if (window.location.pathname === '/' && typeof loadCurrentVerse === 'function') {
            loadCurrentVerse();
        }
    } catch (error) {
        showNotification('Failed to refresh display', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Generate preview (global function)
 */
async function generatePreview() {
    try {
        showLoading('Generating preview...');
        const result = await apiRequest('/api/preview', { 
            method: 'POST',
            body: JSON.stringify({})
        });
        
        showNotification('Preview generated successfully', 'success');
        return result;
    } catch (error) {
        showNotification('Failed to generate preview', 'error');
        throw error;
    } finally {
        hideLoading();
    }
}

/**
 * Initialize notification system
 */
function initializeNotifications() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification transform transition-all duration-300 translate-x-full opacity-0 ${getNotificationClass(type)}`;
    
    notification.innerHTML = `
        <div class="flex items-center justify-between p-4 rounded-lg shadow-lg">
            <div class="flex items-center">
                ${getNotificationIcon(type)}
                <span class="ml-3 text-sm font-medium">${message}</span>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full', 'opacity-0');
    }, 100);
    
    // Auto remove
    if (duration > 0) {
        setTimeout(() => {
            notification.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
}

/**
 * Get notification CSS class based on type
 */
function getNotificationClass(type) {
    const classes = {
        success: 'bg-green-500 text-white',
        error: 'bg-red-500 text-white',
        warning: 'bg-yellow-500 text-white',
        info: 'bg-blue-500 text-white'
    };
    return classes[type] || classes.info;
}

/**
 * Get notification icon based on type
 */
function getNotificationIcon(type) {
    const icons = {
        success: `<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                  </svg>`,
        error: `<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>`,
        warning: `<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                  </svg>`,
        info: `<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
               </svg>`
    };
    return icons[type] || icons.info;
}

/**
 * Show loading indicator
 */
function showLoading(message = 'Loading...') {
    // Remove existing loading indicator
    hideLoading();
    
    const loading = document.createElement('div');
    loading.id = 'global-loading';
    loading.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    
    loading.innerHTML = `
        <div class="bg-white rounded-lg p-6 flex items-center space-x-3">
            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-bible-accent"></div>
            <span class="text-gray-700">${message}</span>
        </div>
    `;
    
    document.body.appendChild(loading);
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loading = document.getElementById('global-loading');
    if (loading) {
        loading.remove();
    }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

/**
 * Format duration for display
 */
function formatDuration(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

/**
 * Debounce function to limit API calls
 */
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

/**
 * Throttle function to limit API calls
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Handle global errors
 */
function handleGlobalError(event) {
    console.error('Global error:', event.error);
    showNotification('An unexpected error occurred', 'error');
}

/**
 * Handle promise rejection errors
 */
function handlePromiseError(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showNotification('A network error occurred', 'error');
}

/**
 * Utility function to copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copied to clipboard', 'success', 2000);
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        showNotification('Failed to copy to clipboard', 'error');
    }
}

/**
 * Utility function to download data as file
 */
function downloadAsFile(data, filename, type = 'application/json') {
    const blob = new Blob([data], { type });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    
    URL.revokeObjectURL(url);
}

/**
 * Validate form input
 */
function validateInput(input, rules) {
    const errors = [];
    const value = input.value.trim();
    
    if (rules.required && !value) {
        errors.push('This field is required');
    }
    
    if (rules.minLength && value.length < rules.minLength) {
        errors.push(`Minimum length is ${rules.minLength} characters`);
    }
    
    if (rules.maxLength && value.length > rules.maxLength) {
        errors.push(`Maximum length is ${rules.maxLength} characters`);
    }
    
    if (rules.pattern && !rules.pattern.test(value)) {
        errors.push('Invalid format');
    }
    
    if (rules.min && parseFloat(value) < rules.min) {
        errors.push(`Minimum value is ${rules.min}`);
    }
    
    if (rules.max && parseFloat(value) > rules.max) {
        errors.push(`Maximum value is ${rules.max}`);
    }
    
    return errors;
}

/**
 * Show form validation errors
 */
function showValidationErrors(input, errors) {
    // Remove existing error messages
    const existingError = input.parentNode.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
    
    if (errors.length > 0) {
        input.classList.add('border-red-500');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'validation-error text-red-500 text-sm mt-1';
        errorDiv.textContent = errors[0]; // Show first error
        
        input.parentNode.appendChild(errorDiv);
    } else {
        input.classList.remove('border-red-500');
    }
}

/**
 * Initialize tooltips (if needed)
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

/**
 * Show tooltip
 */
function showTooltip(event) {
    const element = event.target;
    const text = element.getAttribute('data-tooltip');
    
    const tooltip = document.createElement('div');
    tooltip.id = 'tooltip';
    tooltip.className = 'absolute bg-gray-800 text-white text-sm px-2 py-1 rounded shadow-lg z-50';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
}

/**
 * Hide tooltip
 */
function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Export global functions for use in templates
window.BibleClock = BibleClock;
window.refreshDisplay = refreshDisplay;
window.generatePreview = generatePreview;
window.showNotification = showNotification;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.formatTimestamp = formatTimestamp;
window.formatDuration = formatDuration;
window.copyToClipboard = copyToClipboard;
window.downloadAsFile = downloadAsFile;