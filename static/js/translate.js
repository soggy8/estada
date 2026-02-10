// Translation system
(function() {
    'use strict';
    
    const STORAGE_KEY = 'estada_lang';
    const DEFAULT_LANG = 'en';
    
    let currentLang = localStorage.getItem(STORAGE_KEY) || DEFAULT_LANG;
    
    // Initialize translation system
    function init() {
        // Apply saved language on page load
        applyLanguage(currentLang);
        
        // Set up language toggle button
        const langToggle = document.getElementById('lang-toggle');
        if (langToggle) {
            langToggle.addEventListener('click', toggleLanguage);
            updateToggleButton(langToggle);
        }
    }
    
    // Toggle between languages
    function toggleLanguage() {
        currentLang = currentLang === 'en' ? 'mk' : 'en';
        localStorage.setItem(STORAGE_KEY, currentLang);
        applyLanguage(currentLang);
        
        const langToggle = document.getElementById('lang-toggle');
        if (langToggle) {
            updateToggleButton(langToggle);
        }
    }
    
    // Update toggle button text
    function updateToggleButton(button) {
        if (button) {
            button.textContent = currentLang === 'en' ? 'MK' : 'EN';
            button.setAttribute('aria-label', currentLang === 'en' ? 'Switch to Macedonian' : 'Switch to English');
        }
    }
    
    // Apply translations to the page
    function applyLanguage(lang) {
        // Update HTML lang attribute
        document.documentElement.lang = lang;
        
        // Get all elements with data-translate attribute
        const elements = document.querySelectorAll('[data-translate]');
        
        elements.forEach(element => {
            const key = element.getAttribute('data-translate');
            const translation = translations[lang] && translations[lang][key];
            
            if (translation) {
                // Check if element is input/textarea/select
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT') {
                    if (element.type === 'submit' || element.type === 'button') {
                        element.value = translation;
                    } else if (element.hasAttribute('placeholder') || element.placeholder) {
                        element.placeholder = translation;
                    } else {
                        element.value = translation;
                    }
                } else if (element.tagName === 'OPTION') {
                    element.textContent = translation;
                } else if (element.tagName === 'LABEL') {
                    element.textContent = translation;
                } else {
                    // For regular elements, preserve HTML structure if needed
                    const preserveHTML = element.hasAttribute('data-preserve-html');
                    if (preserveHTML && element.innerHTML.includes('<em>') || element.innerHTML.includes('<strong>')) {
                        // Try to preserve emphasis tags
                        const parts = translation.split(/(<em>.*?<\/em>|<strong>.*?<\/strong>)/);
                        if (parts.length > 1) {
                            element.innerHTML = translation;
                        } else {
                            element.textContent = translation;
                        }
                    } else {
                        element.textContent = translation;
                    }
                }
            }
        });
        
        // Update page title if it has a data-translate attribute
        const titleElement = document.querySelector('title[data-translate]');
        if (titleElement) {
            const titleKey = titleElement.getAttribute('data-translate');
            const titleTranslation = translations[lang] && translations[lang][titleKey];
            if (titleTranslation) {
                document.title = titleTranslation;
            }
        }
    }
    
    // Expose functions globally if needed
    window.TranslationSystem = {
        getCurrentLang: () => currentLang,
        setLanguage: (lang) => {
            if (translations[lang]) {
                currentLang = lang;
                localStorage.setItem(STORAGE_KEY, currentLang);
                applyLanguage(currentLang);
                const langToggle = document.getElementById('lang-toggle');
                if (langToggle) {
                    updateToggleButton(langToggle);
                }
            }
        },
        translate: (key) => {
            return translations[currentLang] && translations[currentLang][key] || key;
        }
    };
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

