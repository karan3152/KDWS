/**
 * Session Manager for KDWS
 * Handles session timeout tracking and notifications
 */

class SessionManager {
    constructor(options = {}) {
        // Default options
        this.options = {
            sessionTimeout: 30 * 60, // 30 minutes in seconds (from server config)
            warningTime: 5 * 60,     // Show warning 5 minutes before expiration
            checkInterval: 10,       // Check every 10 seconds
            extendUrl: '/extend-session',
            logoutUrl: '/logout',
            ...options
        };

        // State variables
        this.timeRemaining = this.options.sessionTimeout;
        this.warningShown = false;
        this.activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart'];

        // Initialize
        this.init();
    }

    init() {
        // Create UI elements
        this.createUI();

        // Start the timer
        this.startTimer();

        // Add activity listeners
        this.setupActivityTracking();

        // Initial update
        this.updateDisplay();
    }

    createUI() {
        // Create session timer display
        const timerContainer = document.createElement('div');
        timerContainer.id = 'session-timer-container';
        timerContainer.className = 'session-timer-container';
        timerContainer.innerHTML = `
            <div class="session-timer">
                <span class="session-timer-icon"><i class="fas fa-clock"></i></span>
                <span class="session-timer-text">Session: <span id="session-time-remaining">30:00</span></span>
                <button id="extend-session-btn" class="btn btn-sm btn-outline-primary">Extend</button>
            </div>
            <div id="session-warning" class="session-warning" style="display: none;">
                <div class="session-warning-content">
                    <p><i class="fas fa-exclamation-triangle"></i> Your session will expire soon!</p>
                    <button id="session-extend-btn" class="btn btn-primary">Extend Session</button>
                </div>
            </div>
        `;

        document.body.appendChild(timerContainer);

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .session-timer-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
            }
            .session-timer {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                display: flex;
                align-items: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .session-timer-icon {
                margin-right: 8px;
                color: #6c757d;
            }
            .session-timer-text {
                margin-right: 10px;
            }
            #extend-session-btn {
                font-size: 12px;
                padding: 2px 8px;
            }
            .session-warning {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1050;
            }
            .session-warning-content {
                background-color: white;
                border-radius: 5px;
                padding: 20px;
                text-align: center;
                max-width: 400px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .session-warning-content p {
                margin-bottom: 15px;
                font-size: 18px;
                color: #dc3545;
            }
            .session-warning-content i {
                margin-right: 10px;
            }
        `;
        document.head.appendChild(style);

        // Add event listeners
        document.getElementById('extend-session-btn').addEventListener('click', () => this.extendSession());
        document.getElementById('session-extend-btn').addEventListener('click', () => this.extendSession());
    }

    startTimer() {
        this.timer = setInterval(() => {
            this.timeRemaining -= this.options.checkInterval;

            // Show warning when approaching timeout
            if (this.timeRemaining <= this.options.warningTime && !this.warningShown) {
                this.showWarning();
            }

            // Update the display
            this.updateDisplay();

            // Handle session expiration
            if (this.timeRemaining <= 0) {
                this.handleExpiration();
            }
        }, this.options.checkInterval * 1000);
    }

    updateDisplay() {
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        const timerElement = document.getElementById('session-time-remaining');
        if (timerElement) {
            timerElement.textContent = display;

            // Change color based on time remaining
            if (this.timeRemaining <= 300) { // 5 minutes
                timerElement.style.color = '#dc3545'; // red
            } else if (this.timeRemaining <= 600) { // 10 minutes
                timerElement.style.color = '#fd7e14'; // orange
            } else {
                timerElement.style.color = ''; // default
            }
        }
    }

    showWarning() {
        this.warningShown = true;
        const warningElement = document.getElementById('session-warning');
        if (warningElement) {
            warningElement.style.display = 'flex';
        }
    }

    hideWarning() {
        this.warningShown = false;
        const warningElement = document.getElementById('session-warning');
        if (warningElement) {
            warningElement.style.display = 'none';
        }
    }

    setupActivityTracking() {
        // Track user activity
        this.activityEvents.forEach(eventType => {
            document.addEventListener(eventType, () => this.handleUserActivity(), { passive: true });
        });
    }

    handleUserActivity() {
        // Only extend automatically if more than 5 minutes have passed since last extension
        const now = new Date().getTime();
        if (!this.lastExtensionTime || (now - this.lastExtensionTime) > 5 * 60 * 1000) {
            this.extendSession();
        }
    }

    extendSession() {
        // Record extension time
        this.lastExtensionTime = new Date().getTime();

        // Hide warning if shown
        this.hideWarning();

        // Reset timer
        this.timeRemaining = this.options.sessionTimeout;
        this.updateDisplay();

        // Call server to extend session
        fetch(this.options.extendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                console.error('Failed to extend session');
            }
        })
        .catch(error => {
            console.error('Error extending session:', error);
        });
    }

    handleExpiration() {
        clearInterval(this.timer);
        alert('Your session has expired. You will be redirected to the login page.');
        window.location.href = this.options.logoutUrl;
    }

    getCSRFToken() {
        // Get CSRF token from meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on employee pages
    if (document.body.classList.contains('employee-view')) {
        // Get session timeout from meta tag (set by server)
        const metaTimeout = document.querySelector('meta[name="session-timeout"]');
        const sessionTimeout = metaTimeout ? parseInt(metaTimeout.getAttribute('content'), 10) : 30 * 60;

        window.sessionManager = new SessionManager({
            sessionTimeout: sessionTimeout,
            extendUrl: '/extend-session',
            logoutUrl: '/logout'
        });
    }
});
