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
- Flask (Python backend)
- Flask-Mail (Email functionality)

## Getting Started

### Running with Flask (Recommended)

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up Resend API:**
   - Sign up at [resend.com](https://resend.com) (free tier: 3,000 emails/month)
   - Get your API key from the dashboard
   - Create a `.env` file in the project root:
   ```env
   RESEND_API_KEY=re_xxxxxxxxxxxxx
   ```
   
   Or set it as an environment variable:
   ```bash
   export RESEND_API_KEY=re_xxxxxxxxxxxxx
   ```

**Note:** Emails will be sent FROM the user's email address (from the form) TO all three recipients.

3. **Run the Flask server:**
```bash
python app.py
```

The site will be available at `http://localhost:8082`

### Static File Server (Alternative)

Simply open `index.html` in your browser, or serve with any static file server:

```bash
# Using Python
python -m http.server 8000

# Using Node.js (npx)
npx serve

# Using PHP
php -S localhost:8000
```

**Note:** The contact form will only work when running with Flask.

## File Structure

```
estada/
├── app.py          # Flask backend server
├── index.html      # Main HTML file
├── styles.css      # All styles
├── script.js       # Interactive functionality
├── requirements.txt # Python dependencies
├── .env            # Email configuration (create this)
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

