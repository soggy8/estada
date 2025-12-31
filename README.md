# Estada - Tech Logistics & Digital Solutions

A modern, responsive static website for Estada, a tech logistics firm offering design, fullstack development, marketing, hosting, and digital solutions.

## Features

- **Modern Dark Theme** - Sophisticated dark color scheme with warm terracotta accents
- **Responsive Design** - Fully responsive across all device sizes
- **Smooth Animations** - CSS animations and scroll-triggered effects
- **Interactive Elements** - Working contact form with validation, mobile navigation
- **Performance Optimized** - Minimal JavaScript, CSS-first animations

## Sections

1. **Hero** - Bold headline with animated orbital visual
2. **Services** - Four service cards (Design, Development, Hosting, Marketing)
3. **About** - Company overview with floating feature cards and stats
4. **Process** - Four-step process breakdown
5. **Contact** - Form and contact information

## Tech Stack

- HTML5
- CSS3 (Custom properties, Grid, Flexbox, Animations)
- Vanilla JavaScript
- Google Fonts (Syne, Instrument Serif)

## Getting Started

Simply open `index.html` in your browser, or serve with any static file server:

```bash
# Using Python
python -m http.server 8000

# Using Node.js (npx)
npx serve

# Using PHP
php -S localhost:8000
```

## File Structure

```
estada/
├── index.html      # Main HTML file
├── styles.css      # All styles
├── script.js       # Interactive functionality
└── README.md       # This file
```

## Customization

### Colors
Edit CSS variables in `styles.css`:

```css
:root {
    --accent: #e07a5f;        /* Primary accent color */
    --bg-primary: #0a0a0b;    /* Main background */
    --text-primary: #f5f5f4;  /* Main text color */
}
```

### Content
All content is in `index.html` - update text, services, and contact info directly.

## License

© 2024 Estada. All rights reserved.

