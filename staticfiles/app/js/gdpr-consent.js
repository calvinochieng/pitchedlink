// gdpr-consent.js - Full GDPR + Google Consent Mode Support
(function () {
    // Only run on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeConsent);
    } else {
        initializeConsent();
    }

    function initializeConsent() {
        // Restore consent if already given
        restoreConsent();

        // Only show banner if no consent
        const consent = getCookie('gdpr_consent');
        if (consent) return;

        // Don't add if already exists
        if (document.getElementById('gdpr-banner')) return;

        // Create banner
        const banner = document.createElement('div');
        banner.id = 'gdpr-banner';
        banner.className = 'cookie-banner';
        banner.innerHTML = `
            <div class="cookie-banner-content">
                <p>
                    We use cookies to enhance your experience, analyze site usage, and deliver personalized content. 
                    By clicking "Accept", you consent to our use of cookies.
                </p>
                <div class="cookie-banner-actions">
                    <button class="button is-small" id="gdpr-reject">Reject</button>
                    <button class="button is-warning is-small" id="gdpr-accept">Accept</button>
                </div>
            </div>
        `;

        // Add styles
        addStyles();

        // Insert banner
        document.body.appendChild(banner);

        // Attach event listeners
        document.getElementById('gdpr-accept').addEventListener('click', function () {
            setCookie('gdpr_consent', 'accepted', 365);
            updateGoogleConsent('granted');
            banner.remove();
            onConsentGranted();
        });

        document.getElementById('gdpr-reject').addEventListener('click', function () {
            setCookie('gdpr_consent', 'rejected', 365);
            updateGoogleConsent('denied');
            banner.remove();
            onConsentDenied();
        });
    }

    function addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* GDPR Cookie Banner */
            .cookie-banner {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background: rgba(0, 0, 0, 0.95);
                color: white;
                padding: 1rem;
                z-index: 9999;
                font-size: 0.9rem;
                box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.3);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            }

            .cookie-banner-content {
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 1rem;
                text-align: center;
            }

            .cookie-banner p {
                margin: 0;
                flex: 1;
            }

            .cookie-banner-actions {
                display: flex;
                gap: 0.5rem;
            }

            .cookie-banner button {
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9rem;
                font-weight: 500;
            }

            #gdpr-accept {
                background-color: #FFB70F;
                color: #000;
            }

            #gdpr-reject {
                background-color: transparent;
                color: #ffffffc9;
                border: 1px solid #ffffff40;
            }

            @media (max-width: 480px) {
                .cookie-banner-content {
                    flex-direction: column;
                }
                .cookie-banner button {
                    width: 100%;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Cookie helpers
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = "expires=" + date.toUTCString();
        const secure = window.location.protocol === 'https:' ? ';Secure' : '';
        document.cookie = name + "=" + value + ";" + expires + ";path=/; SameSite=Lax" + secure;
    }

    // Update Google Consent Mode
    function updateGoogleConsent(status) {
        if (typeof gtag === 'function') {
            gtag('consent', 'update', {
                'analytics_storage': status,
                'ad_storage': status,
                'ad_user_data': status,
                'ad_personalization': status
            });
        }
    }

    // Restore consent on page load
    function restoreConsent() {
        const consent = getCookie('gdpr_consent');
        if (consent === 'accepted') {
            updateGoogleConsent('granted');
            onConsentGranted();
        } else if (consent === 'rejected') {
            updateGoogleConsent('denied');
            onConsentDenied();
        }
        // If no cookie, Google defaults to 'denied' (safe)
    }

    // Hook functions (override in your app if needed)
    window.onConsentGranted = function () {
        console.log('✅ GDPR: User accepted non-essential cookies');
        // Example: loadAnalytics();
    };

    window.onConsentDenied = function () {
        console.log('❌ GDPR: User rejected non-essential cookies');
        // Example: disableTracking();
    };
})();