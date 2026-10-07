// ========================================
// Estada - Main JavaScript
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Mobile Navigation Toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    const navBackdrop = document.querySelector('.nav-backdrop');
    const body = document.body;
    
    function toggleMenu() {
        const isActive = navLinks.classList.contains('active');
        navLinks.classList.toggle('active');
        navToggle.classList.toggle('active');
        
        if (navBackdrop) {
            navBackdrop.classList.toggle('active');
        }
        
        // Update aria-expanded
        navToggle.setAttribute('aria-expanded', !isActive);
        
        // Prevent body scroll when menu is open
        if (!isActive) {
            body.style.overflow = 'hidden';
        } else {
            body.style.overflow = '';
        }
    }
    
    function closeMenu() {
        navLinks.classList.remove('active');
        navToggle.classList.remove('active');
        
        if (navBackdrop) {
            navBackdrop.classList.remove('active');
        }
        
        navToggle.setAttribute('aria-expanded', 'false');
        body.style.overflow = '';
    }
    
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', toggleMenu);
        
        // Close menu when clicking backdrop (if it exists)
        if (navBackdrop) {
            navBackdrop.addEventListener('click', closeMenu);
        }
        
        // Close menu when clicking a link
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeMenu);
        });
        
        // Close menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && navLinks.classList.contains('active')) {
                closeMenu();
            }
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const navHeight = document.querySelector('.nav').offsetHeight;
                const targetPosition = target.offsetTop - navHeight - 20;
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Intersection Observer for fade-in animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    
    // Add fade-in class to elements we want to animate
    const animateElements = document.querySelectorAll(
        '.service-card, .process-step, .value-card, .stat-item'
    );
    
    // Stagger within each group, so the last card of a grid never waits on the whole page
    animateElements.forEach((el) => {
        el.classList.add('fade-in');
        el.style.transitionDelay = `${[...el.parentElement.children].indexOf(el) * 0.08}s`;
        observer.observe(el);
    });
    
    // Form submission handler
    const contactForm = document.querySelector('.contact-form');
    // Localized messages, rendered by the server next to the form
    const messagesElement = document.getElementById('i18n-messages');
    const messages = messagesElement ? JSON.parse(messagesElement.textContent) : {};
    if (contactForm) {
        // Fetch CSRF token on page load
        let csrfToken = null;
        (async () => {
            try {
                const response = await fetch('/api/csrf-token');
                const data = await response.json();
                csrfToken = data.csrf_token;
            } catch (error) {
                console.error('Failed to fetch CSRF token:', error);
            }
        })();
        
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Check if CSRF token is available
            if (!csrfToken) {
                showNotification(messages.tokenMissing, 'error');
                return;
            }
            
            // Get form data
            const formData = new FormData(contactForm);
            const data = {
                name: formData.get('name'),
                email: formData.get('email'),
                service: formData.get('service') || '',
                message: formData.get('message') || '',
                website: formData.get('website') || '', // Honeypot field
                csrf_token: csrfToken
            };
            
            // Simple validation
            if (!data.name || !data.email) {
                showNotification(messages.required, 'error');
                return;
            }
            
            // Email validation
            const emailRegex = /^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$/;
            if (!emailRegex.test(data.email)) {
                showNotification(messages.invalidEmail, 'error');
                return;
            }
            
            // Submit form
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = messages.sending;
            submitBtn.disabled = true;
            
            try {
                const response = await fetch('/api/contact', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showNotification(messages.success, 'success');
                    contactForm.reset();
                    // Refresh CSRF token after successful submission
                    try {
                        const tokenResponse = await fetch('/api/csrf-token');
                        const tokenData = await tokenResponse.json();
                        csrfToken = tokenData.csrf_token;
                    } catch (error) {
                        console.error('Failed to refresh CSRF token:', error);
                    }
                } else {
                    showNotification(messages['error_' + result.code] || messages.error_generic, 'error');
                    // Refresh CSRF token on error (token might be expired)
                    if (response.status === 403) {
                        try {
                            const tokenResponse = await fetch('/api/csrf-token');
                            const tokenData = await tokenResponse.json();
                            csrfToken = tokenData.csrf_token;
                        } catch (error) {
                            console.error('Failed to refresh CSRF token:', error);
                        }
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification(messages.network, 'error');
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
    
    // Form status, shown inline under the submit button
    function showNotification(message, type) {
        const status = contactForm.querySelector('.form-status');
        status.className = `form-status is-${type}`;
        status.setAttribute('role', type === 'error' ? 'alert' : 'status');
        status.textContent = message;
    }

    // Navbar background once the page has scrolled past the top 80px
    const nav = document.querySelector('.nav');
    const scrollSentinel = document.createElement('div');
    scrollSentinel.setAttribute('aria-hidden', 'true');
    scrollSentinel.style.cssText = 'position: absolute; top: 80px; left: 0; width: 1px; height: 1px; pointer-events: none;';
    document.body.prepend(scrollSentinel);
    new IntersectionObserver(([entry]) => {
        nav.classList.toggle('nav-scrolled', !entry.isIntersecting);
    }).observe(scrollSentinel);
});

