// Technologies page JavaScript
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
});

