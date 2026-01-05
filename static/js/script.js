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
        '.service-card, .process-step, .stat, .float-card'
    );
    
    animateElements.forEach((el, index) => {
        el.classList.add('fade-in');
        el.style.transitionDelay = `${index * 0.1}s`;
        observer.observe(el);
    });
    
    // Form submission handler
    const contactForm = document.querySelector('.contact-form');
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
                showNotification('Security token not loaded. Please refresh the page and try again.', 'error');
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
                showNotification('Please fill in all required fields.', 'error');
                return;
            }
            
            // Email validation
            const emailRegex = /^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$/;
            if (!emailRegex.test(data.email)) {
                showNotification('Please enter a valid email address.', 'error');
                return;
            }
            
            // Submit form
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Sending...';
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
                    showNotification('Message sent! We\'ll be in touch soon.', 'success');
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
                    showNotification(result.message || 'Failed to send message. Please try again.', 'error');
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
                showNotification('Network error. Please check your connection and try again.', 'error');
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
    
    // Notification function
    function showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelector('.notification');
        if (existing) existing.remove();
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" aria-label="Close">&times;</button>
        `;
        
        // Add styles dynamically
        notification.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 16px 24px;
            background: ${type === 'success' ? '#0c2d4a' : type === 'error' ? '#4a1c1c' : '#0c1a2e'};
            color: #f0f4f8;
            border-radius: 8px;
            border: 1px solid ${type === 'success' ? 'rgba(59, 130, 246, 0.3)' : type === 'error' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(59, 130, 246, 0.2)'};
            display: flex;
            align-items: center;
            gap: 16px;
            font-size: 0.95rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.4);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        // Add animation keyframes if not exists
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                .notification button {
                    background: none;
                    border: none;
                    color: inherit;
                    font-size: 1.3rem;
                    cursor: pointer;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                }
                .notification button:hover {
                    opacity: 1;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideIn 0.3s ease reverse';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }
    
    // Navbar background on scroll
const nav = document.querySelector('.nav');

window.addEventListener('scroll', () => {
    if (window.scrollY > 80) {
        nav.classList.add('nav-scrolled'); // enable blur + transparency
    } else {
        nav.classList.remove('nav-scrolled');
    }
});

    
    // Parallax effect for hero visual
    const heroVisual = document.querySelector('.hero-visual');
    if (heroVisual) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.3;
            heroVisual.style.transform = `translateY(${rate}px)`;
        });
    }
    
    // Add cursor glow effect
    const cursorGlow = document.createElement('div');
    cursorGlow.className = 'cursor-glow';
    cursorGlow.style.cssText = `
        position: fixed;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        z-index: -1;
        transform: translate(-50%, -50%);
        transition: opacity 0.3s ease;
    `;
    document.body.appendChild(cursorGlow);
    
    document.addEventListener('mousemove', (e) => {
        cursorGlow.style.left = e.clientX + 'px';
        cursorGlow.style.top = e.clientY + 'px';
    });
    
    // Hide cursor glow on mobile
    if ('ontouchstart' in window) {
        cursorGlow.style.display = 'none';
    }
});

